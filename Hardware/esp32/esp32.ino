#include <ESP32Servo.h>
#include <DHT.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <sstream>
#include <ArduinoJson.h>

//Cấu hình phần cứng
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

//Cấu hình WiFi
const char* ssid = "testnetwork";
const char* password = "11223344";

//Cấu hình MQTT
const char* mqtt_server = "4e01ee67ec4e475ca4c3b68e2703f19e.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "Nhom3iot";
const char* mqtt_pass = "Nhom3iot";
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ====== Thời gian gửi dữ liệu DHT ======
unsigned long lastDHTTime = 0;
const long DHTInterval = 3000;

// Biến trạng thái IR và servo
unsigned long lastDetectedIN = 0;
unsigned long lastDetectedOUT = 0;
bool isServoINOpen = false;
bool isServoOUTOpen = false;

// ====== Cấu hình múi giờ Việt Nam (UTC+7) ======
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 7 * 3600;
const int daylightOffset_sec = 0;

// ====== Thêm vào phần khai báo biến toàn cục ======
bool slotStatus[4] = {false, false, false, false}; // false = trống, true = đã đỗ
unsigned long lastLCDUpdate = 0;
bool lcdBusy = false; // LCD đang hiển thị nội dung sự kiện

bool hasBeepedFull = false;

// ====== Hàm kết nối WiFi ======
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

// ====== Callback khi có tin nhắn MQTT ======
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
        // Mở cổng IN
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
        // Mở cổng OU
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

// ====== Kết nối MQTT ======
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

// ====== Lấy timestamp thực tế ======
String getFormattedTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "unknown";
  }
  char buffer[30];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buffer);
}

// ====== Setup ======
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

  espClient.setInsecure(); // Không kiểm tra chứng chỉ TLS
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  Serial.println("Đang đồng bộ NTP...");
  delay(2000);
  Serial.println("✅ NTP đồng bộ xong!");
}

// ====== Loop ======
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
  //Tự động đóng cổng IN
  int irIN = digitalRead(IR_IN_PIN);
  if (irIN == LOW) {  // Phát hiện vật cản
    lastDetectedIN = millis(); // reset thời gian
  }

  // Nếu servo đang mở và không thấy vật trong >2.5s → đóng lại
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

  //Tự động đóng cổng OUT
  int irOUT = digitalRead(IR_OUT_PIN);
  if (irOUT == LOW) {  // Phát hiện vật cản
    lastDetectedOUT = millis(); // reset thời gian
  }

  // Nếu servo đang mở và không thấy vật trong >2.5s → đóng lại
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


  
  //Hiển thị slot trên LCD
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

    // Chỉ kêu 1 lần duy nhất
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
    // reset nếu không còn full
    hasBeepedFull = false;
  }

  if (!lcdBusy && millis() - lastLCDUpdate > 5000) { // mỗi 5 giây hiển thị lại
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
