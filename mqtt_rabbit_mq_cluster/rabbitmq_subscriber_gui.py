import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import time
import os
import threading
from dotenv import load_dotenv

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class RabbitMQSubscriberHA:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Subscriber (HA - Smart Client)")
        self.root.geometry("700x550")
        
        # HA Configuration
        self.brokers = [
            {"host": "localhost", "port": 1883},
            {"host": "localhost", "port": 1884},
            {"host": "localhost", "port": 1885}
        ]
        self.current_broker_index = 0
        self.client = None
        self.is_connected = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Connection Status
        status_frame = ttk.LabelFrame(self.root, text="Cluster Connection Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Disconnected")
        self.conn_info_var = tk.StringVar(value="Ready to connect")
        
        ttk.Label(status_frame, textvariable=self.conn_info_var).pack(side=tk.LEFT, padx=5)
        self.lbl_status = ttk.Label(status_frame, textvariable=self.status_var, foreground="red", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=5)
        
        self.btn_connect = ttk.Button(status_frame, text="Connect HA", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.RIGHT, padx=10)

        # Subscriber Settings
        sub_frame = ttk.LabelFrame(self.root, text="Subscriber Settings", padding="10")
        sub_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(sub_frame, text="Topic:").pack(side=tk.LEFT, padx=5)
        self.sub_topic_var = tk.StringVar(value="ha/cluster/#")
        ttk.Entry(sub_frame, textvariable=self.sub_topic_var, width=30).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sub_frame, text="Update Subscription", command=self.subscribe).pack(side=tk.LEFT, padx=5)
        ttk.Button(sub_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        # Log
        log_frame = ttk.LabelFrame(self.root, text="Received Messages", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_area.pack(fill="both", expand=True)

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def clear_log(self):
        self.log_area.delete('1.0', tk.END)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_ha()
        else:
            self.disconnect()

    def connect_ha(self):
        self.log("Starting HA Connection Sequence...")
        threading.Thread(target=self._connect_loop, daemon=True).start()

    def _connect_loop(self):
        for i in range(len(self.brokers)):
            idx = (self.current_broker_index + i) % len(self.brokers)
            broker = self.brokers[idx]
            
            self.root.after(0, self.log, f"Attempting connection to Node {idx+1} ({broker['port']})...")
            
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                client.on_connect = self.on_connect
                client.on_message = self.on_message
                client.on_disconnect = self.on_disconnect
                
                client.connect(broker['host'], broker['port'], 5)
                client.loop_start()
                
                time.sleep(1)
                
                if client.is_connected():
                    self.client = client
                    self.current_broker_index = idx
                    self.root.after(0, self.log, f"Connected to Node {idx+1}")
                    return
                else:
                    client.loop_stop()
            except Exception as e:
                self.root.after(0, self.log, f"Node {idx+1} unreachable: {e}")

        self.root.after(0, self.log, "All nodes unreachable. Retrying in 5s...")
        time.sleep(5)
        self._connect_loop()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            self.root.after(0, lambda: self.status_var.set(f"Connected to Node {self.current_broker_index+1}"))
            self.root.after(0, lambda: self.conn_info_var.set(f"Port: {self.brokers[self.current_broker_index]['port']}"))
            self.root.after(0, lambda: self.lbl_status.config(foreground="green"))
            self.root.after(0, lambda: self.btn_connect.config(text="Disconnect"))
            self.subscribe()

    def subscribe(self):
        if self.client and self.is_connected:
            topic = self.sub_topic_var.get()
            self.client.subscribe(topic)
            self.log(f"Subscribed to {topic}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
        except:
            payload = str(msg.payload)
        
        self.root.after(0, self.log, f"[{msg.topic}] {payload}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        self.root.after(0, lambda: self.status_var.set("Lost Connection - Failover..."))
        self.root.after(0, lambda: self.lbl_status.config(foreground="orange"))
        
        if self.client:
            self.client.loop_stop()
            self.client = None
            
        # Try next node
        self.current_broker_index = (self.current_broker_index + 1) % len(self.brokers)
        self.connect_ha()

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            self.client = None
        self.is_connected = False
        self.status_var.set("Disconnected")
        self.lbl_status.config(foreground="red")
        self.btn_connect.config(text="Connect HA")

if __name__ == "__main__":
    root = tk.Tk()
    app = RabbitMQSubscriberHA(root)
    root.mainloop()
