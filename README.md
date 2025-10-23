# 🌡️ MQTT IoT Project – ESP32 + DHT11 + Python Desktop App

Proyek ini merupakan implementasi Internet of Things (IoT) menggunakan **ESP32**, **sensor DHT11**, dan **komunikasi MQTT** dengan **aplikasi desktop berbasis Python**.  
Dibuat sebagai bagian dari mata kuliah **Pemrograman Platform Desktop dan Embedded (PPDE)** oleh **Ahmad Zamroni Trikarta**.

---

## 📁 Struktur Proyek

```
mqtt-iot-project/
├── esp32/
│   └── firmware/
│       └── esp32_sensor_suhu.ino   # Firmware untuk ESP32 (Arduino IDE)
│
├── desktop_app/
│   ├── app.py                      # Aplikasi desktop (GUI + MQTT)
│   ├── requirements.txt             # Dependencies Python
│   └── README.md                    # Dokumentasi tambahan
│
├── LICENSE
└── README.md (ini)
```

---

## ⚙️ Fitur Utama

✅ Membaca data suhu dan kelembapan dari **sensor DHT11**  
✅ Mengirim data sensor ke **broker MQTT (test.mosquitto.org)**  
✅ Menampilkan data suhu & kelembapan secara **real-time** di aplikasi desktop  
✅ Kontrol LED ESP32 secara **manual** maupun **otomatis (auto mode)**  
✅ Menampilkan **grafik suhu dan kelembapan** secara live menggunakan Matplotlib  

---

## 🧠 Arsitektur Sistem

ESP32 ↔ MQTT Broker ↔ Desktop App

```
[ESP32] -- publish --> sensor/esp32/3/temperature
                    --> sensor/esp32/3/humidity
          <-- subscribe -- sensor/esp32/3/led_control

[Desktop App]
- Menampilkan data suhu/kelembapan secara live
- Mengirim perintah LED (RED, YELLOW, GREEN)
```

---

## 🛠️ Instalasi dan Setup

### 1️⃣ Persiapan ESP32
#### a. Hardware Connection
| Komponen | Pin ESP32 | Keterangan |
|-----------|------------|-------------|
| DHT11 (Data) | 22 | Pin input sensor |
| LED Merah | 18 | Indikator suhu > 30°C |
| LED Kuning | 19 | Indikator suhu 25–30°C |
| LED Hijau | 21 | Indikator suhu < 25°C |

#### b. Library Arduino
Pastikan sudah menginstal library berikut melalui **Arduino IDE → Sketch → Include Library → Manage Libraries**:
- `PubSubClient` (MQTT)
- `DHT sensor library` by Adafruit
- `Adafruit Unified Sensor`

#### c. Upload Firmware
1. Buka file:  
   ```
   esp32/firmware/esp32_sensor_suhu/esp32_sensor_suhu.ino
   ```
2. Sesuaikan SSID WiFi dan Password.
3. Pilih board `ESP32 Dev Module` dan port yang sesuai (misal COM3).
4. Upload dan buka **Serial Monitor** pada baud rate `115200`.

---

### 2️⃣ Persiapan Aplikasi Desktop
#### a. Instalasi Dependency
Masuk ke folder `desktop_app/` kemudian jalankan:
```bash
pip install -r requirements.txt
```

#### b. Jalankan Aplikasi
```bash
python app.py
```

#### c. Fitur di Aplikasi:
- **Monitoring Real-time** grafik suhu dan kelembapan.
- **Tombol kontrol LED** (RED, YELLOW, GREEN).
- **Auto Mode** untuk mengaktifkan logika otomatis LED berdasarkan suhu.

---

## 🧩 Topik MQTT yang Digunakan

| Topik | Deskripsi | Arah |
|--------|------------|------|
| `sensor/esp32/3/temperature` | Data suhu dari ESP32 | Publish |
| `sensor/esp32/3/humidity` | Data kelembapan dari ESP32 | Publish |
| `sensor/esp32/3/led_control` | Perintah kontrol LED | Subscribe |

Broker MQTT:
```
Host   : test.mosquitto.org
Port   : 1883
Client : mqttx-monitor-3
```

---

## 🎛️ Mode Otomatis (Auto LED Logic)

| Kondisi Suhu | LED Aktif |
|---------------|------------|
| > 30°C | 🔴 Merah |
| 25–30°C | 🟡 Kuning |
| < 25°C | 🟢 Hijau |

Jika **Auto Mode** dinonaktifkan, kontrol LED dapat dilakukan secara manual lewat tombol di aplikasi.

---

## 🖥️ Tampilan Aplikasi

- Realtime Chart (Suhu & Kelembapan)  
- Status koneksi MQTT  
- Tombol kontrol LED dan Auto Mode  

---

## 📜 Lisensi
Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---


