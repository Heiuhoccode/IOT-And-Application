const mysql = require("mysql2");
const db = mysql.createConnection({
    host: "YOUR_mysql.services.clever-cloud.com",
    user: "YOUR_USERNAME",
    password: "YOUR_PASSWORD",
    database: "YOUR_DATABASE",
    port: "YOUR_PORT",
});
  
// Testing connect
db.connect((err) => {
    if (err) {
      console.error("❌ Error connect MySQL:", err);
    } else {
      console.log("✅ Connected MySQL Clever Cloud successful!");
    }
});
module.exports = db;