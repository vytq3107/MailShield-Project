

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const urlModule = require('url');
const app = express();
const { processUrl } = require('./processResponse'); // Import hàm xử lý từ file khác

app.use(cors());
app.use(express.json());

// Định nghĩa mức độ ưu tiên cho các trạng thái
const statusPriority = {
  malicious2: 4,
  XSS2: 3,
  mark_redirect: 2,
  suspicious: 1,
  safe: 0,
  "No redirect or location": 0
};

// Hàm để lấy trạng thái cao nhất từ danh sách trạng thái các URL
function getHighestStatus(urlResults) {
  return urlResults.reduce((highest, result) => {
    const status = result.processedResult;
    return statusPriority[status] > statusPriority[highest] ? status : highest;
  }, 'safe');
}

// Hàm gửi yêu cầu HEAD và xử lý redirect
function sendCurlLikeRequest(url) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const options = {
      method: 'HEAD',
      hostname: parsedUrl.hostname,
      path: parsedUrl.pathname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      headers: { 'User-Agent': 'Mozilla/5.0' }
    };

    const protocol = parsedUrl.protocol === 'https:' ? https : http;

    const req = protocol.request(options, (res) => {
      let locationHeader = res.headers.location;

      if (res.statusCode === 301 || res.statusCode === 302 || res.statusCode === 303) {
        if (locationHeader) {
          resolve({
            url,
            status: res.statusCode,
            location: locationHeader // Trích xuất location nếu có
          });
        } else {
          resolve({
            url,
            status: res.statusCode,
            location: 'No location header found' // Nếu không có location header
          });
        }
      } else if (res.statusCode === 200) {
        resolve({
          url,
          status: res.statusCode
        });
      } else {
        resolve({
          url,
          status: res.statusCode,
          headers: res.headers
        });
      }
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.end();
  });
}

// Hàm gửi các yêu cầu và xử lý từng URL
async function sendRequestsWithoutRedirect(urls) {
  const results = await Promise.all(
    urls.map(async (url) => {
      try {
        console.log(`Sending curl-like request to: ${url}`);
        const result = await sendCurlLikeRequest(url);
        const processedResult = processUrl(result.status, result.url, result.location);
        console.log(`Processed result for ${url}: ${processedResult}`);

        return { ...result, processedResult };
      } catch (error) {
        console.error(`Error sending request to ${url}:`, error.message);
        return { url, error: error.message, processedResult: 'error' };
      }
    })
  );

  return results;
}

app.post('/data', async (req, res) => {
  const { deliveryTo, messageId, urls } = req.body;

  if (!deliveryTo || !messageId || !urls) {
    return res.status(400).json({ message: 'Các trường deliveryTo, messageId, và urls là bắt buộc!' });
  }

  try {
    const urlResults = await sendRequestsWithoutRedirect(urls);
    const overallStatus = getHighestStatus(urlResults);

    res.json({
      messageId,
      // deliveryTo,
      overallStatus
      // results: urlResults
    });
  } catch (error) {
    console.error('Error while processing requests:', error);
    res.status(500).json({ message: 'Lỗi khi xử lý các request!' });
  }
});

app.listen(1234, '0.0.0.0', () => {
  console.log('Server đang chạy tại http://0.0.0.0:1234/');
});
