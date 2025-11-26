import React, { useState, useEffect } from "react";
import DashboardHeader from "./components/DashboardHeader";
import ParkingLot from "./components/ParkingLot";
import ParkingHistory from "./components/ParkingHistory";
import "./components/Dashboard.css";
import Camera from "./components/Camera";
import mqtt from "mqtt";
function App() {
  const [data,setData] = useState({parkingLot: '', address: '', slot: 0, temperature: 0, humidity: 0,status:
  {s1: 'available', s2: 'available', s3: 'available', s4: 'available'}});
  const [entry,setEntry] = useState("");
  useEffect(() => {
    try{
      const broker = "YOUR_MQTT_HOST";
      const options = {
        username: "YOUR_USERNAME",
        password: "YOUR_PASSWORD",
        reconnectPeriod: 2000,
      };

      const mqttClient = mqtt.connect(broker, options);

      mqttClient.on("connect", () => {
        console.log("✅ Connected MQTT Broker!");
        mqttClient.subscribe(["Information","camera/entry"]);
      });

      mqttClient.on("message", (topic, message) => {
          try {
            const result = JSON.parse(message.toString());
            if (topic === "Information") {
              setData(result);
            }
            if (topic === "camera/entry") {
              console.log(result);
              setEntry(result);
            }
          } catch (err) {
            console.error("Error parse JSON:", err);
          }
        
      });

      mqttClient.on("error", (err) => console.error("❌ MQTT Error:", err));

      return () => mqttClient.end();
    }
    catch (error) {
      console.log(error);
    }
  }, []);

  return (
    <div className="dashboard">
      <div className="header-section">
        <DashboardHeader data={data}/>
      </div>

      <div className="content-section">
        <div className="left">
          <ParkingLot slots={data.status}/>
        </div>
        <div className="right">
          <ParkingHistory data={entry} />
        </div>
          
      </div>
      <Camera />
    </div>
  );
}

export default App;
