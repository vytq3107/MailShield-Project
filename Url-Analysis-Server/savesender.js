const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors"); // Thêm module CORS

const app = express();
app.use(bodyParser.json());
app.use(cors()); // Kích hoạt CORS cho mọi nguồn

// Lắng nghe dữ liệu từ client
app.post("/savesender", (req, res) => {
  const { email, analysis } = req.body;
  if (!email || !analysis) {
    return res.status(400).send("Missing email or analysis result");
  }

  console.log(`Received sender email: ${email}, Analysis: ${analysis}`);

  // Lưu dữ liệu vào file hoặc database (nếu cần)
  const fs = require("fs");
  const logData = `Email: ${email}, Analysis: ${analysis}\n`;
  fs.appendFileSync("senderblacklist.txt", logData, "utf8");

  res.status(200).send("Sender saved successfully");
});

// Thay đổi để server lắng nghe trên tất cả IP
const PORT = 5678;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server is running on port ${PORT}`);
});
