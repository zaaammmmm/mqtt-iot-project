# app.py (Fix realtime chart: thread-safe queue + proper datetime x-axis)
import tkinter as tk
from tkinter import messagebox
import time, threading, json, os, queue
from collections import deque
import paho.mqtt.client as mqtt
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import customtkinter as ctk
from datetime import datetime
import matplotlib.dates as mdates

# -------------------- CONFIG --------------------
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPIC_TEMP = "sensor/esp32/3/temperature"
TOPIC_HUM  = "sensor/esp32/3/humidity"
TOPIC_LED  = "sensor/esp32/3/led_control"
CLIENT_ID  = "desktop-monitor-ahmad"

NAMA = "Bintang Wishnu Pradana"
NIM  = "23106050064"
KELOMPOK = "Kelompok 3"

MAX_POINTS = 100  # max history

# thread-safe queue to receive messages from MQTT callback
mqtt_queue = queue.Queue()

# deques for plotting
temps = deque(maxlen=MAX_POINTS)
hums = deque(maxlen=MAX_POINTS)
times = deque(maxlen=MAX_POINTS)   # store datetime objects

auto_led_enabled = True

# -------------------- MQTT CALLBACKS --------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ MQTT connected.")
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_HUM)
        print(f"Subscribed to: {TOPIC_TEMP}, {TOPIC_HUM}")
    else:
        print("❌ MQTT failed, rc =", rc)

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore").strip()
    # debug print so user sees incoming messages in terminal
    print(f"[MQTT RX] {msg.topic}: {payload}")
    # push to thread-safe queue (use datetime.now() here)
    mqtt_queue.put((msg.topic, payload, datetime.now()))

def start_mqtt():
    try:
        client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.V4)
    except Exception:
        client = mqtt.Client(client_id=CLIENT_ID)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        return client
    except Exception as e:
        messagebox.showerror("MQTT Error", f"Gagal connect ke broker:\n{e}")
        return None

# -------------------- THEME --------------------
theme_path = os.path.join("assets", "theme.json")
if os.path.exists(theme_path):
    with open(theme_path, "r") as f:
        theme = json.load(f)
        ctk.set_appearance_mode(theme.get("appearance_mode", "dark"))
        ctk.set_default_color_theme(theme.get("color_theme", "blue"))
else:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

