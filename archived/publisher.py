import paho.mqtt.client as mqtt
import time
import json

# Konfigurasi Broker
BROKER = "localhost"
PORT = 1883
TOPIC = "tes/mqtt"

def run_publisher():
    # Inisialisasi client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        # Hubungkan ke broker
        client.connect(BROKER, PORT, 60)
        client.loop_start() # Mulai loop di background thread

        print(f"Terhubung ke broker {BROKER}:{PORT}")
        print(f"Mulai mengirim pesan ke topic: {TOPIC}")
        print("Tekan Ctrl+C untuk berhenti...")

        count = 1
        while True:
            # Buat pesan dummy
            pesan = {
                "id": count,
                "data": f"Halo MQTT, ini pesan ke-{count}",
                "timestamp": time.time()
            }
            payload = json.dumps(pesan)
            
            # Publish pesan
            result = client.publish(TOPIC, payload)
            
            # Cek status pengiriman (opsional)
            status = result[0]
            if status == 0:
                print(f"Terkirim: {payload}")
            else:
                print(f"Gagal mengirim pesan ke {TOPIC}")

            count += 1
            time.sleep(2) # Kirim setiap 2 detik

    except KeyboardInterrupt:
        print("\nPublisher dihentikan.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run_publisher()
