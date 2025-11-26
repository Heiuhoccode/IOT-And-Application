const express = require("express");
const db = require("./db");
const cors = require("cors");
require("./mqttHandler");
const app = express();
app.use(cors());
app.use(express.json());

// // Kết nối tới MySQL Clever Cloud
// const db = mysql.createConnection({
//   host: "binzkjb5rditypwr6b8r-mysql.services.clever-cloud.com",
//   user: "uziwfoaieje3u6sj",
//   password: "hQN6EvKO4kAwg4s3sScS",
//   database: "binzkjb5rditypwr6b8r",
//   port: 3306,
// });

// INSERT
// db.query(
//   "INSERT INTO Vehicle (license_plate, vehicle_type) VALUES (?, ?)",
//   ["67C1-03786", "car"],
//   (err, result) => {
//     if (err) {
//       console.error("❌ Insert error:", err);
//     } else {
//       console.log("✅ Inserted new vehicle, ID:", result.insertId);
//     }
//   }
// );

// update;
// db.query(
//   "UPDATE ParkingLot SET total_slot = ? WHERE lot_id = ?",
//   [4, 2],
//   (err, result) => {
//     if (err) {
//       console.error("❌ Lỗi khi cập nhật:", err);
//     } else {
//       console.log(
//         "✅ Cập nhật thành công, số dòng ảnh hưởng:",
//         result.affectedRows
//       );
//     }
//   }
// );

//Xoa thuoc tinh
// db.query("ALTER TABLE ParkingHistory DROP COLUMN gate_action", (err, result) => {
//   if (err) {
//     console.error("❌ Lỗi khi xóa cột:", err);
//   } else {
//     console.log("✅ Đã xóa cột khỏi bảng ");
//   }
// });

//delete
db.query("DELETE FROM EnvironmentData", (error) => {
  if (error) {
    console.log(error);
  }
});
// db.query("DELETE FROM ParkingHistory", (error) => {
//   if (error) {
//     console.log(error);
//   }
// });
// Camera
app.get("/camera", (req, res) => {
  db.query("SELECT * FROM Camera", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});

// Vehicle
app.get("/vehicle", (req, res) => {
  db.query("SELECT * FROM Vehicle", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});

// ParkingLot
app.get("/parking-lot", (req, res) => {
  db.query("SELECT * FROM ParkingLot", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});
app.post("/parking-lot", (req, res) => {
  const { lot_name, location, total_slot } = req.body;

  const sql =
    "INSERT INTO ParkingLot (lot_name, location, total_slot) VALUES (?, ?, ?)";
  db.query(sql, [lot_name, location, total_slot], (err, result) => {
    if (err) {
      console.error("❌ Insert failed:", err);
      return res.status(500).json({ message: "Database error" });
    }
    res.json({
      message: "✅ Added new ParkingLot successfully",
      id: result.insertId,
    });
  });
});

// EnvironmentData
app.get("/envirnoment-data", (req, res) => {
  db.query("SELECT * FROM EnvironmentData", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});

// Slot
app.get("/slot", (req, res) => {
  db.query("SELECT * FROM Slot", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});

// ParkingHistory
app.get("/parking-history", (req, res) => {
  db.query("SELECT * FROM ParkingHistory", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
  });
});
app.get("/parking-history/search", (req, res) => {
  const plate = req.query.plate || "";
  const slot = req.query.slot || "";
  db.query(
    `SELECT ph.history_id, v.license_plate, s.slot_number, s.lot_id,
            ph.time_in, ph.time_out
            FROM ParkingHistory ph
            JOIN Vehicle v ON v.vehicle_id = ph.vehicle_id
            JOIN Slot s ON s.slot_id = ph.slot_id
            ORDER BY ph.time_in DESC`,
    (err, result) => {
      if (err) {
        return res.status(500).send(err);
      }
      res.json(
        result.filter(
          (item) =>
            item.license_plate.toLowerCase().includes(plate.toLowerCase()) &&
            item.slot_number.toLowerCase().includes(slot.toLowerCase())
        )
      );
    }
  );
});

app.listen(8080, () => console.log("Server running on port 8080"));
