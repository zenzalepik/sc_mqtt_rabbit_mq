import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(parent_dir, ".env")
print(f"[monitor] Loading .env from: {env_path}")
load_dotenv(env_path)

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_STATUS = "home/livingroom/light/status"
print(f"[monitor] Config -> BROKER={BROKER}, PORT={PORT}, STATUS={TOPIC_STATUS}")


class LightMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Status Monitor")
        self.root.geometry("300x200")

        self.client = None
        print("[monitor] App initialized")

        self.status_var = tk.StringVar(value="UNKNOWN")
        self.conn_var = tk.StringVar(value="Connecting...")

        self.status_label = ttk.Label(self.root, textvariable=self.status_var, font=("Arial", 24))
        self.status_label.pack(pady=20)

        self.conn_label = ttk.Label(self.root, textvariable=self.conn_var, font=("Arial", 9))
        self.conn_label.pack(pady=10)

        self.connect_mqtt()

    def update_status_visual(self, value):
        print(f"[monitor] update_status_visual -> {value}")
        self.status_var.set(value)
        if value == "ON":
            self.status_label.config(foreground="#00AA00")
        elif value == "OFF":
            self.status_label.config(foreground="#AA0000")
        else:
            self.status_label.config(foreground="#888888")

    def connect_mqtt(self):
        try:
            print("[monitor] Initializing MQTT client")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            print(f"[monitor] Connecting to {BROKER}:{PORT}...")
            self.client.connect(BROKER, PORT, 60)
            print("[monitor] Starting network loop")
            self.client.loop_start()
        except Exception as e:
            print(f"[monitor] connect_mqtt error: {e}")
            self.conn_var.set(f"Error: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[monitor] on_connect called, reason_code={reason_code}")
        if reason_code == 0:
            self.conn_var.set("Connected to MQTT")
            print(f"[monitor] Subscribing to {TOPIC_STATUS}")
            client.subscribe(TOPIC_STATUS)
        else:
            self.conn_var.set(f"Failed: {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"[monitor] on_disconnect called, reason_code={reason_code}")
        self.conn_var.set("Disconnected")

    def on_message(self, client, userdata, msg):
        value = msg.payload.decode().upper()
        print(f"[monitor] on_message from {msg.topic}: {value}")
        self.root.after(0, lambda: self.update_status_visual(value))


if __name__ == "__main__":
    root = tk.Tk()
    app = LightMonitorApp(root)
    root.mainloop()
