import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import time
import threading
import json

class MQTTClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Tester (Publisher & Subscriber)")
        self.root.geometry("800x600")
        
        # Variabel MQTT
        self.client = None
        self.is_connected = False
        
        self.create_widgets()

    def create_widgets(self):
        # Frame Koneksi
        conn_frame = ttk.LabelFrame(self.root, text="Koneksi Broker", padding="10")
        conn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, padx=5)
        self.broker_var = tk.StringVar(value="localhost")
        ttk.Entry(conn_frame, textvariable=self.broker_var).grid(row=0, column=1, padx=5)

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.port_var = tk.StringVar(value="1883")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=5)

        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=4, padx=10)

        self.lbl_status = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.lbl_status.grid(row=0, column=5, padx=10)

        # Frame Publisher
        pub_frame = ttk.LabelFrame(self.root, text="Publisher", padding="10")
        pub_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(pub_frame, text="Topic:").grid(row=0, column=0, padx=5)
        self.pub_topic_var = tk.StringVar(value="tes/mqtt")
        ttk.Entry(pub_frame, textvariable=self.pub_topic_var, width=30).grid(row=0, column=1, padx=5)

        ttk.Label(pub_frame, text="Pesan:").grid(row=1, column=0, padx=5, pady=5)
        self.msg_var = tk.StringVar(value="Halo dari GUI")
        ttk.Entry(pub_frame, textvariable=self.msg_var, width=50).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(pub_frame, text="Publish", command=self.publish_message).grid(row=1, column=2, padx=5)

        # Frame Subscriber
        sub_frame = ttk.LabelFrame(self.root, text="Subscriber", padding="10")
        sub_frame.pack(fill="both", expand=True, padx=10, pady=5)

        top_sub_frame = ttk.Frame(sub_frame)
        top_sub_frame.pack(fill="x", pady=5)
        
        ttk.Label(top_sub_frame, text="Subscribe Topic:").pack(side="left", padx=5)
        self.sub_topic_var = tk.StringVar(value="tes/#")
        ttk.Entry(top_sub_frame, textvariable=self.sub_topic_var, width=30).pack(side="left", padx=5)
        ttk.Button(top_sub_frame, text="Subscribe", command=self.subscribe_topic).pack(side="left", padx=5)
        ttk.Button(top_sub_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)

        self.log_area = scrolledtext.ScrolledText(sub_frame, height=15)
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def clear_log(self):
        self.log_area.delete('1.0', tk.END)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()

    def connect_mqtt(self):
        broker = self.broker_var.get()
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port harus berupa angka")
            return

        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            
            self.btn_connect.config(state="disabled") # Prevent double click
        except Exception as e:
            messagebox.showerror("Error", f"Gagal connect: {e}")

    def disconnect_mqtt(self):
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.is_connected = True
            self.update_status("Connected", "green")
            self.log(f"Terhubung ke {self.broker_var.get()}:{self.port_var.get()}")
            self.root.after(0, lambda: self.btn_connect.config(text="Disconnect", state="normal"))
            
            # Auto subscribe jika ada topic
            topic = self.sub_topic_var.get()
            if topic:
                self.subscribe_topic()
        else:
            self.update_status(f"Failed RC: {reason_code}", "red")
            self.root.after(0, lambda: self.btn_connect.config(state="normal"))

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.is_connected = False
        self.update_status("Disconnected", "red")
        self.log("Terputus dari broker")
        self.root.after(0, lambda: self.btn_connect.config(text="Connect", state="normal"))

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
        except:
            payload = str(msg.payload)
        
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{msg.topic}] {payload}"
        self.root.after(0, lambda: self.log(log_msg))

    def update_status(self, text, color):
        self.root.after(0, lambda: self.lbl_status.config(text=f"Status: {text}", foreground=color))

    def publish_message(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Belum terhubung ke broker!")
            return

        topic = self.pub_topic_var.get()
        msg = self.msg_var.get()
        
        if not topic:
            messagebox.showwarning("Warning", "Topic tidak boleh kosong")
            return

        info = self.client.publish(topic, msg)
        info.wait_for_publish()
        if info.rc == mqtt.MQTT_ERR_SUCCESS:
            self.log(f"[SENT] [{topic}] {msg}")
        else:
            self.log(f"[FAIL] Gagal mengirim ke {topic}")

    def subscribe_topic(self):
        if not self.is_connected:
            return # Silent fail or queue? Better just return, user needs to connect first
            
        topic = self.sub_topic_var.get()
        if topic:
            self.client.subscribe(topic)
            self.log(f"Subscribed ke {topic}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTClientGUI(root)
    root.mainloop()
