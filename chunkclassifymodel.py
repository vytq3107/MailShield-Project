from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from transformers import pipeline, BertTokenizer

app = Flask(__name__)
CORS(app)  # Thêm CORS cho toàn bộ app

# Khởi tạo pipeline phân loại văn bản
pipe = pipeline("text-classification", model="Nhieu123/final_model_continued")
tokenizer = BertTokenizer.from_pretrained("Nhieu123/final_model_continued")  # Khởi tạo tokenizer BERT

# Hàm chia văn bản thành các chunk
def chunk_text(text):
    # Tách văn bản thành các từ
    words = text.split()
    chunks = []
    current_chunk = []
    current_chunk_length = 0

    for word in words:
        # Token hóa từ và thêm vào chunk hiện tại
        encoded_word = tokenizer.encode(word, add_special_tokens=False)
        current_chunk_length += len(encoded_word)

        # Kiểm tra nếu tổng số token vượt quá 512
        if current_chunk_length > 512:
            # Cắt đoạn trước từ này và tìm dấu câu gần cuối nhất trong chunk
            chunk_text = " ".join(current_chunk)
            last_punctuation = max(chunk_text.rfind(punc) for punc in ['.', ',', '!', '?', ';', ':', ')', '}', ']', '"'])
            
            if last_punctuation != -1:
                # Cắt tại vị trí dấu câu gần cuối
                chunk_text = chunk_text[:last_punctuation + 1]
            
            # Đảm bảo rằng không vượt quá 512 token
            encoded_chunk = tokenizer.encode(chunk_text, add_special_tokens=True)
            if len(encoded_chunk) > 512:
                chunk_text = " ".join(chunk_text.split()[:-1])  # Loại bỏ từ cuối cùng nếu token vẫn vượt quá

            chunks.append(chunk_text.strip())  # Thêm chunk vào danh sách
            current_chunk = [word]  # Bắt đầu chunk mới với từ hiện tại
            current_chunk_length = len(tokenizer.encode(word, add_special_tokens=False))  # Cập nhật độ dài chunk mới

        else:
            current_chunk.append(word)  # Thêm từ vào chunk hiện tại

    # Nếu còn từ trong chunk hiện tại, thêm vào danh sách chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        encoded_chunk = tokenizer.encode(chunk_text, add_special_tokens=True)
        # Đảm bảo không vượt quá 512 token
        if len(encoded_chunk) <= 512:
            chunks.append(chunk_text)

    return chunks


@app.route('/classify', methods=['POST'])
def predict():
    try:
        # Xử lý dữ liệu JSON đầu vào
        data = json.loads(request.data.decode("utf-8"))
        text = data.get("email_text", "")
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 400

    # Kiểm tra input
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Thực hiện chunking
    chunks = chunk_text(text)

    # Biến lưu trữ số lượng chunk "phishing", "safe" và điểm số
    phishing_count = 0
    safe_count = 0
    phishing_scores = []
    safe_scores = []

    # Phân loại từng chunk và đếm số lượng "phishing" và "safe"
    for chunk in chunks:
        result = pipe(chunk)

        for res in result:
            if res['label'] == 'Phishing Email':
                phishing_count += 1
                phishing_scores.append(res['score'])  # Lưu điểm "phishing"
            else:
                safe_count += 1
                safe_scores.append(res['score'])  # Lưu điểm "safe"

    # Kiểm tra số lượng chunk "phishing" và "safe"
    if phishing_count > safe_count:
        # Nếu số lượng chunk "phishing" nhiều hơn "safe", trả về trung bình điểm "phishing"
        avg_phishing_score = sum(phishing_scores) / len(phishing_scores)
        return jsonify([{"label": "phishing", "score": avg_phishing_score}])
    elif safe_count > phishing_count:
        # Nếu số lượng chunk "safe" nhiều hơn "phishing", trả về trung bình điểm "safe"
        avg_safe_score = sum(safe_scores) / len(safe_scores)
        return jsonify([{"label": "safe", "score": avg_safe_score}])
    else:
        # Nếu số lượng chunk "phishing" và "safe" bằng nhau, có thể trả về trung bình điểm của cả hai
        avg_phishing_score = sum(phishing_scores) / len(phishing_scores) if phishing_scores else 0
        avg_safe_score = sum(safe_scores) / len(safe_scores) if safe_scores else 0

        # Quyết định kết quả cuối cùng dựa trên điểm
        if avg_phishing_score > avg_safe_score:
            return jsonify([{"label": "phishing", "score": avg_phishing_score}])
        else:
            return jsonify([{"label": "safe", "score": avg_safe_score}])

# Chạy server lắng nghe từ mọi IP
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
