import os
import shutil
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
import webbrowser
import hashlib
import filetype
import schedule
import time
import concurrent.futures
import threading
import smtplib
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth

# Global variables for email notifications
sender_email = "isen97509@gmail.com"  # Replace with your actual email
receiver_email = "senishan526@gmail.com"  # Replace with the recipient's email
password = "juth btnx wsxp kpwd"  # Use generated App Password instead of your regular password

# Global variable for selected directory
selected_directory = None

# Initialize GUI
root = tk.Tk()
root.title("File Organizer")

def update_status(message):
    """Update the status label with a message and log the action."""
    status_label.config(text=message)
    root.update_idletasks()
    log_action(message)

def log_action(message):
    """Log all actions into a file for tracking."""
    with open("file_organizer_log.txt", "a") as log_file:
        log_file.write(f"{message}\n")

def preview_files(directory):
    """Show files before organizing."""
    file_listbox.delete(0, tk.END)
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    for file in files:
        file_listbox.insert(tk.END, file)

def detect_category(file_path):
    """Use AI-based file recognition to determine the correct category."""
    kind = filetype.guess(file_path)
    if kind:
        mime = kind.mime
        if "image" in mime:
            return "Images"
        elif "video" in mime:
            return "Videos"
        elif "pdf" in mime or "application/msword" in mime:
            return "Documents"
        elif "zip" in mime or "x-rar" in mime:
            return "Archives"
    return "Others"

def batch_process_files(directory):
    """Process files in parallel for efficiency."""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(organize_single_file, files)

def organize_single_file(file_path):
    """Organizes individual files efficiently."""
    category = detect_category(file_path)
    folder_path = os.path.join(os.path.dirname(file_path), category)
    os.makedirs(folder_path, exist_ok=True)
    shutil.move(file_path, os.path.join(folder_path, os.path.basename(file_path)))
    update_status(f"Moved {os.path.basename(file_path)} → {category}")

def organize_files(directory):
    """Organize files and remove duplicates before processing."""
    remove_duplicates(directory)
    batch_process_files(directory)
    
    send_email_notification()  # 🔹 Send an email alert after completion
    
    update_status("File organization complete!")

def get_file_hash(file_path):
    """Generate a hash for duplicate file detection."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def remove_duplicates(directory):
    """Scan and remove duplicate files across storage."""
    seen_hashes = {}
    duplicate_count = 0
    for root_dir, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root_dir, file)
            file_hash = get_file_hash(file_path)

            if file_hash in seen_hashes:
                os.remove(file_path)  # Remove duplicate
                duplicate_count += 1
            else:
                seen_hashes[file_hash] = file_path

    update_status(f"Removed {duplicate_count} duplicates across storage!")

def send_email_notification():
    """Sends an email notification when file organization is complete."""
    subject = "File Organization Completed"
    body = "Your files have been successfully organized and duplicates removed."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        update_status("Notification email sent!")
    except Exception as e:
        update_status(f"Error sending email: {e}")

def start_scheduler():
    """Runs scheduled tasks in the background."""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Schedule to run daily at 10 AM
schedule.every().day.at("10:00").do(lambda: organize_files("C:/Users/Ishaan/Desktop/AutoFolder"))

# Start the scheduler in a background thread
scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

def upload_to_drive(file_path):
    """Upload organized files to Google Drive."""
    creds, _ = google.auth.default()
    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": os.path.basename(file_path)}
    media = MediaFileUpload(file_path, resumable=True)
    service.files().create(body=file_metadata, media_body=media).execute()

def search_file():
    """Search for a file inside the folder."""
    global selected_directory
    query = search_entry.get()
    if selected_directory:
        files = [f for f in os.listdir(selected_directory) if query.lower() in f.lower()]
        if files:
            file_path = os.path.join(selected_directory, files[0])
            webbrowser.open(file_path)
        else:
            update_status("File not found!")
    else:
        update_status("Please select a folder first!")

def select_folder():
    """Select a folder and trigger organization."""
    global selected_directory
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        preview_files(selected_directory)

# Apply modern theme
style = ttk.Style()
style.theme_use("clam")

# GUI Elements
progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
progress.pack(pady=10)

status_label = ttk.Label(root, text="Select a folder to organize", style="TLabel")
status_label.pack(pady=10)

file_listbox = tk.Listbox(root, height=10, width=50)
file_listbox.pack()

search_entry = tk.Entry(root, width=30)
search_entry.pack()

search_button = ttk.Button(root, text="Search File", command=search_file, style="TButton")
search_button.pack()

select_button = ttk.Button(root, text="Select Folder to Organize", command=select_folder, style="TButton")
select_button.pack(pady=20)

# Start GUI
root.mainloop()