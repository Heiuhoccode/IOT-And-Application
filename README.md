# Smart Parking System -- IoT & Application Project

Hệ thống bãi đỗ xe thông minh (Smart Parking) được xây dựng dựa trên nền
tảng **IoT -- MQTT -- Machine Learning -- Web Application -- Desktop
App**.\
Dự án bao gồm nhiều thành phần hoạt động song song nhằm cung cấp khả
năng:

-   Nhận diện biển số xe tự động bằng YOLO + OCR
-   Giám sát slot bãi xe theo thời gian thực
-   Điều khiển barrier IN/OUT sử dụng ESP32
-   Gửi và nhận dữ liệu qua MQTT
-   Dashboard trực quan trên Web
-   Ứng dụng Kivy Desktop để giám sát và tra cứu lịch sử
-   Lưu trữ dữ liệu vào MySQL

## 1. Kiến trúc tổng thể hệ thống

Hệ thống được thiết kế theo mô hình **đa tác nhân** giao tiếp qua **MQTT
Broker**.

![IOT](https://github.com/user-attachments/assets/d5f08586-de5f-4516-a3e7-4004c982c658)

## 2. Thiết kế cơ sở dữ liệu

Database bao gồm 6 bảng chính: ParkingLot, Slot, Camera, Vehicle,
ParkingHistory, EnvironmentData.

![Entity Relationship Diagram1](https://github.com/user-attachments/assets/ea886e81-ee7b-47ef-aaff-284142bf6861)


## 3. Các thành phần hệ thống

### 3.1. ESP32 Controller

-   Điều khiển Servo IN/OUT
-   Đọc cảm biến DHT22
-   Điều khiển LED theo trạng thái slot
-   Gửi dữ liệu về WebServer qua MQTT

### 3.2. Camera Server

-   Dùng YOLO + OCR để nhận diện biển số
-   Gửi dữ liệu camera/entry & camera/slot qua MQTT

### 3.3. Web Server (Node.js)

-   Kiểm tra biển số hợp lệ
-   Tạo/Update ParkingHistory
-   Lưu sensor vào EnvironmentData
-   Trả thông tin tổng quan cho Dashboard

### 3.4. Web Dashboard (ReactJS)

-   Hiển thị trạng thái slot
-   Lịch sử vào/ra
-   Camera Dashboard

### 3.5. AppClient (Kivy)

-   Dashboard
-   Map slot
-   Tra cứu lịch sử theo biển số

## 4. Cách cài đặt

### Clone repo

    git clone https://github.com/Heiuhoccode/IOT-And-Application
    cd IOT-And-Application

## 5. Cấu trúc thư mục

    IOT-And-Application/
    │── AppClient/
    │── CameraServer/
    │── WebAdmin/
    │── WebServer/
    │── Hardware/
    │── README.md

## 6. MQTT Topics

  Topic          Producer       Consumer           Mô tả
  -------------- -------------- ------------------ -----------------
  camera/entry   CameraServer   WebServer          Xe vào/ra
  camera/slot    CameraServer   WebServer/ESP32    Xe slot
  plate/valid    WebServer      ESP32              Biển số hợp lệ
  plate/slot     WebServer      ESP32              Map slot
  sensor/dht22   ESP32          WebServer          Nhiệt độ/độ ẩm
  Information    WebServer      WebApp/AppClient   Dashboard

## 7. Chạy WebServer

    cd WebServer
    npm install
    node server.js

## 8. Chạy Camera Server

    cd CameraServer
    python main.py

## 9. Chạy AppClient

    cd AppClient
    python main.py

## 10. Chạy ESP32

-   Mở file .ino
-   Compile & Upload lên ESP32

## 11. Người thực hiện

**Nguyễn Đăng Hiếu (nhóm trưởng)**\
**Nguyễn Đăng Dương**\
**Nguyễn Khắc Dũng**\
**Đinh Việt Hiếu**\
**Hoàng Văn Hướng**\
**Nguyễn Thị Quỳnh Trang**

