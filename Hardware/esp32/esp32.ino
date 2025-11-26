#include <ESP32Servo.h>
#include <DHT.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <sstream>
#include <ArduinoJson.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define SERVO_IN_PIN 14
#define SERVO_OUT_PIN 25
#define IR_IN_PIN 34
#define IR_OUT_PIN 35
#define BUZZER_PIN 15


int ledRed[4] = {26, 27, 32, 33};
LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servoIN;
Servo servoOUT;
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

const char* mqtt_server = "YOUR_HOST";
const int mqtt_port = "YOUR_PORT";
const char* mqtt_user = "YOUR_USERNAME";
const char* mqtt_pass = "YOUR_PASSWORD";
WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long lastDHTTime = 0;
const long DHTInterval = 3000;

unsigned long lastDetectedIN = 0;
unsigned long lastDetectedOUT = 0;
bool isServoINOpen = false;
bool isServoOUTOpen = false;

// ====== VietNam's Time Zone (UTC+7) ======
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 7 * 3600;
const int daylightOffset_sec = 0;

bool slotStatus[4] = {false, false, false, false}; // false = available, true = occupied
unsigned long lastLCDUpdate = 0;
bool lcdBusy = false;
bool hasBeepedFull = false;

void setup_wifi() {
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    lcd.print(".");
  }
  lcd.clear();
  lcd.print("WiFi connected");
  delay(1000);
}

// ====== Callback MQTT ======
void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)message[i];
  }

  Serial.print("SERVER -> ESP32 [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);


  if (String(topic) == "plate/valid") {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, msg);
    if (error){
       Serial.println("JSON parse failed!");
       return;
    }
    String plate = doc["plate"];
    bool valid = doc["valid"];
    String status = doc["status"];

    int irIN = digitalRead(IR_IN_PIN);
    int irOUT = digitalRead(IR_OUT_PIN);
    if (status == "in"){
      if (valid && irIN == LOW) {
        lcd.setCursor(0, 0);
        lcd.print(plate);
        lcd.setCursor(0, 1);
        lcd.print("Welcome");

        for (int pos = 0; pos <= 60; pos += 2) {
          servoIN.write(pos);
          delay(15);
        }
        isServoINOpen = true;
        lastDetectedIN = millis();
      } 
      else if (!valid) {
        lcd.setCursor(0, 0);
        lcd.print(plate);
        lcd.setCursor(0, 1);
        lcd.print("Invalid");
        delay(2000);
        lcd.clear();
      }  
    }
    if (status == "out"){
      if (valid && irOUT == LOW) {
        lcd.setCursor(0, 0);
        lcd.print(plate);
        lcd.setCursor(0, 1);
        lcd.print("See You Again");

        for (int pos = 0; pos <= 60; pos += 2) {
          servoOUT.write(pos);
          delay(15);
        }
        isServoOUTOpen = true;
        lastDetectedOUT = millis();
      } 
      else if (!valid) {
        lcd.setCursor(0, 0);
        lcd.print(plate);
        lcd.setCursor(0, 1);
        lcd.print("Invalid");
        delay(2000);
        lcd.clear();
      }  
    }
  }

  if (String(topic) == "plate/slot") {
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, msg);
    if (error){
       Serial.println("JSON parse failed!");
       return;
    }
    String plate = doc["plate"];
    String status = doc["status"];
    int slot = doc["slot"];
    if (status == "occupied"){
      digitalWrite(ledRed[slot-1], HIGH);
      slotStatus[slot - 1] = true;
    }
    else{
      digitalWrite(ledRed[slot-1], LOW);
      slotStatus[slot - 1] = false;
    } 
  }
  
}

void reconnect() {
  while (!client.connected()) {
    lcd.clear();
    lcd.print("MQTT connecting");
    String clientId = "ESP32-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      lcd.clear();
      lcd.print("MQTT connected");
      client.subscribe("plate/valid");
      client.subscribe("plate/slot");
    } else {
      lcd.clear();
      lcd.print("Retry...");
      delay(2000);
    }
  }
}

String getFormattedTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "unknown";
  }
  char buffer[30];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buffer);
}

void setup() {
  Serial.begin(115200);
  lcd.init();
  lcd.backlight();

  for (int i = 0; i < 4; i++) {
    pinMode(ledRed[i], OUTPUT);
  }
  pinMode(IR_IN_PIN, INPUT);
  pinMode(IR_OUT_PIN, INPUT);
  servoIN.attach(SERVO_IN_PIN);
  servoIN.write(0);
  servoOUT.attach(SERVO_OUT_PIN);
  servoOUT.write(0);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, HIGH);


  dht.begin();

  setup_wifi();

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Synchronizing NTP...");
  delay(2000);
  Serial.println("✅ Synchronized NTP!");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastDHTTime > DHTInterval) {
    lastDHTTime = now;
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (!isnan(t) && !isnan(h)) {
      String timestamp = getFormattedTime();
      String payload = "{\"temperature\": " + String(t, 1) + 
                       ", \"humidity\": " + String(h, 1) + 
                       ", \"timestamp\": " + "\"" + String(timestamp) + "\"" + "}";
      client.publish("sensor/dht22", payload.c_str());
      Serial.println("[ESP32 -> SERVER]: " + payload);
    }
  }

  int irIN = digitalRead(IR_IN_PIN);
  if (irIN == LOW) {
    lastDetectedIN = millis();
  }

  if (isServoINOpen && (millis() - lastDetectedIN > 2500)) {
    for (int pos = 60; pos >= 0; pos -= 2) {
      servoIN.write(pos);
      delay(15);
    }
    isServoINOpen = false;
    Serial.println("IN gate closed");
    lcd.clear();
    lcd.print("Closed");
  }

  int irOUT = digitalRead(IR_OUT_PIN);
  if (irOUT == LOW) {
    lastDetectedOUT = millis();
  }

  if (isServoOUTOpen && (millis() - lastDetectedOUT > 2500)) {
    for (int pos = 60; pos >= 0; pos -= 2) {
      servoOUT.write(pos);
      delay(15);
    }
    isServoOUTOpen = false;
    Serial.println("OUT gate closed");
    lcd.clear();
    lcd.print("Closed");
  }

  int occupied = 0;
  for (int i = 0; i < 4; i++) {
    if (slotStatus[i]) occupied++;
  }

  if (occupied == 4) {

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("PARKING FULL");
    lcd.setCursor(0, 1);
    lcd.print("No Slot Left!");

    if (!hasBeepedFull) {
      tone(BUZZER_PIN, 2000);
      delay(2500);
      noTone(BUZZER_PIN);
      hasBeepedFull = true;
    }

    lastLCDUpdate = millis();
    return;
  } 
  else {
    hasBeepedFull = false;
  }

  if (!lcdBusy && millis() - lastLCDUpdate > 5000) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Occupied: ");
    lcd.print(occupied);
    lcd.setCursor(0, 1);
    lcd.print("Available: ");
    lcd.print(4 - occupied);
    lastLCDUpdate = millis();
  }
}
