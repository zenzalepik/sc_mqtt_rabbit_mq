import tkinter as tk
from tkinter import ttk, font, messagebox
import subprocess
import threading
import time
from datetime import datetime
import sys
import psutil
import socket
import os
from dotenv import load_dotenv

print("[monitor_pw] Loading .env")
# Force load .env from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)


class MosquittoMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosquitto Monitor - Real-time (Password)")
        self.root.geometry("700x650")
        
        self.monitor_port = 52345
        self.default_mqtt_port = 1883
        self.other_services = []
        
        # Variabel untuk auto-kill
        self.auto_kill_enabled = tk.BooleanVar(value=False)
        self.kill_thread = None
        self.kill_running = False
        
        self.setup_gui()
        
        self.running = True
        self.update_status()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        status_font = font.Font(family="Helvetica", size=10)
        warning_font = font.Font(family="Helvetica", size=11, weight="bold")
        
        title_label = tk.Label(self.root, text="Mosquitto MQTT Monitor (Password)", font=title_font)
        title_label.pack(pady=10)
        
        # Frame untuk auto-kill checkbox
        auto_kill_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2, bg="#f0f0f0")
        auto_kill_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        self.auto_kill_checkbox = tk.Checkbutton(
            auto_kill_frame,
            text=" Auto Kill Mosquitto 1883 & Anonymous Mosquitto",
            variable=self.auto_kill_enabled,
            font=("Helvetica", 10, "bold"),
            fg="darkred",
            bg="#f0f0f0",
            command=self.toggle_auto_kill
        )
        self.auto_kill_checkbox.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.auto_kill_status = tk.Label(
            auto_kill_frame,
            text="[OFF]",
            font=("Helvetica", 9),
            fg="red",
            bg="#f0f0f0"
        )
        self.auto_kill_status.pack(side=tk.LEFT, padx=5)
        
        # Info label untuk auto-kill
        auto_kill_info = tk.Label(
            auto_kill_frame,
            text="(Akan otomatis kill service yang tidak aman setiap detik)",
            font=("Helvetica", 8),
            fg="gray",
            bg="#f0f0f0"
        )
        auto_kill_info.pack(side=tk.RIGHT, padx=10)
        
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=5)
        tk.Label(port_frame, text="Monitoring Port:", font=status_font).pack(side=tk.LEFT)
        self.port_label = tk.Label(port_frame, text=str(self.monitor_port), 
                                  font=status_font, fg="blue")
        self.port_label.pack(side=tk.LEFT, padx=5)
        
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        self.left_frame = tk.Frame(top_frame, relief=tk.RIDGE, borderwidth=2)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        default_title_frame = tk.Frame(self.left_frame)
        default_title_frame.pack(fill=tk.X, pady=(2, 5))
        
        tk.Label(default_title_frame, text="Default MQTT Port Monitor", 
                font=("Helvetica", 11, "bold"), fg="darkred").pack(side=tk.LEFT)
        
        default_status_frame = tk.Frame(self.left_frame)
        default_status_frame.pack(fill=tk.X, pady=2)
        
        self.default_status_label = tk.Label(default_status_frame, text="Checking...", 
                                           font=status_font)
        self.default_status_label.pack(side=tk.LEFT, padx=5)
        
        self.default_detail_label = tk.Label(default_status_frame, text="", 
                                           font=status_font, fg="gray")
        self.default_detail_label.pack(side=tk.LEFT, padx=20)
        
        self.default_action_button = tk.Button(default_status_frame, text="Kill Process", 
                                             command=self.kill_default_port, 
                                             state=tk.DISABLED, bg="orange", fg="white",
                                             font=("Helvetica", 9))
        self.default_action_button.pack(side=tk.RIGHT, padx=5)
        
        self.right_frame = tk.Frame(top_frame, relief=tk.RIDGE, borderwidth=2)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        other_title_frame = tk.Frame(self.right_frame)
        other_title_frame.pack(fill=tk.X, pady=(2, 5))
        
        tk.Label(other_title_frame, text="Other MQTT Services", 
                font=("Helvetica", 11, "bold"), fg="purple").pack(side=tk.LEFT)
        
        other_status_frame = tk.Frame(self.right_frame)
        other_status_frame.pack(fill=tk.X, pady=2)
        
        self.other_status_label = tk.Label(other_status_frame, text="Scanning...", 
                                         font=status_font, fg="gray")
        self.other_status_label.pack(side=tk.LEFT, padx=5)
        
        other_buttons_frame = tk.Frame(other_status_frame)
        other_buttons_frame.pack(side=tk.RIGHT)
        
        self.other_killall_button = tk.Button(other_buttons_frame, text="Kill All", 
                                            command=self.kill_all_anonymous_services,
                                            state=tk.DISABLED, bg="darkred", fg="white",
                                            font=("Helvetica", 8))
        self.other_killall_button.pack(side=tk.LEFT, padx=2)
        
        self.other_detail_button = tk.Button(other_buttons_frame, text="Detail", 
                                           command=self.show_other_services_detail,
                                           state=tk.DISABLED, bg="lightgray", fg="black",
                                           font=("Helvetica", 8))
        self.other_detail_button.pack(side=tk.LEFT, padx=2)
        
        self.other_refresh_button = tk.Button(other_buttons_frame, text="Scan", 
                                            command=self.scan_other_mqtt_services,
                                            font=("Helvetica", 8), bg="lightblue")
        self.other_refresh_button.pack(side=tk.LEFT, padx=2)
        
        status_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        status_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.time_label = tk.Label(status_frame, text="Last check: --:--:--", font=status_font)
        self.time_label.pack(pady=5)
        
        ttk.Separator(status_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        monitor_frame = tk.Frame(status_frame)
        monitor_frame.pack(pady=5, fill=tk.X)
        tk.Label(monitor_frame, text=f"Your Port {self.monitor_port}:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.monitor_status = tk.Label(monitor_frame, text="CHECKING...", 
                                      font=status_font, width=15)
        self.monitor_status.pack(side=tk.LEFT)
        
        process_frame = tk.Frame(status_frame)
        process_frame.pack(pady=5, fill=tk.X)
        tk.Label(process_frame, text="Mosquitto Process:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.process_status = tk.Label(process_frame, text="CHECKING...", 
                                      font=status_font, width=15)
        self.process_status.pack(side=tk.LEFT)
        
        pid_frame = tk.Frame(status_frame)
        pid_frame.pack(pady=5, fill=tk.X)
        tk.Label(pid_frame, text="Process ID:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.pid_label = tk.Label(pid_frame, text="--", font=status_font)
        self.pid_label.pack(side=tk.LEFT)
        
        conn_frame = tk.Frame(status_frame)
        conn_frame.pack(pady=5, fill=tk.X)
        tk.Label(conn_frame, text="MQTT Connection:", font=status_font, 
                width=20, anchor="w").pack(side=tk.LEFT)
        self.conn_status = tk.Label(conn_frame, text="CHECKING...", 
                                   font=status_font, width=15)
        self.conn_status.pack(side=tk.LEFT)
        
        ttk.Separator(status_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.summary_label = tk.Label(status_frame, text="", font=title_font, pady=10)
        self.summary_label.pack()
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Refresh Now", command=self.force_refresh,
                 bg="lightblue").pack(side=tk.LEFT, padx=5)
        
        self.status_bar = tk.Label(self.root, text="Monitoring started...", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_port_status(self, port):
        try:
            for conn in psutil.net_connections(kind='inet'):
                if hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                    if conn.status == 'LISTEN':
                        try:
                            proc = psutil.Process(conn.pid)
                            return True, conn.pid, proc.name()
                        except:
                            return True, conn.pid, "Unknown"
            return False, None, None
        except Exception as e:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    return True, None, "Unknown"
            except:
                pass
            return False, None, None
    
    def check_mosquitto_process(self):
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'mosquitto' in proc.info['name'].lower():
                        return True, proc.info['pid'], proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False, None, None
        except Exception as e:
            return False, None, None
    
    def test_mqtt_connection(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                try:
                    # Check env path first
                    mosquitto_dir = os.getenv("MOSQUITTO_DIR")
                    pub_cmd = "mosquitto_pub"
                    if mosquitto_dir:
                        potential_path = os.path.join(mosquitto_dir, "mosquitto_pub.exe")
                        if os.path.exists(potential_path):
                            pub_cmd = potential_path

                    test_cmd = [
                        pub_cmd,
                        "-h", "localhost",
                        "-p", str(port),
                        "-t", "monitor/test",
                        "-m", "test",
                        "-q", "0",
                        "-i", "monitor_client_pw",
                        "-W", "1"
                    ]
                    username = os.getenv("MQTT_USERNAME")
                    password = os.getenv("MQTT_PASSWORD")
                    if username:
                        test_cmd.extend(["-u", username, "-P", password or ""])
                    
                    result = subprocess.run(
                        test_cmd,
                        capture_output=True, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                        timeout=2
                    )
                    
                    return result.returncode == 0
                except (subprocess.SubprocessError, FileNotFoundError):
                    return True
            return False
        except:
            return False
    
    def find_other_mqtt_services(self):
        other_services = []
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                if hasattr(conn.laddr, 'port') and conn.status == 'LISTEN':
                    port = conn.laddr.port
                    
                    if port in [self.default_mqtt_port, self.monitor_port]:
                        continue
                    
                    if port > 1024 and port < 65535:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name().lower()
                            
                            mqtt_keywords = ['mosquitto', 'mqtt', 'emqx', 'hivemq', 'vernemq', 'rabbitmq']
                            is_mqtt_like = any(keyword in proc_name for keyword in mqtt_keywords)
                            
                            if is_mqtt_like:
                                other_services.append({
                                    'port': port,
                                    'pid': conn.pid,
                                    'name': proc.name(),
                                    'anonymous': True
                                })
                        except:
                            if self.test_mqtt_connection(port):
                                other_services.append({
                                    'port': port,
                                    'pid': None,
                                    'name': 'Unknown',
                                    'anonymous': True
                                })
        except Exception as e:
            print(f"Error finding other MQTT services: {e}")
        
        return other_services
    
    def update_other_services_display(self):
        self.other_services = self.find_other_mqtt_services()
        
        if self.other_services:
            self.other_status_label.config(
                text=f"⚠ Service MQTT Anonymous terdeteksi ({len(self.other_services)} service)",
                fg="red",
                font=("Helvetica", 10, "bold")
            )
            
            self.other_killall_button.config(state=tk.NORMAL, bg="darkred", fg="white")
            self.other_detail_button.config(state=tk.NORMAL, bg="#ff9966", fg="white")
            
            self.right_frame.config(bg="#ffcc99")
            
            service_ports = [str(s['port']) for s in self.other_services]
            self.status_bar.config(
                text=f"{self.status_bar.cget('text')} | Anonymous MQTT pada port: {', '.join(service_ports)}"
            )
        else:
            self.other_status_label.config(
                text="✓ Tidak ada service MQTT lain",
                fg="darkgreen",
                font=("Helvetica", 10)
            )
            
            self.other_killall_button.config(state=tk.DISABLED, bg="lightgray", fg="black")
            self.other_detail_button.config(state=tk.DISABLED, bg="lightgray", fg="black")
            
            self.right_frame.config(bg="#ccffcc")
    
    def show_other_services_detail(self):
        if not self.other_services:
            return
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detail Service MQTT Anonymous")
        detail_window.geometry("400x300")
        detail_window.resizable(False, False)
        
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        title_label = tk.Label(detail_window, 
                             text="Service MQTT Anonymous Terdeteksi",
                             font=("Helvetica", 12, "bold"),
                             fg="red")
        title_label.pack(pady=10)
        
        list_frame = tk.Frame(detail_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        from tkinter import scrolledtext
        detail_text = scrolledtext.ScrolledText(list_frame, width=50, height=15)
        detail_text.pack(fill=tk.BOTH, expand=True)
        
        detail_text.insert(tk.END, "="*50 + "\n")
        detail_text.insert(tk.END, "DETAIL SERVICE MQTT ANONYMOUS\n")
        detail_text.insert(tk.END, "="*50 + "\n\n")
        
        for i, service in enumerate(self.other_services, 1):
            detail_text.insert(tk.END, f"[Service #{i}]\n")
            detail_text.insert(tk.END, f"Port: {service['port']}\n")
            
            if service['pid']:
                detail_text.insert(tk.END, f"PID: {service['pid']}\n")
            else:
                detail_text.insert(tk.END, f"PID: Tidak diketahui\n")
            
            detail_text.insert(tk.END, f"Nama Process: {service['name']}\n")
            detail_text.insert(tk.END, f"Status: Anonymous MQTT Service\n")
            detail_text.insert(tk.END, "-"*30 + "\n\n")
        
        detail_text.insert(tk.END, f"\nTotal: {len(self.other_services)} service anonymous\n")
        
        detail_text.config(state=tk.DISABLED)
        
        close_button = tk.Button(detail_window, text="Tutup", 
                               command=detail_window.destroy,
                               bg="lightgray", font=("Helvetica", 10))
        close_button.pack(pady=10)
        
        detail_window.update_idletasks()
        width = detail_window.winfo_width()
        height = detail_window.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry(f'{width}x{height}+{x}+{y}')
    
    def kill_all_anonymous_services(self):
        if not self.other_services:
            return
        
        service_count = len(self.other_services)
        service_ports = [str(s['port']) for s in self.other_services]
        
        confirm_msg = f"Kill semua {service_count} service MQTT anonymous?\n\n"
        confirm_msg += f"Port yang akan di-kill: {', '.join(service_ports)}\n\n"
        confirm_msg += "Tindakan ini tidak dapat dibatalkan!"
        
        if not messagebox.askyesno("Konfirmasi Kill All", confirm_msg):
            return
        
        killed_count = 0
        failed_count = 0
        
        for service in self.other_services:
            try:
                if service['pid']:
                    try:
                        process = psutil.Process(service['pid'])
                        process.terminate()
                        
                        try:
                            process.wait(timeout=1)
                        except:
                            pass
                        
                        killed_count += 1
                        
                    except Exception as e:
                        try:
                            process = psutil.Process(service['pid'])
                            process.kill()
                            killed_count += 1
                        except:
                            failed_count += 1
            except:
                failed_count += 1
        
        result_msg = f"Berhasil kill {killed_count} service\n"
        if failed_count > 0:
            result_msg += f"Gagal kill {failed_count} service\n"
        
        messagebox.showinfo("Hasil Kill All", result_msg)
        
        self.status_bar.config(text=f"Killed {killed_count} anonymous MQTT services")
        self.update_other_services_display()
    
    def update_default_port_display(self, default_active, default_pid, default_name):
        if default_active:
            self.left_frame.config(bg="#ffcccc", relief=tk.RIDGE, borderwidth=3)
            
            self.default_status_label.config(
                text="⚠ WARNING: Default Port 1883 is ACTIVE!",
                fg="red",
                font=("Helvetica", 10, "bold")
            )
            
            detail_text = f"PID: {default_pid if default_pid else 'Unknown'}"
            if default_name and default_name != "Unknown":
                detail_text += f" | Process: {default_name}"
            self.default_detail_label.config(text=detail_text, fg="darkred")
            
            self.default_action_button.config(state=tk.NORMAL, bg="red", fg="white")
            
        else:
            self.left_frame.config(bg="#ccffcc", relief=tk.RIDGE, borderwidth=2)
            
            self.default_status_label.config(
                text="✓ Default Port 1883 is inactive",
                fg="darkgreen",
                font=("Helvetica", 10)
            )
            
            self.default_detail_label.config(text="No service detected", fg="gray")
            
            self.default_action_button.config(state=tk.DISABLED, bg="lightgray", fg="black")
    
    def update_status(self):
        if not self.running:
            return
            
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=f"Last check: {current_time}")
            
            default_active, default_pid, default_name = self.check_port_status(self.default_mqtt_port)
            
            self.update_default_port_display(default_active, default_pid, default_name)
            
            self.update_other_services_display()
            
            monitor_active, monitor_pid, monitor_name = self.check_port_status(self.monitor_port)
            
            if monitor_active:
                self.monitor_status.config(text="ACTIVE", fg="green")
                monitor_conn = self.test_mqtt_connection(self.monitor_port)
                if monitor_conn:
                    self.conn_status.config(text=f"CONNECTED", fg="green")
                else:
                    self.conn_status.config(text=f"PORT OPEN", fg="orange")
            else:
                self.monitor_status.config(text="INACTIVE", fg="red")
                self.conn_status.config(text="DISCONNECTED", fg="red")
            
            process_running, process_pid, process_name = self.check_mosquitto_process()
            
            if process_running:
                self.process_status.config(text="RUNNING", fg="green")
                self.pid_label.config(text=process_pid, fg="blue")
            else:
                self.process_status.config(text="STOPPED", fg="red")
                self.pid_label.config(text="--", fg="gray")
            
            if monitor_active:
                self.summary_label.config(text=f"✅ PORT {self.monitor_port} ACTIVE", fg="green")
                self.status_bar.config(
                    text=f"Port {self.monitor_port} active | "
                         f"Default port 1883: {'ACTIVE' if default_active else 'inactive'} | "
                         f"Other MQTT: {len(self.other_services)} service(s) | "
                         f"Updated: {current_time}"
                )
            else:
                self.summary_label.config(text=f"❌ PORT {self.monitor_port} INACTIVE", fg="red")
                self.status_bar.config(
                    text=f"Port {self.monitor_port} not active | "
                         f"Default port 1883: {'ACTIVE' if default_active else 'inactive'} | "
                         f"Other MQTT: {len(self.other_services)} service(s) | "
                         f"Updated: {current_time}"
                )
                
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)[:50]}...")
        
        self.root.after(2000, self.update_status)
    
    def scan_other_mqtt_services(self):
        self.status_bar.config(text="Scanning for other MQTT services...")
        self.update_other_services_display()
        self.status_bar.config(text="Scan completed" + self.status_bar.cget('text').split('Scan completed')[-1])
    
    def force_refresh(self):
        self.status_bar.config(text="Manual refresh triggered...")
        self.update_status()
    
    def toggle_auto_kill(self):
        if self.auto_kill_enabled.get():
            # Enable Auto Kill
            if messagebox.askyesno("Confirm Auto Kill", 
                                 "Warning: This will AUTOMATICALLY KILL any process on port 1883\n"
                                 "and any other anonymous MQTT services every second.\n\n"
                                 "Are you sure you want to enable this?"):
                self.kill_running = True
                self.auto_kill_status.config(text="[ON]", fg="green")
                self.auto_kill_checkbox.config(fg="green")
                
                # Start thread
                if self.kill_thread is None or not self.kill_thread.is_alive():
                    self.kill_thread = threading.Thread(target=self.auto_kill_loop, daemon=True)
                    self.kill_thread.start()
                    
                self.status_bar.config(text="Auto Kill STARTED - Monitoring every 1 second")
            else:
                self.auto_kill_enabled.set(False)
        else:
            # Disable Auto Kill
            if messagebox.askyesno("Confirm Stop", "Stop Auto Kill monitoring?"):
                self.kill_running = False
                self.auto_kill_status.config(text="[OFF]", fg="red")
                self.auto_kill_checkbox.config(fg="darkred")
                self.status_bar.config(text="Auto Kill STOPPED")
            else:
                self.auto_kill_enabled.set(True)

    def auto_kill_loop(self):
        while self.kill_running and self.running:
            try:
                # 1. Kill Default Port 1883
                active, pid, name = self.check_port_status(self.default_mqtt_port)
                if active and pid:
                    self.silent_kill_pid(pid, f"Port {self.default_mqtt_port}")
                
                # 2. Kill Anonymous Services
                # Re-scan to be sure
                other_services = self.find_other_mqtt_services()
                for service in other_services:
                    if service['pid']:
                        self.silent_kill_pid(service['pid'], f"Anonymous Port {service['port']}")
                
                # Update UI via main thread is tricky if not using after()
                # But Tkinter is somewhat thread-safe for simple config, or we can rely on main update loop
                # to reflect changes.
                
            except Exception as e:
                print(f"Auto kill error: {e}")
            
            time.sleep(1)
            
    def silent_kill_pid(self, pid, description):
        try:
            process = psutil.Process(pid)
            process.terminate()
            try:
                process.wait(timeout=1)
            except:
                process.kill()
            print(f"[Auto Kill] Terminated {description} (PID: {pid})")
        except Exception as e:
            print(f"[Auto Kill] Failed to kill {description} (PID: {pid}): {e}")

    def stop_auto_kill_thread(self):
        self.kill_running = False
        if self.kill_thread and self.kill_thread.is_alive():
            self.kill_thread.join(timeout=1.0)

    def kill_default_port(self):
        try:
            default_active, default_pid, default_name = self.check_port_status(self.default_mqtt_port)
            
            if default_active and default_pid:
                try:
                    process = psutil.Process(default_pid)
                    
                    if not messagebox.askyesno("Confirm Kill", 
                                             f"Kill process on port 1883?\n\n"
                                             f"PID: {default_pid}\n"
                                             f"Process: {default_name if default_name else 'Unknown'}\n\n"
                                             f"This may stop important services."):
                        return
                    
                    process.terminate()
                    
                    try:
                        process.wait(timeout=3)
                        self.status_bar.config(text=f"Process on port 1883 (PID: {default_pid}) terminated.")
                        
                        self.update_default_port_display(False, None, None)
                        
                    except:
                        process.kill()
                        self.status_bar.config(text=f"Process on port 1883 (PID: {default_pid}) force killed.")
                        
                        self.update_default_port_display(False, None, None)
                    
                except Exception as e:
                    self.status_bar.config(text=f"Failed to kill process: {str(e)[:50]}")
            elif default_active:
                self.status_bar.config(text="Port 1883 active but cannot identify process.")
            else:
                self.status_bar.config(text="Port 1883 is already inactive.")
                
        except Exception as e:
            self.status_bar.config(text=f"Error checking port: {str(e)[:50]}")
    
    def on_closing(self):
        self.stop_auto_kill_thread()
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MosquittoMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

