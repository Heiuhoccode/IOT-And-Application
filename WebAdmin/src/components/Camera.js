import "./Camera.css";

export default function CameraView() {
  const base = "http://10.180.225.210:5000";

  return (
    <div className="container">
      <h1 className="pageTitle">🎥 Camera Dashboard</h1>

      <div className="grid">
        <div className="card">
          <h3 className="cardTitle">Slot Camera</h3>
          <img src={`${base}/video_slot`} className="camera" alt="slot" />
        </div>

        <div className="card">
          <h3 className="cardTitle">Entry IN Camera</h3>
          <img src={`${base}/video_entry_in`} className="camera" alt="entry-in" />
        </div>

        <div className="card">
          <h3 className="cardTitle">Entry OUT Camera</h3>
          <img src={`${base}/video_entry_out`} className="camera" alt="entry-out" />
        </div>
      </div>
    </div>
  );
}
