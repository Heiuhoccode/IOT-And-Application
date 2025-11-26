import cv2, json, time
import paho.mqtt.client as mqtt
from flask import Flask, Response, render_template, jsonify
from OcrPlate import OcrPlate
from smart_parking.parking_lot_status import parking_lot_status
app = Flask(__name__)

MQTT_BROKER = "YOUR_HOST"
MQTT_PORT = "YOUR_PORT"
MQTT_USER = "YOUR_USERNAME"
MQTT_PASS = "YOUR_PASSWORD"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

ocr_slot = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap_slot = cv2.VideoCapture(0)

ocr_in = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap_in = cv2.VideoCapture(2, cv2.CAP_DSHOW)

ocr_out = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap_out = cv2.VideoCapture(1, cv2.CAP_DSHOW)


with open("smart_parking/parking_labels.txt") as f:
    labels = f.read().splitlines()

with open("smart_parking/parking_area_coordinates.txt") as f:
    coords_lines = f.read().splitlines()
parking_lot_coords = [list(map(int, line.split())) for line in coords_lines]

def gen_slot():
    last_status = {}
    last_sent = {}
    last_publish_time = time.time()
    last_published_payload = None

    slot_memory = {}

    def stable_status(slot_name, current_status, stable_time=5.0):
        now = time.time()
        prev = slot_memory.get(slot_name, {"status": None, "time": now})

        if current_status != prev["status"]:
            slot_memory[slot_name] = {"status": current_status, "time": now}
            return prev["status"]

        if now - prev["time"] >= stable_time:
            return current_status
        return prev["status"]

    changed = False
    last_publish_time = time.time()
    last_published_payload = None

    while True:
        ret, frame = cap_slot.read()
        if not ret:
            continue

        status = {}
        for i, coords in enumerate(parking_lot_coords):
            slot_name = labels[i]
            slot_img = frame[coords[1]:coords[3], coords[0]:coords[2]]
            lot_status = parking_lot_status(slot_img)
            lot_status = stable_status(slot_name, lot_status, stable_time=4.0)
            plate_number = None

            if lot_status == "available":
                color = (0, 255, 0)
                text = slot_name
                status[slot_name] = {"status": "available", "plate": None}
            else:
                color = (0, 0, 255)
                ocr_slot.set_data(slot_img)
                plate_number = (
                    ocr_slot.digit_out if ocr_slot.digit_out != "unknow" else "???"
                )
                text = f"{slot_name}: {plate_number}"
                status[slot_name] = {"status": "occupied", "plate": plate_number}

                if plate_number == "???" and slot_name in last_status:
                    prev_plate = last_status[slot_name].get("plate")
                    if prev_plate:
                        plate_number = prev_plate
                        status[slot_name]["plate"] = prev_plate
                        text = f"{slot_name}: {prev_plate}"

            current = {"status": lot_status, "plate": plate_number}
            if last_sent.get(slot_name) != current:
                last_sent[slot_name] = current
                changed = True

            cv2.rectangle(frame, (coords[0], coords[1]), (coords[2], coords[3]), color, 2)
            cv2.putText(frame, text, (coords[0], coords[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        last_status = status

        current_time = time.time()
        if current_time - last_publish_time >= 2.5:
            payload = last_sent

            if not last_published_payload or last_published_payload != payload:
                mqtt_client.publish("camera/slots", json.dumps(payload))
                print("[Camera Slot-> Server]:", json.dumps(payload, indent=2))
                last_published_payload = payload.copy()

            else: pass

            last_publish_time = current_time
            changed = False

        ret2, buffer = cv2.imencode('.jpg', frame)
        if not ret2:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


def gen_entry_in():
    last_plate = None
    last_publish_time = 0

    while True:
        ret, frame = cap_in.read()
        if not ret:
            continue

        ocr_in.set_data(frame)
        plate = ocr_in.digit_out

        if plate != "unknow":
            current_time = time.time()
            if current_time - last_publish_time > 5 or last_plate!=plate:
                payload = {
                    "plate": plate,
                    "status": "in",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                mqtt_client.publish("camera/entry", json.dumps(payload))
                print("[Camera In -> Server]:", payload)
                last_plate = plate
                last_publish_time = current_time

        ret2, buffer = cv2.imencode('.jpg', frame)
        if not ret2:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


def gen_entry_out():
    last_plate = None
    last_publish_time = 0

    while True:
        ret, frame = cap_out.read()
        if not ret:
            continue

        ocr_out.set_data(frame)
        plate = ocr_out.digit_out

        if plate != "unknow":
            current_time = time.time()
            if current_time - last_publish_time > 5 or last_plate!=plate:
                payload = {
                    "plate": plate,
                    "status": "out",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                mqtt_client.publish("camera/entry", json.dumps(payload))
                print("[Camera Out -> Server]:", payload)
                last_plate = plate
                last_publish_time = current_time

        ret2, buffer = cv2.imencode('.jpg', frame)
        if not ret2:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route("/video_slot")
def video_slot():
    return Response(gen_slot(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/video_entry_in")
def video_entry_in():
    return Response(gen_entry_in(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/video_entry_out")
def video_entry_out():
    return Response(gen_entry_out(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
