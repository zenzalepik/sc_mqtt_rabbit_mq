# Setup Manual RabbitMQ Cluster

Karena proses download otomatis gagal (kemungkinan masalah jaringan/firewall), Anda perlu menyiapkan file server secara manual.

## 1. Download File
Silakan download 2 file berikut:

1.  **Erlang OTP 26.2.2** (Windows 64-bit Binary / EXE)
    *   Link: [https://github.com/erlang/otp/releases/download/OTP-26.2.2/otp_win64_26.2.2.exe](https://github.com/erlang/otp/releases/download/OTP-26.2.2/otp_win64_26.2.2.exe)
2.  **RabbitMQ Server 3.13.0** (Windows Binary Zip)
    *   Link: [https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.0/rabbitmq-server-windows-3.13.0.zip](https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.0/rabbitmq-server-windows-3.13.0.zip)

## 2. Ekstrak ke Folder Tools
Siapkan folder `D:\Github\sc_mqtt_rabbit_mq\tools` (jika belum ada).

1.  **Erlang**:
    *   Install atau ekstrak file EXE tersebut.
    *   Pindahkan hasil instalasi/ekstrak agar folder `bin` berada di:
        `D:\Github\sc_mqtt_rabbit_mq\tools\erlang\bin\erl.exe`
2.  **RabbitMQ**:
    *   Ekstrak file ZIP.
    *   Rename folder hasil ekstrak menjadi `rabbitmq`.
    *   Pastikan file `rabbitmq-server.bat` berada di:
        `D:\Github\sc_mqtt_rabbit_mq\tools\rabbitmq\sbin\rabbitmq-server.bat`

## 3. Jalankan Cluster
Setelah file siap:
1.  Buka terminal di `D:\Github\sc_mqtt_rabbit_mq\mqtt_rabbit_mq_cluster\ps1`
2.  Jalankan: `.\start_cluster.ps1`
