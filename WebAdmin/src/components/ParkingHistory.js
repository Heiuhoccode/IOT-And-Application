import React,{useEffect, useState} from "react";
import "./ParkingHistory.css";
function formatUTC(raw) {
    if (!raw) return null;
    const d = new Date(raw);
    const pad = n => n.toString().padStart(2, "0");
    
    return `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} `+ 
    `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` ;
  }
const ParkingHistory = ({ data }) => {
  const [history, setHistory] = useState([]);
  const [search,setSearch] = useState("");
  const [action,setAction] = useState(1);
  useEffect(()=>{
    const fetchData = async () => {
      try {
        const response = await fetch("http://localhost:8080/parking-history/search?plate=");
        const result = await response.json();
        setHistory(result);
      }
      catch(error){
        console.log(error);
      }

    }
    fetchData();
  },[data]);
  
  const handleSearch = async () => {
    try{
      const response = await fetch("http://localhost:8080/parking-history/search?plate="+search);
      const result = await response.json();
      setHistory(result);
    }
    catch (error){
      console.log(error);
    }
  }
  const sortAction = () => {
    if (action === 1) setAction(-1);
    else setAction(1);
    const result = [...history];
    result.sort((a,b) => {
      const x = a.time_out === null ? "In" : "Out";
      const y = b.time_out === null ? "In" : "Out";
      if (x>y) return action;
      if (x<y) return -action;
      if (a.time_in<b.time_in) return 1;
      return -1;
    });
    setHistory(result);
  }
  const sortTime = () => {
    if (action === 1) setAction(-1);
    else setAction(1);
    const result = [...history];
    result.sort((a,b) => {
      if (a.time_in>b.time_in) return action;
      return -action;
    });
    setHistory(result);
  }
  return (
    <div className="panel">
      <h2>📋 Parking History</h2>

      {/* Khung cuộn */}
      <div className="search-box">
          <input type="text" onChange={(e) => setSearch(e.target.value)} />
          <button onClick={handleSearch}>Search</button>
        </div>
      <div className="history-scroll">
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              <th>License Plate</th>
              <th><button className="th-btn" onClick={sortAction}>Action</button></th>
              <th><button className="th-btn" onClick={sortTime}>Time In</button></th>
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
