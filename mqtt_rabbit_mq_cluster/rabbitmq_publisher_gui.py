import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import time
import os
import sqlite3
import json
import threading
from dotenv import load_dotenv

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class RabbitMQPublisherHA:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Publisher (HA - Smart Client)")
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
        self.db_path = os.path.join(current_dir, "message_buffer.db")
        
        self.init_db()
        self.create_widgets()
        
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS offline_messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, payload TEXT, timestamp REAL)''')
        conn.commit()
        conn.close()

    def create_widgets(self):
        # Connection Status
        status_frame = ttk.LabelFrame(self.root, text="Cluster Connection Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Disconnected")
        self.broker_info_var = tk.StringVar(value="Target: Node 1, Node 2, Node 3")
        
        ttk.Label(status_frame, textvariable=self.broker_info_var).pack(side=tk.LEFT, padx=5)
        self.lbl_status = ttk.Label(status_frame, textvariable=self.status_var, foreground="red", font=("Arial", 10, "bold"))
        self.lbl_status.pack(side=tk.RIGHT, padx=5)
        
        self.btn_connect = ttk.Button(status_frame, text="Connect HA", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.RIGHT, padx=10)

        # Publisher
        pub_frame = ttk.LabelFrame(self.root, text="Publisher", padding="10")
        pub_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(pub_frame, text="Topic:").grid(row=0, column=0, padx=5, sticky="w")
        self.pub_topic_var = tk.StringVar(value="ha/cluster/test")
        ttk.Entry(pub_frame, textvariable=self.pub_topic_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(pub_frame, text="Message:").grid(row=1, column=0, padx=5, sticky="nw")
        self.msg_text = tk.Text(pub_frame, height=5, width=50)
        self.msg_text.grid(row=1, column=1, padx=5, pady=5)
        self.msg_text.insert("1.0", "Hello RabbitMQ Cluster!")

        ttk.Button(pub_frame, text="Publish (HA)", command=self.publish_message).grid(row=2, column=1, padx=5, pady=5, sticky="e")

        # Log
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_area.pack(fill="both", expand=True)

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_ha()
        else:
            self.disconnect()

    def connect_ha(self):
        self.log("Starting HA Connection Sequence...")
        threading.Thread(target=self._connect_loop, daemon=True).start()

    def _connect_loop(self):
        # Try each broker
        for i in range(len(self.brokers)):
            idx = (self.current_broker_index + i) % len(self.brokers)
            broker = self.brokers[idx]
            
            self.root.after(0, self.log, f"Trying Node {idx+1} ({broker['host']}:{broker['port']})...")
            
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
                client.on_connect = self.on_connect
                client.on_disconnect = self.on_disconnect
                
                # Optional: Set username/password if needed
                # client.username_pw_set("user", "pass")
                
                client.connect(broker['host'], broker['port'], 5)
                client.loop_start()
                
                # Wait a bit to see if we connect
                time.sleep(1)
                
                if client.is_connected():
                    self.client = client
                    self.current_broker_index = idx
                    self.root.after(0, self.log, f"Successfully connected to Node {idx+1}")
                    return
                else:
                    client.loop_stop()
                    
            except Exception as e:
                self.root.after(0, self.log, f"Failed to connect to Node {idx+1}: {e}")
        
        self.root.after(0, self.log, "All nodes unreachable! System is offline.")
        self.root.after(0, lambda: self.status_var.set("ALL NODES DOWN"))
        self.root.after(0, lambda: self.lbl_status.config(foreground="red"))

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            self.root.after(0, lambda: self.status_var.set(f"Connected to Node {self.current_broker_index+1}"))
            self.root.after(0, lambda: self.lbl_status.config(foreground="green"))
            self.root.after(0, lambda: self.btn_connect.config(text="Disconnect"))
            
            # Flush buffer
            threading.Thread(target=self.flush_buffer, daemon=True).start()

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        self.root.after(0, lambda: self.status_var.set("Disconnected - Reconnecting..."))
        self.root.after(0, lambda: self.lbl_status.config(foreground="orange"))
        self.log("Disconnected. Triggering Failover...")
        
        # Auto reconnect (Failover)
        if self.client:
            self.client.loop_stop()
            self.client = None
            
        # Move to next broker
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

    def publish_message(self):
        topic = self.pub_topic_var.get()
        payload = self.msg_text.get("1.0", tk.END).strip()
        
        if not topic:
            messagebox.showwarning("Error", "Topic required")
            return

        if self.is_connected and self.client:
            try:
                info = self.client.publish(topic, payload, qos=1)
                info.wait_for_publish()
                self.log(f"[SENT] {payload}")
            except Exception as e:
                self.log(f"[ERROR] Publish failed: {e}")
                self.save_to_buffer(topic, payload)
        else:
            self.log("[OFFLINE] Saving to local buffer (SQLite)")
            self.save_to_buffer(topic, payload)

    def save_to_buffer(self, topic, payload):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO offline_messages (topic, payload, timestamp) VALUES (?, ?, ?)",
                      (topic, payload, time.time()))
            conn.commit()
            conn.close()
            self.log(f"[BUFFERED] Message saved to DB")
        except Exception as e:
            self.log(f"[CRITICAL] DB Error: {e}")

    def flush_buffer(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT id, topic, payload FROM offline_messages ORDER BY id ASC")
            rows = c.fetchall()
            
            if rows:
                self.root.after(0, self.log, f"Flushing {len(rows)} buffered messages...")
                
                for row in rows:
                    msg_id, topic, payload = row
                    if self.client and self.is_connected:
                        self.client.publish(topic, payload, qos=1)
                        c.execute("DELETE FROM offline_messages WHERE id=?", (msg_id,))
                        self.root.after(0, self.log, f"[RE-SENT] {payload}")
                        time.sleep(0.1)
                    else:
                        break
                
                conn.commit()
            conn.close()
        except Exception as e:
            self.root.after(0, self.log, f"Flush Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RabbitMQPublisherHA(root)
    root.mainloop()