# -------------------- MAIN APP --------------------
class App(ctk.CTk):
    def __init__(self, mqtt_client):
        super().__init__()
        self.mqtt_client = mqtt_client
        self.title("🌡️ Monitoring Suhu & Kelembaban — ESP32")
        self.geometry("1000x620")
        self.resizable(False, False)

        # === HEADER ===
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(padx=15, pady=10, fill="x")
        ctk.CTkLabel(header, text=f"👤 {NAMA} | 🆔 {NIM} | 👥 {KELOMPOK}",
                     font=("Segoe UI", 16, "bold")).pack(pady=8)

        # === MAIN CONTENT ===
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        left_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_frame = ctk.CTkFrame(main_frame, width=260, corner_radius=12)
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        # === CHART ===
        self.fig = Figure(figsize=(6.5, 4.5))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("📈 Grafik Suhu (°C) & Kelembaban (%)")
        self.ax.set_xlabel("Waktu (HH:MM:SS)")
        self.ax.grid(True)
        # initial empty lines
        self.temp_line, = self.ax.plot([], [], label="Suhu (°C)", color="#ff6363", linewidth=2)
        self.hum_line,  = self.ax.plot([], [], label="Kelembaban (%)", color="#4facfe", linewidth=2)
        self.ax.legend(loc="upper right")

        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # === RIGHT PANEL ===
        self.auto_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(
            right_frame, text="Auto LED (indikator suhu)",
            variable=self.auto_var, command=self.toggle_auto,
            font=("Segoe UI", 13)
        ).pack(pady=(20, 10))

        ctk.CTkLabel(right_frame, text="Manual LED Control",
                     font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))

        btns = [
            ("🔴 Red ON", "#ff4d4d", "RED_ON"),
            ("⚫ Red OFF", "#333333", "RED_OFF"),
            ("🟡 Yellow ON", "#ffd633", "YELLOW_ON"),
            ("⚫ Yellow OFF", "#333333", "YELLOW_OFF"),
            ("🟢 Green ON", "#33cc33", "GREEN_ON"),
            ("⚫ Green OFF", "#333333", "GREEN_OFF")
        ]
        for t, c, cmd in btns:
            ctk.CTkButton(right_frame, text=t, fg_color=c, hover_color="#202020",
                          text_color="white", command=lambda x=cmd: self.publish_led(x)).pack(fill="x", padx=10, pady=4)

        self.status = ctk.CTkLabel(self, text="🔌 MQTT: Connecting...", anchor="w", font=("Segoe UI", 12))
        self.status.pack(side="bottom", fill="x", pady=(0, 5), padx=10)

        # Setup x-axis formatter for datetime
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

        # Start update loop
        self.after(300, self.update_data)   # slightly faster polling

    # -------------------- MQTT --------------------
    def toggle_auto(self):
        global auto_led_enabled
        auto_led_enabled = bool(self.auto_var.get())
        cmd = "AUTO_ENABLE" if auto_led_enabled else "AUTO_DISABLE"
        self.publish_led(cmd)
        self.set_status(f"Auto LED {'ENABLED' if auto_led_enabled else 'DISABLED'}")

    def publish_led(self, msg):
        try:
            if self.mqtt_client:
                self.mqtt_client.publish(TOPIC_LED, msg)
                print(f"[MQTT TX] {msg}")
            else:
                print("[MQTT TX] client not connected")
        except Exception as e:
            print("Publish error:", e)

    def set_status(self, txt):
        self.status.configure(text=f"🔌 {txt}")

    # -------------------- DATA UPDATE LOOP --------------------
    def update_data(self):
        """
        Dipanggil di main thread lewat after().
        Mengambil semua pesan dari mqtt_queue (thread-safe), memproses, lalu menggambar chart.
        """
        updated = False

        # drain the thread-safe queue
        while True:
            try:
                topic, payload, ts = mqtt_queue.get_nowait()
            except queue.Empty:
                break

            # attempt to parse numeric value robustly
            val = None
            try:
                val = float(payload)
            except Exception:
                # last token mungkin angka, misal "Temperature: 30.2"
                try:
                    val = float(payload.split()[-1])
                except Exception:
                    val = None

            if val is None:
                # non-numeric payload (could be status message) — show on status
                self.set_status(f"{topic}: {payload}")
                continue

            # append data
            if topic == TOPIC_TEMP:
                temps.append(val)
                times.append(ts)
                updated = True
            elif topic == TOPIC_HUM:
                hums.append(val)
                # ensure times length covers hums (if humidity arrives before temp)
                if len(times) < len(hums):
                    times.append(ts)
                updated = True

        # if any new data, update plot
        if updated and len(times) > 0:
            # convert datetime objects to matplotlib numeric format
            x_nums = mdates.date2num(list(times))

            # update lines with their respective recent slices
            # ensure x and y lengths match per line:
            # temps correspond to the last len(temps) x points
            if len(x_nums) >= len(temps):
                xs_temp = x_nums[-len(temps):]
            else:
                xs_temp = x_nums

            if len(x_nums) >= len(hums):
                xs_hum = x_nums[-len(hums):]
            else:
                xs_hum = x_nums

            try:
                self.temp_line.set_data(xs_temp, list(temps))
                self.hum_line.set_data(xs_hum, list(hums))
            except Exception as e:
                print("Set data error:", e)

            # update axes limits and format
            self.ax.relim()
            self.ax.autoscale_view()

            # optionally set x limits to recent window (last N seconds)
            # window_seconds = 60
            # now_num = mdates.date2num(datetime.now())
            # left = mdates.date2num(datetime.now()) - window_seconds / 86400.0
            # self.ax.set_xlim(left, now_num)

            self.fig.autofmt_xdate()
            # force immediate draw on the main thread
            self.canvas.draw()

            # update status with last values
            last_temp = temps[-1] if temps else None
            last_hum = hums[-1] if hums else None
            if last_temp is not None and last_hum is not None:
                self.set_status(f"Receiving data... Suhu: {last_temp:.2f}°C | Kelembaban: {last_hum:.2f}%")
            elif last_temp is not None:
                self.set_status(f"Receiving data... Suhu: {last_temp:.2f}°C")
            elif last_hum is not None:
                self.set_status(f"Receiving data... Kelembaban: {last_hum:.2f}%")

        # schedule next poll
        self.after(300, self.update_data)

# -------------------- MAIN --------------------
def main():
    mqtt_client = start_mqtt()
    app = App(mqtt_client)

    def wait_connect():
        for _ in range(10):
            if mqtt_client and mqtt_client.is_connected():
                app.set_status("Connected ✅")
                return
            time.sleep(0.5)
        app.set_status("⚠️ MQTT not connected")

    threading.Thread(target=wait_connect, daemon=True).start()
    app.mainloop()

    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
