import tkinter as tk
from tkinter import filedialog
import threading
import json
import os

JSON_FILE_PATH = 'meeting_info.json'

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files",".xlsm .xlsx")])
    if file_path:
        print(f"Selected file: {file_path}")
        append_to_json(file_path)

def append_to_json(file_path):
    data = {}
    # Load existing data from the JSON file
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    
    # Append the new file path to the existing data
    data['workbook_path'] = file_path

    # Save the updated data back to the JSON file
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

def run_tkinter():
    select_file()

if __name__ == "__main__":
    thread = threading.Thread(target=run_tkinter)
    thread.start()
    thread.join()
