import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paho.mqtt.client as mqtt
import time
import os
from dotenv import load_dotenv

print("[pub_gui_pw] Loading .env")
# Force load .env from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)


class MQTTPublisherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Publisher GUI - Password")
        self.root.geometry("600x450")
        
        self.client = None
        self.is_connected = False
        self.offline_queue = []
        print("[pub_gui_pw] App initialized")
        self.create_widgets()

    def create_widgets(self):
        conn_frame = ttk.LabelFrame(self.root, text="Koneksi Broker", padding="10")
        conn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, padx=5)
        self.broker_var = tk.StringVar(value=os.getenv("MQTT_BROKER", "localhost"))
        ttk.Entry(conn_frame, textvariable=self.broker_var).grid(row=0, column=1, padx=5)

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.port_var = tk.StringVar(value=os.getenv("MQTT_PORT", "1883"))
        ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=5)

        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=4, padx=10)

        self.lbl_status = ttk.Label(conn_frame, text="Status: Disconnected", foreground="red")
        self.lbl_status.grid(row=0, column=5, padx=10)

        pub_frame = ttk.LabelFrame(self.root, text="Publisher", padding="10")
        pub_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(pub_frame, text="Topic:").grid(row=0, column=0, padx=5, sticky="w")
        self.pub_topic_var = tk.StringVar(value=os.getenv("MQTT_TOPIC_PUB", "tes/mqtt"))
        ttk.Entry(pub_frame, textvariable=self.pub_topic_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(pub_frame, text="Pesan:").grid(row=1, column=0, padx=5, sticky="nw")
        self.msg_text = tk.Text(pub_frame, height=5, width=40)
        self.msg_text.grid(row=1, column=1, padx=5, pady=5)
        self.msg_text.insert("1.0", "Halo dari Publisher GUI (Password)")

        self.keep_send_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pub_frame,
            text="Keep send message when disconnected",
            variable=self.keep_send_var
        ).grid(row=2, column=0, padx=5, pady=5, sticky="w")

        ttk.Button(pub_frame, text="Publish", command=self.publish_message).grid(row=2, column=1, padx=5, pady=5, sticky="e")

        log_frame = ttk.LabelFrame(self.root, text="Log Aktivitas", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_area.pack(fill="both", expand=True)

    def log(self, message):
        print(f"[pub_gui_pw] {message}")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_mqtt()
        else:
            self.disconnect_mqtt()

    def connect_mqtt(self):
        broker = self.broker_var.get()
        print(f"[pub_gui_pw] toggle_connection -> is_connected={self.is_connected}, broker={broker}, port={self.port_var.get()}")
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port harus berupa angka")
            return

        try:
            print("[pub_gui_pw] Initializing MQTT client")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            username = os.getenv("MQTT_USERNAME")
            password = os.getenv("MQTT_PASSWORD")
            if username:
                self.client.username_pw_set(username, password)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            
            print(f"[pub_gui_pw] Connecting to {broker}:{port}...")
            self.client.connect(broker, port, 60)
            print("[pub_gui_pw] Starting network loop")
            self.client.loop_start()
            
            self.btn_connect.config(state="disabled")
        except Exception as e:
            print(f"[pub_gui_pw] connect_mqtt error: {e}")
            messagebox.showerror("Error", f"Gagal connect: {e}")

    def disconnect_mqtt(self):
        if self.client:
            print("[pub_gui_pw] disconnect_mqtt called")
            self.client.disconnect()
            self.client.loop_stop()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[pub_gui_pw] on_connect called, reason_code={reason_code}")
        if reason_code == 0:
            self.is_connected = True
            self.update_status("Connected", "green")
            self.log(f"Terhubung ke {self.broker_var.get()}:{self.port_var.get()}")
            if self.offline_queue:
                self.log("Mengirim pesan yang tersimpan saat offline")
                queue_copy = list(self.offline_queue)
                self.offline_queue.clear()
                for topic, msg in queue_copy:
                    try:
                        info = self.client.publish(topic, msg, retain=True)
                        info.wait_for_publish()
                        if info.rc == mqtt.MQTT_ERR_SUCCESS:
                            self.log(f"[SENT-OFFLINE] [{topic}] {msg}")
                        else:
                            self.log(f"[FAIL-OFFLINE] Gagal mengirim ke {topic}")
                    except Exception as e:
                        self.log(f"[FAIL-OFFLINE] Exception saat kirim ke {topic}: {e}")
            self.root.after(0, lambda: self.btn_connect.config(text="Disconnect", state="normal"))
        else:
            self.update_status(f"Failed RC: {reason_code}", "red")
            self.root.after(0, lambda: self.btn_connect.config(state="normal"))

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"[pub_gui_pw] on_disconnect called, reason_code={reason_code}")
        self.is_connected = False
        self.update_status("Disconnected", "red")
        self.log("Terputus dari broker")
        self.root.after(0, lambda: self.btn_connect.config(text="Connect", state="normal"))

    def update_status(self, text, color):
        self.root.after(0, lambda: self.lbl_status.config(text=f"Status: {text}", foreground=color))

    def publish_message(self):
        if not self.is_connected and not self.keep_send_var.get():
            messagebox.showwarning("Warning", "Belum terhubung ke broker!")
            return

        topic = self.pub_topic_var.get()
        msg = self.msg_text.get("1.0", tk.END).strip()
        
        if not topic:
            messagebox.showwarning("Warning", "Topic tidak boleh kosong")
            return

        if self.client is None:
            if self.keep_send_var.get():
                self.offline_queue.append((topic, msg))
                self.log(f"[QUEUED-OFFLINE] [{topic}] {msg}")
            else:
                messagebox.showwarning("Warning", "Client MQTT belum diinisialisasi")
            return

        try:
            info = self.client.publish(topic, msg, retain=True)
            info.wait_for_publish()
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                self.log(f"[SENT] [{topic}] {msg}")
            else:
                self.log(f"[FAIL] Gagal mengirim ke {topic}")
                if self.keep_send_var.get():
                    self.offline_queue.append((topic, msg))
                    self.log(f"[QUEUED-OFFLINE] [{topic}] {msg}")
        except Exception as e:
            self.log(f"[FAIL] Exception saat publish ke {topic}: {e}")
            if self.keep_send_var.get():
                self.offline_queue.append((topic, msg))
                self.log(f"[QUEUED-OFFLINE] [{topic}] {msg}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MQTTPublisherGUI(root)
    root.mainloop()

