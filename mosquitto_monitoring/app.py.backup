import tkinter as tk
from tkinter import ttk, font
import subprocess
import threading
import time
from datetime import datetime
import sys

class MosquittoMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosquitto Monitor - Real-time")
        self.root.geometry("500x400")
        
        # Port yang dimonitor
        self.monitor_port = 52345
        
        # Setup GUI
        self.setup_gui()
        
        # Start monitoring
        self.running = True
        self.update_status()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        # Custom font
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        status_font = font.Font(family="Helvetica", size=12)
        
        # Title
        title_label = tk.Label(self.root, text="Mosquitto MQTT Monitor", font=title_font)
        title_label.pack(pady=10)
        
        # Port info
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=5)
        tk.Label(port_frame, text="Monitoring Port:", font=status_font).pack(side=tk.LEFT)
        self.port_label = tk.Label(port_frame, text=str(self.monitor_port), 
                                  font=status_font, fg="blue")
        self.port_label.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        status_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Last update time
        self.time_label = tk.Label(status_frame, text="Last check: --:--:--", font=status_font)
        self.time_label.pack(pady=5)
        
        # Process status
        process_frame = tk.Frame(status_frame)
        process_frame.pack(pady=10, fill=tk.X)
        tk.Label(process_frame, text="Process Status:", font=status_font, 
                width=15, anchor="w").pack(side=tk.LEFT)
        self.process_status = tk.Label(process_frame, text="CHECKING...", 
                                      font=status_font, width=20)
        self.process_status.pack(side=tk.LEFT)
        
        # Process PID
        pid_frame = tk.Frame(status_frame)
        pid_frame.pack(pady=5, fill=tk.X)
        tk.Label(pid_frame, text="Process ID:", font=status_font, 
                width=15, anchor="w").pack(side=tk.LEFT)
        self.pid_label = tk.Label(pid_frame, text="--", font=status_font)
        self.pid_label.pack(side=tk.LEFT)
        
        # Port status
        port_status_frame = tk.Frame(status_frame)
        port_status_frame.pack(pady=10, fill=tk.X)
        tk.Label(port_status_frame, text="Port Status:", font=status_font, 
                width=15, anchor="w").pack(side=tk.LEFT)
        self.port_status = tk.Label(port_status_frame, text="CHECKING...", 
                                   font=status_font, width=20)
        self.port_status.pack(side=tk.LEFT)
        
        # Connection test
        conn_frame = tk.Frame(status_frame)
        conn_frame.pack(pady=10, fill=tk.X)
        tk.Label(conn_frame, text="MQTT Connection:", font=status_font, 
                width=15, anchor="w").pack(side=tk.LEFT)
        self.conn_status = tk.Label(conn_frame, text="CHECKING...", 
                                   font=status_font, width=20)
        self.conn_status.pack(side=tk.LEFT)
        
        # Summary status
        self.summary_label = tk.Label(status_frame, text="", font=title_font, pady=20)
        self.summary_label.pack()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Monitoring started", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_mosquitto_process(self):
        """Check if mosquitto process is running"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq mosquitto.exe"],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
                if "mosquitto.exe" in result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if "mosquitto.exe" in line:
                            parts = line.split()
                            pid = parts[1]
                            return True, pid
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "mosquitto"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    pid = result.stdout.strip()
                    return True, pid
            return False, None
        except Exception as e:
            return False, None
    
    def check_port(self):
        """Check if port is listening"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
                if str(self.monitor_port) in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if f":{self.monitor_port}" in line and "LISTENING" in line:
                            return True
            else:
                result = subprocess.run(
                    ["netstat", "-tln"],
                    capture_output=True, text=True
                )
                if f":{self.monitor_port}" in result.stdout:
                    return True
            return False
        except:
            return False
    
    def test_mqtt_connection(self):
        """Test MQTT connection by publishing a test message"""
        try:
            test_cmd = [
                "mosquitto_pub",
                "-h", "localhost",
                "-p", str(self.monitor_port),
                "-t", "monitor/test",
                "-m", "test",
                "-q", "1"
            ]
            
            result = subprocess.run(
                test_cmd,
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                timeout=3
            )
            
            return result.returncode == 0
        except:
            return False
    
    def update_status(self):
        """Update all status indicators"""
        if not self.running:
            return
            
        # Update time
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"Last check: {current_time}")
        
        # Check process
        process_running, pid = self.check_mosquitto_process()
        
        if process_running:
            self.process_status.config(text="RUNNING", fg="green")
            self.pid_label.config(text=pid, fg="blue")
        else:
            self.process_status.config(text="STOPPED", fg="red")
            self.pid_label.config(text="--", fg="gray")
        
        # Check port
        port_listening = self.check_port()
        if port_listening:
            self.port_status.config(text="LISTENING", fg="green")
        else:
            self.port_status.config(text="NOT LISTENING", fg="red")
        
        # Test connection only if process is running
        if process_running and port_listening:
            connection_ok = self.test_mqtt_connection()
            if connection_ok:
                self.conn_status.config(text="CONNECTED", fg="green")
            else:
                self.conn_status.config(text="NO CONNECTION", fg="orange")
        else:
            self.conn_status.config(text="NOT TESTED", fg="gray")
        
        # Update summary
        if process_running and port_listening:
            self.summary_label.config(text="✅ MOSQUITTO ACTIVE", fg="green")
            self.status_bar.config(text=f"Mosquitto running on port {self.monitor_port}, PID: {pid}")
        else:
            self.summary_label.config(text="❌ MOSQUITTO INACTIVE", fg="red")
            self.status_bar.config(text=f"Mosquitto not running on port {self.monitor_port}")
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MosquittoMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()