import React, { useEffect, useState } from "react";

const ParkingLot = ({ slots }) => {
  const [plates, setPlates] = useState({});

  const fetchPlate = async (slot) => {
    try {
      const response = await fetch(
        "API_SEARCH_HISTORY_BY_SLOT" + slot[1]
      );
      const data = await response.json();

      setPlates(prev => ({
        ...prev,
        [slot]: data[0]?.license_plate || "Unknown",
      }));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    Object.entries(slots).forEach(([slot, status]) => {
      if (status === "occupied") {
        fetchPlate(slot);
      }
    });
  }, [slots]);

  return (
    <div className="panel">
      <h2>🚗 Parking Lot Status</h2>
      <div className="grid">
        {Object.entries(slots).map(([slot, status]) => (
          <div
            key={slot}
            className={`slot ${status === "occupied" ? "occupied" : "available"}`}
          >
            <h3>{slot}</h3>

            <p>
              {status === "occupied"
                ? `🔴 Occupied (${plates[slot] || "..."})`
                : "🟢 Available"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ParkingLot;
