import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    ("smart_light", os.path.join(BASE_DIR, "smart_light.py")),
    ("monitor", os.path.join(BASE_DIR, "smart_light2", "monitor.py")),
    ("remote", os.path.join(BASE_DIR, "smart_light2", "remote.py")),
]

procs = []

try:
    for name, path in scripts:
        print(f"[launcher] Menjalankan {name} -> {path}")
        p = subprocess.Popen([sys.executable, path])
        procs.append(p)

    # Tunggu semua proses sampai selesai / Ctrl+C
    for p in procs:
        p.wait()

except KeyboardInterrupt:
    print("[launcher] KeyboardInterrupt diterima. Menghentikan semua proses anak...")
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
finally:
    print("[launcher] Selesai.")