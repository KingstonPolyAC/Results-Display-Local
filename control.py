import tkinter as tk
from tkinter import messagebox
import subprocess
import os
#import signal
import sys

server_process = None

# Get the installation directory from AppData
install_dir = os.path.join(os.environ['LOCALAPPDATA'], 'GLINTegrate-Results-Display')

# Construct paths to python.exe and app.py
python_exe_path = os.path.join(install_dir, 'venv', 'Scripts', 'python.exe')
app_py_path = os.path.join(install_dir, 'app.py')

def start_server():
    global server_process
    if server_process is None:
        # Check if the paths exist
        if not os.path.exists(python_exe_path):
            print(f"Error: Python executable not found at {python_exe_path}")
            sys.exit(1)

        if not os.path.exists(app_py_path):
            print(f"Error: app.py not found at {app_py_path}")
            sys.exit(1)
            
        #Start the server process
        try:
            server_process = subprocess.Popen([python_exe_path, app_py_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            messagebox.showinfo("Server", "Server started successfully!")
        except Exception as e:
            print(f"Error starting server: {e}")
            sys.exit(1)
    else:
        messagebox.showwarning("Server", "Server is already running.")

# def stop_server():
#     global server_process
#     if server_process is not None:
#         # Sending Ctrl+C to the main process group
#         os.kill(server_process.pid, signal.CTRL_C_EVENT)
#         server_process.wait()
#         server_process = None
#         messagebox.showinfo("Server", "Server stopped successfully!")
#     else:
#         messagebox.showwarning("Server", "Server is not running.")

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        #stop_server()
        messagebox.showinfo("Server", "Close the console window to terminate the program")
        root.destroy()
        sys.exit(1)

root = tk.Tk()
root.title("Server Control")
root.geometry("300x100")
start_button = tk.Button(root, text="Start Server", command=start_server)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Terminate Server", command=on_closing)
stop_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
#pyinstaller --name "Launch Results Display" --icon new_logo.ico --onefile control.py