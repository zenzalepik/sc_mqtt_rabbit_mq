import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import psutil
import os
import sys
from dotenv import load_dotenv

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class RabbitMQControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Cluster Controller - HA Plan A")
        self.root.geometry("800x600")
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, 
                               text="RabbitMQ Cluster Controller (Plan A)", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Info Panel
        info_frame = ttk.LabelFrame(main_frame, text="Cluster Information", padding=10)
        info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(info_frame, text="Nodes: 3 (1 Master, 2 Slaves)").pack(anchor="w")
        ttk.Label(info_frame, text="Ports: 1883, 1884, 1885 (MQTT)").pack(anchor="w")
        ttk.Label(info_frame, text="Mode: Localhost Simulation").pack(anchor="w")
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Cluster", 
                                      command=self.start_cluster, width=20)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(button_frame, text="■ Stop Cluster", 
                                     command=self.stop_cluster, width=20)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        self.open_monitor_button = ttk.Button(button_frame, text="📊 Open Monitor", 
                                        command=self.open_monitor, width=20)
        self.open_monitor_button.pack(side=tk.LEFT, padx=10)
        
        # Log Area
        ttk.Label(main_frame, text="Controller Log:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=90)
        self.log_text.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("success", foreground="green")

    def log(self, message, tag="info"):
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)

    def run_script(self, script_name):
        script_path = os.path.join(current_dir, "ps1", script_name)
        if not os.path.exists(script_path):
            self.log(f"Script not found: {script_path}", "error")
            return

        self.log(f"Executing {script_name}...", "info")
        
        def _run():
            try:
                # Use PowerShell to run the script
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                for line in process.stdout:
                    self.root.after(0, self.log, line.strip(), "info")
                    
                process.wait()
                if process.returncode == 0:
                    self.root.after(0, self.log, "Execution completed successfully.", "success")
                else:
                    self.root.after(0, self.log, f"Execution failed with code {process.returncode}", "error")
            except Exception as e:
                self.root.after(0, self.log, f"Error running script: {e}", "error")

        threading.Thread(target=_run, daemon=True).start()

    def start_cluster(self):
        self.run_script("start_cluster.ps1")

    def stop_cluster(self):
        self.run_script("stop_cluster.ps1")
        
    def open_monitor(self):
        try:
            subprocess.Popen([sys.executable, "app.py"], cwd=current_dir)
        except Exception as e:
            self.log(f"Failed to open monitor: {e}", "error")

if __name__ == "__main__":
    root = tk.Tk()
    app = RabbitMQControllerGUI(root)
    root.mainloop()
