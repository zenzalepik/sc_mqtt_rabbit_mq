import paho.mqtt.client as mqtt
import time

# Konfigurasi Broker
BROKER = "localhost"
PORT = 1883
TOPIC = "tes/mqtt"

# Callback ketika berhasil terhubung
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Terhubung ke broker MQTT di {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"Subscribe ke topic: {TOPIC}")
    else:
        print(f"Gagal terhubung, return code {reason_code}")

# Callback ketika pesan diterima
def on_message(client, userdata, msg):
    print(f"Pesan diterima di topic '{msg.topic}': {msg.payload.decode()}")

def run_subscriber():
    # Inisialisasi client
    # Protocol version 5 direkomendasikan untuk paho-mqtt v2+
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    # Set callback
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Hubungkan ke broker
        client.connect(BROKER, PORT, 60)

        # Loop selamanya untuk memproses pesan
        print("Menunggu pesan... (Tekan Ctrl+C untuk berhenti)")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nSubscriber dihentikan.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    run_subscriber()
