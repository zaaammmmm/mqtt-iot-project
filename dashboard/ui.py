# dashboard/ui.py - Dashboard UI dengan tkinter
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import threading
from collections import deque

class DashboardUI:
    """Dashboard UI untuk monitoring data real-time"""

    def __init__(self, mqtt_client, config_file='config.json'):
        """Inisialisasi dashboard"""
        # Load konfigurasi
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.config = config
        self.mqtt_client = mqtt_client

        # Root window
        self.root = tk.Tk()
        self.root.title(config['dashboard']['title'])
        self.root.geometry(f"{config['dashboard']['width']}x{config['dashboard']['height']}")
        self.root.resizable(False, False)

        # Data storage (untuk grafik)
        self.data_history = {
            'temperature': deque(maxlen=60),
            'humidity': deque(maxlen=60),
            'pressure': deque(maxlen=60)
        }

        # Current values
        self.current_values = {
            'temperature': 0.0,
            'humidity': 0.0,
            'pressure': 0.0,
            'led_status': 'OFF',
            'last_update': None
        }

        # Status tracking
        self.is_running = True
        self.connection_status = False

        # Setup UI
        self.setup_ui()

        # Start message processor thread
        self.start_message_processor()

        print("[Dashboard] UI initialized")

    def setup_ui(self):
        """Setup user interface"""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Header frame
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        # Title
        title_label = ttk.Label(
            header_frame,
            text="IoT Real-time Dashboard",
            font=("Arial", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Connection status
        self.status_label = ttk.Label(
            header_frame,
            text="● Disconnected",
            font=("Arial", 10),
            foreground="red"
        )
        self.status_label.pack(side=tk.RIGHT)

        # Main content frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # === Sensor Data Section ===
        sensor_frame = ttk.LabelFrame(main_frame, text="Sensor Data", padding=15)
        sensor_frame.pack(fill=tk.X, pady=10)

        # Temperature
        temp_frame = ttk.Frame(sensor_frame)
        temp_frame.pack(fill=tk.X, pady=10)

        ttk.Label(temp_frame, text="Temperature:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.temp_value_label = ttk.Label(
            temp_frame,
            text="--°C",
            font=("Arial", 14, "bold"),
            foreground="blue"
        )
        self.temp_value_label.pack(side=tk.LEFT, padx=20)

        self.temp_progress = ttk.Progressbar(
            temp_frame,
            length=300,
            maximum=50,
            mode='determinate'
        )
        self.temp_progress.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Humidity
        humidity_frame = ttk.Frame(sensor_frame)
        humidity_frame.pack(fill=tk.X, pady=10)

        ttk.Label(humidity_frame, text="Humidity:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.humidity_value_label = ttk.Label(
            humidity_frame,
            text="--%",
            font=("Arial", 14, "bold"),
            foreground="green"
        )
        self.humidity_value_label.pack(side=tk.LEFT, padx=20)

        self.humidity_progress = ttk.Progressbar(
            humidity_frame,
            length=300,
            maximum=100,
            mode='determinate'
        )
        self.humidity_progress.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Pressure
        pressure_frame = ttk.Frame(sensor_frame)
        pressure_frame.pack(fill=tk.X, pady=10)

        ttk.Label(pressure_frame, text="Pressure:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.pressure_value_label = ttk.Label(
            pressure_frame,
            text="-- hPa",
            font=("Arial", 14, "bold"),
            foreground="purple"
        )
        self.pressure_value_label.pack(side=tk.LEFT, padx=20)

        self.pressure_progress = ttk.Progressbar(
            pressure_frame,
            length=300,
            maximum=1050,
            mode='determinate'
        )
        self.pressure_progress.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # === Device Control Section ===
        control_frame = ttk.LabelFrame(main_frame, text="Device Control", padding=15)
        control_frame.pack(fill=tk.X, pady=10)

        # LED Status
        led_status_frame = ttk.Frame(control_frame)
        led_status_frame.pack(fill=tk.X, pady=10)

        ttk.Label(led_status_frame, text="LED Status:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.led_status_label = ttk.Label(
            led_status_frame,
            text="OFF",
            font=("Arial", 12, "bold"),
            foreground="red"
        )
        self.led_status_label.pack(side=tk.LEFT, padx=20)

        # LED Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Turn ON",
            command=self.send_led_command_on
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Turn OFF",
            command=self.send_led_command_off
        ).pack(side=tk.LEFT, padx=5)

        # === Status Section ===
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding=15)
        status_frame.pack(fill=tk.X, pady=10)

        self.last_update_label = ttk.Label(
            status_frame,
            text="Last update: --",
            font=("Arial", 10)
        )
        self.last_update_label.pack(anchor=tk.W, padx=5)

        self.message_count_label = ttk.Label(
            status_frame,
            text="Messages received: 0",
            font=("Arial", 10)
        )
        self.message_count_label.pack(anchor=tk.W, padx=5)

        self.broker_info_label = ttk.Label(
            status_frame,
            text=f"Broker: {self.config['broker']['host']}:{self.config['broker']['port']}",
            font=("Arial", 10)
        )
        self.broker_info_label.pack(anchor=tk.W, padx=5)

    def send_led_command_on(self):
        """Kirim command LED ON"""
        self.mqtt_client.publish('led_command', {'action': 'on'})
        messagebox.showinfo("Success", "LED ON command sent")

    def send_led_command_off(self):
        """Kirim command LED OFF"""
        self.mqtt_client.publish('led_command', {'action': 'off'})
        messagebox.showinfo("Success", "LED OFF command sent")

    def update_sensor_display(self, topic, data):
        """Update display sensor data"""
        try:
            if 'temperature' in data:
                temp = data['temperature']
                self.current_values['temperature'] = temp
                self.data_history['temperature'].append(temp)
                self.temp_value_label.config(text=f"{temp:.1f}°C")
                self.temp_progress['value'] = temp

            if 'humidity' in data:
                humidity = data['humidity']
                self.current_values['humidity'] = humidity
                self.data_history['humidity'].append(humidity)
                self.humidity_value_label.config(text=f"{humidity:.0f}%")
                self.humidity_progress['value'] = humidity

            if 'pressure' in data:
                pressure = data['pressure']
                self.current_values['pressure'] = pressure
                self.data_history['pressure'].append(pressure)
                self.pressure_value_label.config(text=f"{pressure:.1f} hPa")
                self.pressure_progress['value'] = pressure

            # Update last update time
            now = datetime.now().strftime("%H:%M:%S")
            self.current_values['last_update'] = now
            self.last_update_label.config(text=f"Last update: {now}")

        except Exception as e:
            print(f"[Dashboard] Error updating display: {e}")

    def process_messages(self):
        """Process incoming MQTT messages"""
        message_count = 0

        while self.is_running:
            try:
                # Check connection status
                if self.mqtt_client.check_connection():
                    if not self.connection_status:
                        self.connection_status = True
                        self.status_label.config(text="● Connected", foreground="green")
                        print("[Dashboard] Connected to MQTT")
                else:
                    if self.connection_status:
                        self.connection_status = False
                        self.status_label.config(text="● Disconnected", foreground="red")
                        print("[Dashboard] Disconnected from MQTT")

                # Get message dari queue
                msg = self.mqtt_client.get_message(timeout=0.5)

                if msg:
                    message_count += 1
                    topic = msg['topic']
                    data = msg['data']

                    # Update display berdasarkan topic
                    if 'temperature' in topic:
                        self.update_sensor_display(topic, data)
                    elif 'humidity' in topic:
                        self.update_sensor_display(topic, data)
                    elif 'pressure' in topic:
                        self.update_sensor_display(topic, data)

                    # Update message count
                    self.message_count_label.config(
                        text=f"Messages received: {message_count}"
                    )

            except Exception as e:
                print(f"[Dashboard] Error processing messages: {e}")

    def start_message_processor(self):
        """Mulai thread untuk process MQTT messages"""
        thread = threading.Thread(target=self.process_messages, daemon=True)
        thread.start()

    def run(self):
        """Jalankan dashboard"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"[Dashboard] Error: {e}")
        finally:
            self.is_running = False
            self.mqtt_client.disconnect()

    def get_data_history(self):
        """Dapatkan history data"""
        return self.data_history