const express = require("express");
const db = require("./db");
const cors = require("cors");
require("./mqttHandler");
const app = express();
app.use(cors());
app.use(express.json());

//Camera
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

//ParkingLot
app.get("/parking-lot", (req, res) => {
  db.query("SELECT * FROM ParkingLot", (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.json(result);
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

// ParkingHistory_by_Plate
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
