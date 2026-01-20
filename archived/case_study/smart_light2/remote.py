import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(parent_dir, ".env")
print(f"[remote] Loading .env from: {env_path}")
load_dotenv(env_path)

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SET = "home/livingroom/light/set"
print(f"[remote] Config -> BROKER={BROKER}, PORT={PORT}, SET={TOPIC_SET}")


class LightRemoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Remote Control")
        self.root.geometry("300x200")

        self.client = None

        self.conn_var = tk.StringVar(value="Connecting...")
        print("[remote] App initialized")

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=20)

        self.btn_on = ttk.Button(btn_frame, text="ON", command=lambda: self.send_command("ON"))
        self.btn_on.grid(row=0, column=0, padx=10)

        self.btn_off = ttk.Button(btn_frame, text="OFF", command=lambda: self.send_command("OFF"))
        self.btn_off.grid(row=0, column=1, padx=10)

        self.conn_label = ttk.Label(self.root, textvariable=self.conn_var, font=("Arial", 9))
        self.conn_label.pack(pady=10)

        self.connect_mqtt()

    def connect_mqtt(self):
        try:
            print("[remote] Initializing MQTT client")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            print(f"[remote] Connecting to {BROKER}:{PORT}...")
            self.client.connect(BROKER, PORT, 60)
            print("[remote] Starting network loop")
            self.client.loop_start()
        except Exception as e:
            print(f"[remote] connect_mqtt error: {e}")
            self.conn_var.set(f"Error: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[remote] on_connect called, reason_code={reason_code}")
        if reason_code == 0:
            self.conn_var.set("Connected to MQTT")
        else:
            self.conn_var.set(f"Failed: {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"[remote] on_disconnect called, reason_code={reason_code}")
        self.conn_var.set("Disconnected")

    def send_command(self, value):
        if not self.client:
            print("[remote] send_command called but client is None")
            return
        payload = value.upper()
        print(f"[remote] send_command -> publishing {payload} to {TOPIC_SET}")
        self.client.publish(TOPIC_SET, payload)


if __name__ == "__main__":
    root = tk.Tk()
    app = LightRemoteApp(root)
    root.mainloop()
