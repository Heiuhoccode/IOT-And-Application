import "./DashboardHeader.css";
const DashboardHeader = ({data}) => {
  const slotNumber = () => {
    return Object.values(data.status).filter(s => s === "available").length;
  };

  return (
    <div className="header-container">
      <div className="header-left">
        <h1 className="parking-title">🏢 {data.tenBai || "Parking Lot"}</h1>
        <p className="parking-location">📍 {data.diaChi}</p>
      </div>

      <div className="header-right grid">
        <div className="info-item">🌡 <b>Nhiệt độ:</b> {data.nhietDo}°C</div>
        <div className="info-item">💧 <b>Độ ẩm:</b> {data.doAm}%</div>
        <div className="info-item">🚘 <b>Tổng chỗ:</b> {data.tongSlot}</div>
        <div className="info-item">🚘 <b>Số chỗ còn trống:</b>{slotNumber(data.status)} </div>
      </div>
    </div>
  );
};

export default DashboardHeader;
