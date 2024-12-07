const fs = require('fs');
const path = require('path');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// Đọc dữ liệu từ file JSON
function loadJsonFile(fileName) {
  try {
    const data = fs.readFileSync(path.join(__dirname, fileName), 'utf8');
    return JSON.parse(data);
  } catch (err) {
    console.error(`Lỗi khi đọc ${fileName}:`, err);
    return [];
  }
}

// Lấy blacklist và OpenRedirectKey
const blacklist = loadJsonFile('blacklist.json');
const redirectKeys = loadJsonFile('OpenRedirectKey.json');

// Hàm để lấy phần chính của hostname
function getMainDomain(hostname) {
  const parts = hostname.split('.');
  return parts.length > 2 ? parts.slice(-2).join('.') : hostname;
}

// Giải mã ký tự đặc biệt trong URL
function decodeUrlEncodedChars(url) {
  return url.replace(/%3C/gi, '<')
            .replace(/%3E/gi, '>')
            .replace(/%22/gi, '"')
            .replace(/%27/gi, "'")
            .replace(/%2F/gi, '/');
}

// Kiểm tra XSS trong URL
function containsXSS(url) {
  const decodedUrl = decodeUrlEncodedChars(url);

  const dangerousPatternsInURL = [
    /<\s*(script|style|title|textarea|noscript|noembed|template|html|svg|p)\b[^>]*>/gi,
    /<\/\s*(script|style|title|textarea|noscript|template|noembed|html|p)[^>]*>/gi,
    /javascript\s*:/gi,
    /(?:alert|confirm|prompt|document\.location)\s*\(/gi,
    /\bon(?:click|load|mouseover)\s*=\s*["']?[^"'>]+["']?/gi,
    /%3Ca\s+href=["']?https?:\/\/[^"'>]+["']?.*%3E/gi,
    /<\s*\/?[a-zA-Z0-9]+[^>]*>.*<\/?\w+>/gi
  ];

  return dangerousPatternsInURL.some(pattern => pattern.test(decodedUrl));
}

// Hàm xử lý URL
function processUrl(statusCode, responseUrl, redirectLocation) {
  console.log(`Processing URL: ${responseUrl}`);

  if (statusCode === 200) {
    try {
      const url = new URL(responseUrl);
      const params = url.searchParams;
      for (let key of redirectKeys) {
        if (params.has(key)) {
          return 'mark_redirect';
        }
      }
      return 'safe';
    } catch (error) {
      console.error('Lỗi khi parse URL:', error);
      return 'error';
    }
  }

  if ((statusCode === 301 || statusCode === 302 || statusCode === 303) && redirectLocation) {
    let responseHostname, locationHostname;
    try {
      responseHostname = getMainDomain(new URL(responseUrl).hostname);
      locationHostname = getMainDomain(new URL(redirectLocation).hostname);
    } catch (error) {
      console.error('Lỗi khi parse URL:', error);
      return 'error';
    }

    if (responseHostname !== locationHostname) {
      if (blacklist.includes(locationHostname)) {
        return 'malicious2';
      } else {
        // Kiểm tra XSS trong redirect location
        return containsXSS(redirectLocation) ? 'XSS2' : 'mark_redirect';
      }
    } else {
      return 'safe';
    }
  }

  if (statusCode === 403) {
    return 'safe';
  }

  return 'No redirect or location';
}

module.exports = {
  processUrl,
};
