import "./DashboardHeader.css";
const DashboardHeader = ({data}) => {
  return (
    <div className="header-container">
      {/* Trái: tên bãi đỗ (to) */}
      <div className="header-left">
        <h1 className="parking-title">🏢 {data.tenBai || "Parking Lot"}</h1>
        <p className="parking-location">📍 {data.diaChi}</p>
      </div>

      {/* Phải: dùng GRID 3 cột x 2 hàng, căn phải từng ô */}
      <div className="header-right grid">
        {/* <div className="info-item">📷 <b>Camera:</b> {info.camera_status ? "✅ Online" : "❌ Offline"}</div> */}
        <div className="info-item">🌡 <b>Nhiệt độ:</b> {data.nhietDo}°C</div>
        <div className="info-item">💧 <b>Độ ẩm:</b> {data.doAm}%</div>
        <div className="info-item">🚘 <b>Tổng chỗ:</b> {data.tongSlot}</div>
        {/* <div className="info-item">🟩 <b>Chỗ trống:</b> {info.available_slots}</div> */}
        <div className="info-item"></div>{/* ô trống để cân layout */}
      </div>
    </div>
  );
};

export default DashboardHeader;
