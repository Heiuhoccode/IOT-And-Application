const mqtt = require("mqtt");
const db = require("./db");
// ===== Thông tin broker (ví dụ HiveMQ Cloud) =====
const broker =
  "mqtts://4e01ee67ec4e475ca4c3b68e2703f19e.s1.eu.hivemq.cloud:8883";
const options = {
  username: "Nhom3iot",
  password: "Nhom3iot",
};

// ===== Kết nối broker =====
const client = mqtt.connect(broker, options);

// ===== Khi kết nối thành công =====
client.on("connect", () => {
  console.log("✅ Connected to MQTT broker");
  client.subscribe(["camera/slots", "camera/entry", "sensor/dht22"], (err) => {
    if (!err) console.log("✅ Subscribed");
  });
});

const slotStatus = {
  s1: "available",
  s2: "available",
  s3: "available",
  s4: "available",
};
// ===== Lắng nghe dữ liệu nhận được =====
client.on("message", (topic, message) => {
  console.log(`📥 Message from ${topic}: ${message.toString()}`);

  try {
    const data = JSON.parse(message);
    if (topic === "camera/entry") {
      const date = new Date(data.ts);           // 2025-11-25T15:26:11 (VN)
      const utc = new Date(date.getTime() + 14*60*60*1000);
      const mysqlTime = utc.toISOString().slice(0, 19).replace("T", " ");
      const plate = data.plate.replaceAll(" ", "");

      // Tạo payload ban đầu
      const pub = { plate, status: "", valid: true };

      // 🔍 Kiểm tra biển số trong DB
      db.query(
        "SELECT * FROM Vehicle WHERE license_plate = ?",
        [plate],
        (err, result) => {
          if (err) {
            console.error("❌ DB error:", err);
            pub.valid = false; // lỗi DB → coi như không hợp lệ
          } else if (result.length === 0) {
            console.log("🚫 Không tìm thấy biển số:", plate);
            pub.valid = false;
          } else {
            console.log("✅ Biển số hợp lệ:", plate);
            db.query(
              "SELECT * FROM ParkingHistory WHERE vehicle_id = ?",
              [result[0].vehicle_id],
              (error, result1) => {
                if (error) {
                  console.log(error);
                }
                if (data.status === "in") {
                  pub.status = "in";
                  client.publish("plate/valid", JSON.stringify(pub), (err) => {
                    if (err) console.error("❌ Publish error:", err);
                    else console.log("🚀 Sent plate/valid:", pub);
                  });
                  if (result1.length === 0 || result1[result1.length - 1].time_out !== null){
                    db.query(
                      "INSERT INTO ParkingHistory (time_in,vehicle_id) VALUES (?,?)",
                      [mysqlTime, result[0].vehicle_id],
                      (err, result2) => {
                        if (err) {
                          console.log("❌ Insert error:", err);
                        } else {
                          console.log("✅ Inserted new parkinghistory");
                        }
                      }
                    );
                  }
                } else {
                  pub.status = "out";
                  client.publish("plate/valid", JSON.stringify(pub), (err) => {
                    if (err) console.error("❌ Publish error:", err);
                    else console.log("🚀 Sent plate/valid:", pub);
                  });
                  db.query(
                    "UPDATE ParkingHistory SET time_out = ? WHERE history_id = ?",
                    [mysqlTime, result1[result1.length - 1].history_id],
                    (error) => {
                      if (error) {
                        console.log(error);
                      }
                    }
                  );
                }
              }
            );
          }

          // ✅ Publish sau khi query hoàn tất
        }
      );
    }

    if (topic === "camera/slots") {
      try {
        let slotsMemory = {};
        Object.entries(data).forEach(([slotName, info]) => {
          let { status, plate } = info;

          const now = Date.now() / 1000;
          slotStatus[slotName] = status;
          // Nếu OCR lỗi hoặc ??? -> dùng dữ liệu cũ trong 10 giây gần nhất
          if (!plate || plate === "???") {
            const prev = slotsMemory[slotName];
            if (prev && now - prev.time < 10) {
              plate = prev.plate;
              status = prev.status;
            } else {
              plate = null;
            }
          }

          // Cập nhật bộ nhớ slot
          slotsMemory[slotName] = { plate, status, time: now };

          // Nếu biển số hợp lệ và xe đang đỗ -> gửi lại cho ESP32
          if (plate && status === "occupied") {
            plate = plate.replaceAll(" ", "");
            const slotIndex = parseInt(slotName.replace("s", ""));
            const payload = JSON.stringify({
              plate,
              status,
              slot: slotIndex,
            });

            client.publish("plate/slot", payload);
            console.log("[MQTT -> ESP32]", payload);
            db.query(
              "SELECT vehicle_id FROM Vehicle WHERE license_plate = ?",
              [plate],
              (error, result) => {
                if (error) {
                  console.log(error);
                }
                if (result.length != 0) {
                  db.query(
                    "UPDATE ParkingHistory SET slot_id = ? WHERE vehicle_id = ? AND time_out IS NULL",
                    [slotIndex, result[0].vehicle_id],
                    (error) => {
                      if (error) {
                        console.log(error);
                      }
                    }
                  );
                }
              }
            );
          }

          // Nếu slot trống -> thông báo cho ESP32
          if (status === "available") {
            const slotIndex = parseInt(slotName.replace("s", ""));
            const payload = JSON.stringify({
              plate: null,
              status,
              slot: slotIndex,
            });

            client.publish("plate/slot", payload);
            console.log("[MQTT -> ESP32]", payload);
          }
        });
      } catch (err) {
        console.error("Error parsing MQTT message:", err.message);
      }
    }
    if (topic === "sensor/dht22") {
      const toMySQLDatetime = (isoString) => {
        const date = new Date(isoString);
        const offset = 7 * 60 * 60 * 1000; // +7h múi giờ Việt Nam
        const local = new Date(date.getTime() + offset);
        return local.toISOString().slice(0, 19).replace("T", " ");
      };
      const isoTime = data.timestamp;
      const mysqlTime = toMySQLDatetime(isoTime);

      db.query("SELECT * FROM EnvironmentData", (error, result) => {
        let k = 0;
        try {
          k =
            (new Date(mysqlTime) -
              new Date(result[result.length - 1].timestamp)) /
            1000;
        } catch (e) {
          k = 10;
        }
        if (k >= 10) {
          db.query("SELECT * FROM ParkingLot", (error, result1) => {
            client.publish(
              "Information",
              JSON.stringify({
                tenBai: result1[1].lot_name,
                diaChi: result1[1].location,
                tongSlot: result1[1].total_slot,
                nhietDo: data.temperature,
                doAm: data.humidity,
                status: slotStatus,
              })
            );
          });

          db.query(
            "INSERT INTO EnvironmentData (timeStamp,temperature,humidity,lot_id) VALUES (?,?,?,?)",
            [mysqlTime, data.temperature, data.humidity, 1],
            (error) => {
              if (error) {
                console.log(error);
              }
            }
          );
        }
      });
    }
  } catch (e) {
    console.error(e);
  }
});
