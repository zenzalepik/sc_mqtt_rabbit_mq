import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import threading
from datetime import datetime
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Coba import paho-mqtt, jika tidak ada beri instruksi
try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False
    print("Paho MQTT library tidak ditemukan. Untuk subscribe yang lebih baik, install dengan:")
    print("pip install paho-mqtt")

class MosquittoConnectionTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosquitto Connection Tester v4.0")
        self.root.geometry("700x700")
        
        # Default settings
        self.host = "localhost"
        self.port = 52345
        self.topic = "test/topic"
        self.message = "Hello from MQTT Tester"
        
        # MQTT Client untuk subscribe
        self.mqtt_client = None
        self.is_subscribing = False
        self.is_connected = False
        self.subscribed_topics = []
        
        # Threading untuk subscribe
        self.subscribe_thread = None
        self.stop_subscribe_flag = False
        
        # Tentukan path ke mosquitto tools
        self.mosquitto_path = self.find_mosquitto_path()
        
        self.setup_gui()
        
        # Tampilkan info path di log
        if self.mosquitto_path:
            self.log_message(f"✓ Mosquitto tools found at: {self.mosquitto_path}", "green")
        else:
            self.log_message("⚠ Mosquitto tools not found. Please specify path.", "orange")
        
        # Info tentang Paho MQTT
        if not PAHO_AVAILABLE:
            self.log_message("⚠ Paho MQTT library not installed. Subscribe may not work properly.", "orange")
            self.log_message("   Install with: pip install paho-mqtt", "gray")
        else:
            self.log_message("✓ Paho MQTT library available for better subscribe functionality", "green")
    
    def find_mosquitto_path(self):
        """Cari path mosquitto tools secara otomatis"""
        possible_paths = []
        
        # Check environment variable first
        env_path = os.getenv("MOSQUITTO_DIR")
        if env_path:
            possible_paths.append(env_path)

        possible_paths.extend([
            r"C:\Program Files\mosquitto",
            r"C:\mosquitto",
            os.path.join(os.path.dirname(__file__), "mosquitto"),
            os.path.join(os.getcwd(), "mosquitto"),
            r"C:\Program Files (x86)\mosquitto",
        ])
        
        path_dirs = os.environ.get('PATH', '').split(';')
        possible_paths.extend(path_dirs)
        
        for path in possible_paths:
            if path:
                pub_path = os.path.join(path, "mosquitto_pub.exe")
                if os.path.exists(pub_path):
                    return path
                
        return None
    
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Mosquitto MQTT Connection Tester v4.0", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Status: Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Path settings frame
        path_frame = ttk.LabelFrame(main_frame, text="Mosquitto Path", padding="10")
        path_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="Path to mosquitto tools:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        if self.mosquitto_path:
            self.path_entry.insert(0, self.mosquitto_path)
        else:
            self.path_entry.insert(0, r"C:\Program Files\mosquitto")
        
        ttk.Button(path_frame, text="Browse", command=self.browse_path, width=10).grid(row=0, column=2)
        
        # Connection settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Connection Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Host
        ttk.Label(settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.host_entry = ttk.Entry(settings_frame, width=30)
        self.host_entry.grid(row=0, column=1, sticky=tk.W)
        self.host_entry.insert(0, self.host)
        
        # Port
        ttk.Label(settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=10)
        self.port_entry = ttk.Entry(settings_frame, width=10)
        self.port_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        self.port_entry.insert(0, str(self.port))
        
        # Topic
        ttk.Label(settings_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.topic_entry = ttk.Entry(settings_frame, width=30)
        self.topic_entry.grid(row=2, column=1, sticky=tk.W)
        self.topic_entry.insert(0, self.topic)
        
        # Message
        ttk.Label(settings_frame, text="Message:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=10)
        self.message_entry = tk.Text(settings_frame, width=30, height=3)
        self.message_entry.grid(row=3, column=1, sticky=tk.W, pady=10)
        self.message_entry.insert("1.0", self.message)
        
        # Test buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Row 1: Publish and basic subscribe
        self.test_pub_btn = ttk.Button(button_frame, text="Test Publish", 
                                      command=self.test_publish, width=15)
        self.test_pub_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.test_sub_btn = ttk.Button(button_frame, text="Basic Subscribe", 
                                      command=self.test_subscribe_basic, width=15)
        self.test_sub_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Row 2: Advanced subscribe (Paho MQTT)
        self.start_sub_btn = ttk.Button(button_frame, text="Start Subscribe (Paho)", 
                                       command=self.start_paho_subscribe, width=15)
        self.start_sub_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.stop_sub_btn = ttk.Button(button_frame, text="Stop Subscribe", 
                                      command=self.stop_paho_subscribe, width=15, state=tk.DISABLED)
        self.stop_sub_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Row 3: Other buttons
        self.test_both_btn = ttk.Button(button_frame, text="Test Both", 
                                       command=self.test_both, width=15)
        self.test_both_btn.grid(row=2, column=0, padx=5, pady=5)
        
        self.clear_btn = ttk.Button(button_frame, text="Clear Log", 
                                   command=self.clear_log, width=15)
        self.clear_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Results frame dengan ScrolledText
        results_frame = ttk.LabelFrame(main_frame, text="Test Results - Live Log", padding="10")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Create scrolled text widget for logs (lebih baik dari Text biasa)
        self.log_text = scrolledtext.ScrolledText(results_frame, width=80, height=15, state=tk.NORMAL)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        path_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def log_message(self, message, color="black"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Enable text widget untuk menulis
        self.log_text.config(state=tk.NORMAL)
        
        # Insert dengan warna
        if color != "black":
            # Buat tag untuk warna
            tag_name = f"color_{color}"
            self.log_text.insert(tk.END, log_entry, tag_name)
            self.log_text.tag_config(tag_name, foreground=color)
        else:
            self.log_text.insert(tk.END, log_entry)
        
        self.log_text.see(tk.END)
        
        # Keep text widget readable (non-editable oleh user)
        self.log_text.config(state=tk.DISABLED)
        
        # Update status bar
        self.update_status(f"Last: {message[:50]}...")
    
    def update_status(self, message):
        self.status_bar.config(text=f"Status: {message}")
    
    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Log cleared", "blue")
        self.update_status("Ready")
    
    def get_settings(self):
        try:
            host = self.host_entry.get().strip() or "localhost"
            port = int(self.port_entry.get().strip() or "52345")
            topic = self.topic_entry.get().strip() or "test/topic"
            message = self.message_entry.get("1.0", tk.END).strip() or "Test message"
            
            return host, port, topic, message
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return None
    
    def browse_path(self):
        folder = filedialog.askdirectory(title="Select Mosquitto installation folder")
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.mosquitto_path = folder
            self.log_message(f"Mosquitto path set to: {folder}", "blue")
    
    def get_mosquitto_tool(self, tool_name):
        path = self.path_entry.get().strip()
        if not path:
            path = self.mosquitto_path or os.getenv("MOSQUITTO_DIR") or r"C:\Program Files\mosquitto"
        
        possible_names = [
            f"{tool_name}.exe",
            tool_name,
            f"{tool_name}.bat",
        ]
        
        for name in possible_names:
            full_path = os.path.join(path, name)
            if os.path.exists(full_path):
                return full_path
        
        return tool_name
    
    def test_publish(self):
        settings = self.get_settings()
        if not settings:
            return
        
        host, port, topic, message = settings
        
        def publish_thread():
            self.test_pub_btn.config(state=tk.DISABLED)
            self.update_status("Publishing...")
            self.log_message(f"📤 Publishing to {host}:{port}", "blue")
            self.log_message(f"Topic: {topic}", "gray")
            
            try:
                mosquitto_pub = self.get_mosquitto_tool("mosquitto_pub")
                
                # Tambahkan timestamp
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                full_message = f"[{timestamp}] {message}"
                
                cmd = [
                    mosquitto_pub,
                    "-h", host,
                    "-p", str(port),
                    "-t", topic,
                    "-m", full_message,
                    "-q", "1",
                    "-d"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                
                if result.returncode == 0:
                    self.log_message("✅ PUBLISH SUCCESSFUL", "green")
                    self.log_message(f"Message: {full_message}", "gray")
                    
                    # Parse MQTT protocol messages
                    for line in result.stdout.split('\n'):
                        if "PUBACK" in line or "PUBLISH" in line:
                            self.log_message(f"  {line.strip()}", "darkgreen")
                else:
                    self.log_message("❌ PUBLISH FAILED", "red")
                    if result.stderr:
                        self.log_message(f"Error: {result.stderr.strip()}", "red")
                
            except subprocess.TimeoutExpired:
                self.log_message("⏰ PUBLISH TIMEOUT", "orange")
            except Exception as e:
                self.log_message(f"❌ Error: {str(e)}", "red")
            finally:
                self.test_pub_btn.config(state=tk.NORMAL)
                self.update_status("Ready")
        
        threading.Thread(target=publish_thread, daemon=True).start()
    
    def test_subscribe_basic(self):
        """Basic subscribe menggunakan mosquitto_sub.exe (masih ada timing issues)"""
        settings = self.get_settings()
        if not settings:
            return
        
        host, port, topic, _ = settings
        
        def subscribe_thread():
            self.test_sub_btn.config(state=tk.DISABLED)
            self.update_status("Subscribing (10s timeout)...")
            self.log_message(f"🎧 Basic subscribe to: {topic}", "blue")
            self.log_message(f"Host: {host}:{port}", "gray")
            self.log_message("Listening for 10 seconds...", "gray")
            
            try:
                mosquitto_sub = self.get_mosquitto_tool("mosquitto_sub")
                
                cmd = [
                    mosquitto_sub,
                    "-h", host,
                    "-p", str(port),
                    "-t", topic,
                    "-q", "1",
                    "-v",  # Verbose mode
                    "-W", "10"  # Timeout 10 detik
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=12,
                    shell=True
                )
                
                if result.returncode == 0:
                    if result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        self.log_message(f"✅ Received {len(lines)} message(s):", "green")
                        for i, line in enumerate(lines):
                            self.log_message(f"  {i+1}. {line}", "darkgreen")
                    else:
                        self.log_message("✅ No messages received (timeout)", "green")
                else:
                    self.log_message("❌ SUBSCRIBE FAILED", "red")
                    if result.stderr:
                        self.log_message(f"Error: {result.stderr.strip()}", "red")
                
            except subprocess.TimeoutExpired:
                self.log_message("✅ Subscribe completed (timeout)", "green")
            except Exception as e:
                self.log_message(f"❌ Error: {str(e)}", "red")
            finally:
                self.test_sub_btn.config(state=tk.NORMAL)
                self.update_status("Ready")
        
        threading.Thread(target=subscribe_thread, daemon=True).start()
    
    def start_paho_subscribe(self):
        """Start subscribe menggunakan Paho MQTT (lebih reliable)"""
        if not PAHO_AVAILABLE:
            messagebox.showerror("Library Required", 
                                "Paho MQTT library not installed.\n\n"
                                "Install with: pip install paho-mqtt\n"
                                "Then restart the application.")
            return
        
        if self.is_subscribing:
            self.log_message("⚠ Already subscribing", "orange")
            return
        
        settings = self.get_settings()
        if not settings:
            return
        
        host, port, topic, _ = settings
        
        def mqtt_thread():
            self.is_subscribing = True
            self.stop_subscribe_flag = False
            
            # Setup MQTT client
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            try:
                # Update GUI
                self.root.after(0, lambda: self.start_sub_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.stop_sub_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.log_message(f"🔌 Connecting to {host}:{port}...", "blue"))
                self.root.after(0, lambda: self.update_status("Connecting to broker..."))
                
                # Connect
                self.mqtt_client.connect(host, port, 60)
                
                # Start network loop
                self.mqtt_client.loop_start()
                
                # Keep thread alive
                while self.is_subscribing and not self.stop_subscribe_flag:
                    time.sleep(0.1)
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"❌ Connection failed: {str(e)}", "red"))
                self.is_subscribing = False
                self.root.after(0, lambda: self.start_sub_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.stop_sub_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.update_status("Connection failed"))
            
        # Start thread
        self.subscribe_thread = threading.Thread(target=mqtt_thread, daemon=True)
        self.subscribe_thread.start()
    
    def stop_paho_subscribe(self):
        """Stop Paho MQTT subscribe"""
        if self.is_subscribing and self.mqtt_client:
            self.is_subscribing = False
            self.stop_subscribe_flag = True
            
            # Disconnect
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
            
            # Update GUI
            self.start_sub_btn.config(state=tk.NORMAL)
            self.stop_sub_btn.config(state=tk.DISABLED)
            self.log_message("⏹️ Subscribe stopped", "blue")
            self.update_status("Subscribe stopped")
    
    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            self.root.after(0, lambda: self.log_message(f"✅ Connected to broker", "green"))
            self.root.after(0, lambda: self.update_status("Connected"))
            
            # Subscribe to topic
            settings = self.get_settings()
            if settings:
                _, _, topic, _ = settings
                client.subscribe(topic)
                self.root.after(0, lambda: self.log_message(f"📡 Subscribed to: {topic}", "blue"))
                self.subscribed_topics.append(topic)
        else:
            self.root.after(0, lambda: self.log_message(f"❌ Connection failed: {reason_code}", "red"))
            self.root.after(0, lambda: self.update_status(f"Connection failed: {reason_code}"))
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming messages"""
        try:
            payload = msg.payload.decode('utf-8')
        except:
            payload = str(msg.payload)
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        message = f"📩 [{timestamp}] [{msg.topic}] {payload}"
        
        # Update GUI dari main thread
        self.root.after(0, lambda: self.log_message(message, "darkgreen"))
    
    def on_mqtt_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        self.root.after(0, lambda: self.log_message("🔌 Disconnected from broker", "orange"))
        self.root.after(0, lambda: self.update_status("Disconnected"))
        self.root.after(0, lambda: self.start_sub_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_sub_btn.config(state=tk.DISABLED))
    
    def test_both(self):
        """Test publish dan subscribe bersama-sama"""
        settings = self.get_settings()
        if not settings:
            return
        
        host, port, topic, message = settings
        
        def both_test_thread():
            self.test_both_btn.config(state=tk.DISABLED)
            self.update_status("Running both test...")
            self.log_message("🔄 Running PUBLISH + SUBSCRIBE test", "purple")
            
            # Step 1: Start Paho subscribe jika tersedia
            if PAHO_AVAILABLE and not self.is_subscribing:
                self.log_message("[STEP 1] Starting Paho subscribe...", "blue")
                # Jalankan di thread terpisah
                threading.Thread(target=self.start_paho_subscribe, daemon=True).start()
                time.sleep(2)  # Tunggu koneksi
            
            # Step 2: Publish beberapa test messages
            self.log_message("[STEP 2] Publishing test messages...", "blue")
            
            for i in range(3):
                if not self.is_connected and i > 0:
                    break
                
                test_msg = f"Test message {i+1}: {message}"
                self.publish_message_direct(host, port, topic, test_msg)
                time.sleep(1)
            
            # Step 3: Tunggu dan selesaikan
            time.sleep(2)
            
            if self.is_connected:
                self.log_message("✅ Both test completed successfully", "green")
                self.log_message("   Messages published and should be received by subscriber", "gray")
            else:
                self.log_message("⚠️ Test completed but no active subscription", "orange")
            
            self.test_both_btn.config(state=tk.NORMAL)
            self.update_status("Test completed")
        
        threading.Thread(target=both_test_thread, daemon=True).start()
    
    def publish_message_direct(self, host, port, topic, message):
        """Publish message langsung (untuk internal use)"""
        try:
            mosquitto_pub = self.get_mosquitto_tool("mosquitto_pub")
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            full_message = f"[{timestamp}] {message}"
            
            cmd = [
                mosquitto_pub,
                "-h", host,
                "-p", str(port),
                "-t", topic,
                "-m", full_message,
                "-q", "1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
            
            if result.returncode == 0:
                self.log_message(f"📤 Published: {full_message[:50]}...", "gray")
                return True
            else:
                self.log_message(f"❌ Publish failed: {result.stderr[:100]}", "red")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Publish error: {str(e)}", "red")
            return False

def main():
    root = tk.Tk()
    app = MosquittoConnectionTester(root)
    root.mainloop()

if __name__ == "__main__":
    main()