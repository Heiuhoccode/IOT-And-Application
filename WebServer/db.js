const mysql = require("mysql2");
const db = mysql.createConnection({
    host: "binzkjb5rditypwr6b8r-mysql.services.clever-cloud.com",
    user: "uziwfoaieje3u6sj",
    password: "hQN6EvKO4kAwg4s3sScS",
    database: "binzkjb5rditypwr6b8r",
    port: 3306,
});
  
  // Kiểm tra kết nối
db.connect((err) => {
    if (err) {
      console.error("❌ Lỗi kết nối MySQL:", err);
    } else {
      console.log("✅ Kết nối MySQL Clever Cloud thành công!");
    }
});
module.exports = db;