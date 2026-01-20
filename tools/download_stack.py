import os
import sys
import requests
import subprocess
import shutil
import zipfile
import time

# Configuration
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
# Try erlang.org for Erlang (sometimes more stable than GitHub redirects)
ERLANG_URL = "https://github.com/erlang/otp/releases/download/OTP-26.2.2/otp_win64_26.2.2.exe"
# Fallback/Alternate: https://erlang.org/download/otp_win64_26.2.2.exe

RABBITMQ_URL = "https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.0/rabbitmq-server-windows-3.13.0.zip"

# MANUAL FILE NAMES (What user likely downloads)
ERLANG_MANUAL = os.path.join(TOOLS_DIR, "otp_win64_26.2.2.exe")
RABBITMQ_MANUAL = os.path.join(TOOLS_DIR, "rabbitmq-server-windows-3.13.0.zip")

ERLANG_EXE = os.path.join(TOOLS_DIR, "erlang_installer.exe")
RABBITMQ_ZIP = os.path.join(TOOLS_DIR, "rabbitmq.zip")

ERLANG_DIR = os.path.join(TOOLS_DIR, "erlang")
RABBITMQ_DIR = os.path.join(TOOLS_DIR, "rabbitmq")

def check_manual_files():
    # Check if user dropped the files manually and rename them for the script
    if os.path.exists(ERLANG_MANUAL):
        print(f"Found manual Erlang file: {ERLANG_MANUAL}")
        if os.path.exists(ERLANG_EXE): os.remove(ERLANG_EXE)
        os.rename(ERLANG_MANUAL, ERLANG_EXE)
        print("-> Renamed to erlang_installer.exe for processing.")
        
    if os.path.exists(RABBITMQ_MANUAL):
        print(f"Found manual RabbitMQ file: {RABBITMQ_MANUAL}")
        if os.path.exists(RABBITMQ_ZIP): os.remove(RABBITMQ_ZIP)
        os.rename(RABBITMQ_MANUAL, RABBITMQ_ZIP)
        print("-> Renamed to rabbitmq.zip for processing.")

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        with requests.get(url, stream=True, headers=headers, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}% ({downloaded//1024} KB)", end="")
            print("\nDownload complete.")
            return True
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        return False

def extract_7z(archive, dest):
    print(f"Extracting {archive} using 7z...")
    try:
        # 7z x archive -o"dest" -y
        subprocess.run(["7z", "x", archive, f"-o{dest}", "-y"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"7z extraction failed: {e}")
        return False
    except FileNotFoundError:
        print("7z.exe not found in PATH. Please install 7-Zip.")
        return False

def setup_erlang():
    if os.path.exists(os.path.join(ERLANG_DIR, "bin", "erl.exe")):
        print("Erlang already installed.")
        return

    if not os.path.exists(ERLANG_EXE):
        if not download_file(ERLANG_URL, ERLANG_EXE):
            return

    # Extract
    temp_dir = os.path.join(TOOLS_DIR, "erlang_temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    if extract_7z(ERLANG_EXE, temp_dir):
        # Move content
        print("Organizing Erlang files...")
        # Check if bin is directly in temp or in subdir
        if os.path.exists(os.path.join(temp_dir, "bin")):
            target_source = temp_dir
        elif os.path.exists(os.path.join(temp_dir, "otp_win64_26.2.2", "bin")):
            target_source = os.path.join(temp_dir, "otp_win64_26.2.2")
        else:
            # Fallback
            target_source = temp_dir
            
        if os.path.exists(ERLANG_DIR):
            shutil.rmtree(ERLANG_DIR)
        
        shutil.move(target_source, ERLANG_DIR)
        shutil.rmtree(temp_dir)
        print("Erlang setup complete.")
        
        # Cleanup installer
        if os.path.exists(ERLANG_EXE):
            os.remove(ERLANG_EXE)

def setup_rabbitmq():
    if os.path.exists(os.path.join(RABBITMQ_DIR, "sbin", "rabbitmq-server.bat")):
        print("RabbitMQ already installed.")
        return

    if not download_file(RABBITMQ_URL, RABBITMQ_ZIP):
        print("Failed to download RabbitMQ.")
        return

    print("Extracting RabbitMQ...")
    try:
        with zipfile.ZipFile(RABBITMQ_ZIP, 'r') as zip_ref:
            zip_ref.extractall(TOOLS_DIR)
        
        # Rename
        extracted_dirs = [d for d in os.listdir(TOOLS_DIR) if d.startswith("rabbitmq_server-")]
        if extracted_dirs:
            src = os.path.join(TOOLS_DIR, extracted_dirs[0])
            if os.path.exists(RABBITMQ_DIR):
                shutil.rmtree(RABBITMQ_DIR)
            os.rename(src, RABBITMQ_DIR)
            print("RabbitMQ setup complete.")
            
            # Cleanup zip
            os.remove(RABBITMQ_ZIP)
        else:
            print("Could not find extracted RabbitMQ folder.")
            
    except Exception as e:
        print(f"Error extracting RabbitMQ: {e}")

def main():
    print("Starting Stack Setup (Python)...")
    setup_erlang()
    setup_rabbitmq()
    print("All tasks finished.")

if __name__ == "__main__":
    main()
