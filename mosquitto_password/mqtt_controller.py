import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import psutil
import os
import sys
from dotenv import load_dotenv

# Force load .env from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)
print(f"Loaded .env from {env_path}")
print(f"MOSQUITTO_DIR: {os.getenv('MOSQUITTO_DIR')}")



class MosquittoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosquitto MQTT Broker Controller - Password")
        self.root.geometry("700x500")
        
        self.mosquitto_process = None
        self.default_port = 1883
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, 
                               text="Mosquitto MQTT Broker Controller (Password)", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        ttk.Label(main_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=str(self.default_port))
        self.port_entry = ttk.Entry(main_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.status_var = tk.StringVar(value="Status: Stopped")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                     font=("Arial", 10))
        self.status_label.grid(row=1, column=2, sticky=tk.E, padx=(20, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Mosquitto", 
                                      command=self.start_mosquitto, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="■ Stop Mosquitto", 
                                     command=self.stop_mosquitto, width=20,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.restart_button = ttk.Button(button_frame, text="↻ Restart", 
                                        command=self.restart_mosquitto, width=15,
                                        state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="Mosquitto Log:").grid(row=3, column=0, 
                                                         sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("info", foreground="blue")
        
        self.check_mosquitto_status()
        
    def check_mosquitto_status(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if 'mosquitto' in proc.info['name'].lower():
                self.status_var.set("Status: Already Running")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.restart_button.config(state=tk.NORMAL)
                self.log_message("Mosquitto already running from external process\n", "info")
                return
        self.log_message("Ready to start Mosquitto\n", "info")
    
    def log_message(self, message, tag="normal"):
        self.log_text.insert(tk.END, message, tag)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def find_mosquitto_path(self):
        possible_paths = []
        
        # Check environment variable first
        env_path = os.getenv("MOSQUITTO_DIR")
        if env_path:
            possible_paths.append(os.path.join(env_path, "mosquitto.exe"))

        possible_paths.extend([
            r"C:\Program Files\mosquitto\mosquitto.exe",
            r"C:\Program Files (x86)\mosquitto\mosquitto.exe",
            os.path.join(os.getcwd(), "mosquitto.exe"),
            r"C:\mosquitto\mosquitto.exe"
        ])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        try:
            result = subprocess.run(['where', 'mosquitto'], 
                                   capture_output=True, text=True, shell=True)
            if result.returncode == 0 and 'mosquitto.exe' in result.stdout:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        messagebox.showwarning("Mosquitto Not Found", 
                              "mosquitto.exe not found in default locations.\n"
                              "Please select mosquitto.exe when prompted.")
        
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select mosquitto.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        return path if path else None
    
    def kill_process_on_port(self, port):
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == int(port) and conn.status == 'LISTEN':
                    try:
                        proc = psutil.Process(conn.pid)
                        proc.terminate()
                        proc.wait(timeout=3)
                        self.log_message(f"Killed process {conn.pid} on port {port}\n", "info")
                    except:
                        pass
        except Exception as e:
            self.log_message(f"Error checking port {port}: {e}\n", "error")
    
    def start_mosquitto(self):
        try:
            port = self.port_var.get()
            if not port.isdigit():
                messagebox.showerror("Invalid Port", "Please enter a valid port number")
                return
            
            port = int(port)
            
            self.clear_log()
            
            self.kill_process_on_port(port)
            
            mosquitto_path = self.find_mosquitto_path()
            if not mosquitto_path:
                messagebox.showerror("Error", "mosquitto.exe not found!")
                return
            
            self.log_message(f"Starting Mosquitto on port {port} (password mode)...\n", "info")
            
            for proc in psutil.process_iter(['pid', 'name']):
                if 'mosquitto' in proc.info['name'].lower():
                    try:
                        proc.kill()
                        self.log_message(f"Stopped existing mosquitto (PID: {proc.info['pid']})\n", "info")
                    except:
                        pass
            
            # Check for config file in ps1 folder
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ps1', 'mosquitto_password.conf')
            if os.path.exists(config_path):
                self.log_message(f"Using config file: {config_path}\n", "info")
                cmd = [mosquitto_path, '-c', config_path, '-p', str(port), '-v']
            else:
                self.log_message("Config file not found, starting without password enforcement\n", "warning")
                cmd = [mosquitto_path, '-p', str(port), '-v']

            
            self.mosquitto_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.log_message(f"Mosquitto started (PID: {self.mosquitto_process.pid})\n", "success")
            self.status_var.set(f"Status: Running on port {port}")
            
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            
            self.read_output_thread = threading.Thread(
                target=self.read_process_output, 
                daemon=True
            )
            self.read_output_thread.start()
            
        except Exception as e:
            self.log_message(f"Error starting mosquitto: {e}\n", "error")
            messagebox.showerror("Error", f"Failed to start mosquitto:\n{str(e)}")
    
    def read_process_output(self):
        while self.mosquitto_process and self.mosquitto_process.poll() is None:
            try:
                output = self.mosquitto_process.stdout.readline()
                if output:
                    self.root.after(0, self.log_message, output)
            except:
                break
    
    def stop_mosquitto(self):
        if self.mosquitto_process:
            try:
                self.mosquitto_process.terminate()
                self.mosquitto_process.wait(timeout=5)
                self.log_message("Mosquitto stopped\n", "info")
            except:
                try:
                    self.mosquitto_process.kill()
                    self.log_message("Mosquitto force stopped\n", "info")
                except:
                    pass
            
            self.mosquitto_process = None
        
        for proc in psutil.process_iter(['pid', 'name']):
            if 'mosquitto' in proc.info['name'].lower():
                try:
                    proc.kill()
                except:
                    pass
        
        self.status_var.set("Status: Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
    
    def restart_mosquitto(self):
        self.log_message("Restarting Mosquitto...\n", "info")
        self.stop_mosquitto()
        self.root.after(1000, self.start_mosquitto)
    
    def on_closing(self):
        if self.mosquitto_process:
            self.stop_mosquitto()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MosquittoGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

