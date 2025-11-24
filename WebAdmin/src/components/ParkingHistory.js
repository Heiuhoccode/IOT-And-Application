import React,{useEffect, useState} from "react";
import "./ParkingHistory.css";

const ParkingHistory = ({ data }) => {
  const [history, setHistory] = useState([]);
  useEffect(()=>{
    const fetchData = async () => {
      const response = await fetch("https://z43k8t-8080.csb.app/parking-history/search?plate=");
      const result = await response.json();
      setHistory(result);
      console.log(result);

    }
    fetchData();
  },[data]);
  function formatUTC(raw) {
    if (!raw) return null;
    const d = new Date(raw);
    const pad = n => n.toString().padStart(2, "0");
    
    return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} `+ 
    `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` ;
}
  return (
    <div className="panel">
      <h2>📋 Parking History</h2>

      {/* Khung cuộn */}
      <div className="history-scroll">
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              <th>License Plate</th>
              <th>Action</th>
              <th>Time In</th>
              <th>Time Out</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, idx) => (
              <tr key={idx}>
                <td>{idx + 1}</td>
                <td>{item.license_plate}</td>
                <td>{item.time_out === null ? "🟩 In" : "🟥 Out"}</td>
                <td>{formatUTC(item.time_in)}</td>
                <td>{formatUTC(item.time_out)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ParkingHistory;
