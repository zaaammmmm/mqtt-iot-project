#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ===== WiFi & MQTT Config =====
const char* ssid = "";
const char* password = "";

const char* mqtt_server = "test.mosquitto.org";
const char* clientId = "esp-sensor-suhu-3";
const char* topicTemp = "sensor/esp32/3/temperature";
const char* topicHum = "sensor/esp32/3/humidity";
const char* topicLedControl = "sensor/esp32/3/led_control";

// ===== Pin Config =====
const int redLed = 18;
const int yellowLed = 19;
const int greenLed = 21;
const int dhtPin = 22;

// ===== Init =====
DHT dht(dhtPin, DHT11);
WiFiClient espClient;
PubSubClient client(espClient);

// ===== State =====
bool autoMode = true;  // default: LED mengikuti suhu otomatis

// ===== Setup =====
void setup() {
  Serial.begin(115200);

  pinMode(redLed, OUTPUT);
  pinMode(yellowLed, OUTPUT);
  pinMode(greenLed, OUTPUT);

  dht.begin();
  connectWiFi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

// ===== Connect WiFi =====
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// ===== MQTT Reconnect =====
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect(clientId)) {
      Serial.println("connected!");
      client.subscribe(topicLedControl);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(", retry in 5s");
      delay(5000);
    }
  }
}

// ===== MQTT Callback =====
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.print("Message received on ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(msg);

  if (String(topic) == topicLedControl) {
    if (msg == "AUTO_ENABLE") {
      autoMode = true;
      Serial.println("AUTO MODE ENABLED");
    } 
    else if (msg == "AUTO_DISABLE") {
      autoMode = false;
      digitalWrite(redLed, LOW);
      digitalWrite(yellowLed, LOW);
      digitalWrite(greenLed, LOW);
      Serial.println("AUTO MODE DISABLED");
    }

    if (!autoMode) {
      if (msg == "RED_ON") digitalWrite(redLed, HIGH);
      if (msg == "RED_OFF") digitalWrite(redLed, LOW);
      if (msg == "YELLOW_ON") digitalWrite(yellowLed, HIGH);
      if (msg == "YELLOW_OFF") digitalWrite(yellowLed, LOW);
      if (msg == "GREEN_ON") digitalWrite(greenLed, HIGH);
      if (msg == "GREEN_OFF") digitalWrite(greenLed, LOW);
    }
  }
}

// ===== Loop =====
void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();

  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (isnan(t) || isnan(h)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  char tempStr[8], humStr[8];
  dtostrf(t, 1, 2, tempStr);
  dtostrf(h, 1, 2, humStr);

  client.publish(topicTemp, tempStr);
  client.publish(topicHum, humStr);

  Serial.print("Temperature: "); Serial.print(tempStr);
  Serial.print(" °C  | Humidity: "); Serial.println(humStr);

  // ===== LED indikator suhu otomatis =====
  if (autoMode) {
    if (t > 30) {
      digitalWrite(redLed, HIGH);
      digitalWrite(yellowLed, LOW);
      digitalWrite(greenLed, LOW);
    } else if (t >= 25 && t <= 30) {
      digitalWrite(redLed, LOW);
      digitalWrite(yellowLed, HIGH);
      digitalWrite(greenLed, LOW);
    } else {
      digitalWrite(redLed, LOW);
      digitalWrite(yellowLed, LOW);
      digitalWrite(greenLed, HIGH);
    }
  }

  delay(2000);
}
