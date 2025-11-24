// import "./Camera.css";

// export default function Camera() {
//   return (
//     <div className="camera-container">
//       <h2 className="camera-title">Hệ thống Camera Giám Sát</h2>

//       <div className="camera-grid">

//         {/* CAM 1 – Slot */}
//         <div className="camera-box">
//           <div className="cam-label">Camera Slot</div>
//           <div className="camera-frame">
//             <iframe
//               src="http://127.0.0.1:5000/video_slot"
//               title="Camera Slot"
//               frameBorder="0"
//             ></iframe>
//           </div>
//         </div>

//         {/* CAM 2 – Entry IN */}
//         <div className="camera-box">
//           <div className="cam-label">Camera Entry - IN</div>
//           <div className="camera-frame">
//             <iframe
//               src="http://127.0.0.1:5000/video_entry_in"
//               title="Camera In"
//               frameBorder="0"
//             ></iframe>
//           </div>
//         </div>

//         {/* CAM 3 – Entry OUT */}
//         <div className="camera-box">
//           <div className="cam-label">Camera Entry - OUT</div>
//           <div className="camera-frame">
//             <iframe
//               src="http://127.0.0.1:5000/video_entry_out"
//               title="Camera Out"
//               frameBorder="0"
//             ></iframe>
//           </div>
//         </div>

//       </div>
//     </div>
//   );
// }

export default function CameraView() {
  const base = "http://127.0.0.1:5000";

  return (
    <div style={styles.container}>
      <h1 style={styles.pageTitle}>🎥 Camera Dashboard</h1>

      <div style={styles.grid}>
        {/* Slot camera */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Slot Camera</h3>
          <img
            src={`${base}/video_slot`}
            style={styles.camera}
            alt="slot"
          />
        </div>

        {/* Entry IN */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Entry IN Camera</h3>
          <img
            src={`${base}/video_entry_in`}
            style={styles.camera}
            alt="entry-in"
          />
        </div>

        {/* Entry OUT */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Entry OUT Camera</h3>
          <img
            src={`${base}/video_entry_out`}
            style={styles.camera}
            alt="entry-out"
          />
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: "30px",
    background: "#f5f7fa",
    minHeight: "100vh",
  },

  pageTitle: {
    textAlign: "center",
    fontSize: "32px",
    fontWeight: "700",
    marginBottom: "30px",
    color: "#222",
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))",
    gap: "24px",
  },

  card: {
    background: "#fff",
    padding: "15px",
    borderRadius: "12px",
    boxShadow: "0px 4px 10px rgba(0,0,0,0.08)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },

  cardTitle: {
    fontSize: "20px",
    fontWeight: "600",
    marginBottom: "10px",
  },

  camera: {
    width: "100%",
    height: "260px",
    objectFit: "cover",
    background: "#ddd",
    borderRadius: "10px",
  },
};
