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

print("[monitor_cluster] Loading .env")
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

class RabbitMQClusterMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Cluster Monitor - HA Plan A")
        self.root.geometry("800x700")
        
        # Configuration from Plan A
        self.nodes = [
            {"name": "Node 1 (Master)", "mqtt_port": 1883, "amqp_port": 5672, "mgmt_port": 15672, "host": "localhost"},
            {"name": "Node 2 (Slave)",  "mqtt_port": 1884, "amqp_port": 5673, "mgmt_port": 15673, "host": "localhost"},
            {"name": "Node 3 (Slave)",  "mqtt_port": 1885, "amqp_port": 5674, "mgmt_port": 15674, "host": "localhost"}
        ]
        
        self.setup_gui()
        
        self.running = True
        self.update_status()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        header_font = font.Font(family="Helvetica", size=12, weight="bold")
        status_font = font.Font(family="Helvetica", size=10)
        
        # Title
        tk.Label(self.root, text="RabbitMQ Cluster Monitor (HA Mode)", font=title_font).pack(pady=15)
        
        # Cluster Status Frame
        self.cluster_frame = tk.LabelFrame(self.root, text="Cluster Node Status", font=header_font, padx=10, pady=10)
        self.cluster_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Headers
        headers = ["Node Name", "MQTT Port", "AMQP Port", "Mgmt Port", "Status", "PID"]
        for i, h in enumerate(headers):
            tk.Label(self.cluster_frame, text=h, font=("Helvetica", 10, "bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Node Rows
        self.node_labels = []
        for i, node in enumerate(self.nodes):
            row_labels = {}
            
            # Name
            tk.Label(self.cluster_frame, text=node["name"], font=status_font).grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            # MQTT Port
            row_labels["mqtt"] = tk.Label(self.cluster_frame, text=f"{node['mqtt_port']}", font=status_font)
            row_labels["mqtt"].grid(row=i+1, column=1, padx=10, pady=5)
            
            # AMQP Port
            row_labels["amqp"] = tk.Label(self.cluster_frame, text=f"{node['amqp_port']}", font=status_font)
            row_labels["amqp"].grid(row=i+1, column=2, padx=10, pady=5)
            
            # Mgmt Port
            row_labels["mgmt"] = tk.Label(self.cluster_frame, text=f"{node['mgmt_port']}", font=status_font)
            row_labels["mgmt"].grid(row=i+1, column=3, padx=10, pady=5)
            
            # Status
            row_labels["status"] = tk.Label(self.cluster_frame, text="Checking...", font=status_font, fg="gray")
            row_labels["status"].grid(row=i+1, column=4, padx=10, pady=5)
            
            # PID
            row_labels["pid"] = tk.Label(self.cluster_frame, text="--", font=status_font)
            row_labels["pid"].grid(row=i+1, column=5, padx=10, pady=5)
            
            self.node_labels.append(row_labels)
            
        # Summary Section
        summary_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        summary_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.time_label = tk.Label(summary_frame, text="Last check: --:--:--", font=status_font)
        self.time_label.pack(pady=5)
        
        self.overall_status = tk.Label(summary_frame, text="Cluster Health: CHECKING", font=("Helvetica", 14, "bold"))
        self.overall_status.pack(pady=10)
        
        # Controls
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Refresh Now", command=self.update_status, bg="lightblue").pack(side=tk.LEFT, padx=5)
        
        # Status Bar
        self.status_bar = tk.Label(self.root, text="Monitoring started...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def check_port(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def get_pid_by_port(self, port):
        try:
            for conn in psutil.net_connections(kind='inet'):
                if hasattr(conn.laddr, 'port') and conn.laddr.port == port and conn.status == 'LISTEN':
                    return conn.pid
        except:
            pass
        return None

    def update_status(self):
        if not self.running:
            return
            
        active_nodes = 0
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"Last check: {current_time}")
        
        for i, node in enumerate(self.nodes):
            labels = self.node_labels[i]
            
            # Check MQTT Port
            mqtt_active = self.check_port(node["host"], node["mqtt_port"])
            pid = self.get_pid_by_port(node["mqtt_port"])
            
            # Update UI
            if mqtt_active:
                active_nodes += 1
                labels["status"].config(text="ONLINE", fg="green", font=("Helvetica", 10, "bold"))
                labels["mqtt"].config(fg="green")
                labels["pid"].config(text=str(pid) if pid else "Unknown")
            else:
                labels["status"].config(text="OFFLINE", fg="red")
                labels["mqtt"].config(fg="red")
                labels["pid"].config(text="--")
                
            # Check other ports just for color
            if self.check_port(node["host"], node["amqp_port"]):
                labels["amqp"].config(fg="green")
            else:
                labels["amqp"].config(fg="red")
                
            if self.check_port(node["host"], node["mgmt_port"]):
                labels["mgmt"].config(fg="green")
            else:
                labels["mgmt"].config(fg="red")

        # Overall Status
        if active_nodes == len(self.nodes):
            self.overall_status.config(text=f"Cluster Health: HEALTHY ({active_nodes}/{len(self.nodes)} Nodes)", fg="green")
        elif active_nodes > 0:
             self.overall_status.config(text=f"Cluster Health: DEGRADED ({active_nodes}/{len(self.nodes)} Nodes)", fg="orange")
        else:
             self.overall_status.config(text="Cluster Health: DOWN", fg="red")
             
        self.status_bar.config(text=f"Updated: {current_time} | Active Nodes: {active_nodes}")
        
        self.root.after(3000, self.update_status)

    def on_closing(self):
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = RabbitMQClusterMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
