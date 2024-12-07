from flask import Flask, request, jsonify
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer, pipeline

# Khởi tạo Flask app
app = Flask(__name__)

# Load tokenizer và model
tokenizer = AutoTokenizer.from_pretrained("laiyer/codebert-base-Malicious_URLs-onnx")
model = ORTModelForSequenceClassification.from_pretrained("laiyer/codebert-base-Malicious_URLs-onnx")

# Tạo pipeline
classifier = pipeline(
    task="text-classification",
    model=model,
    tokenizer=tokenizer,
    top_k=None,
)

@app.route('/classify', methods=['POST'])
def classify():
    # Lấy dữ liệu đầu vào từ request
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request data"}), 400
    
    url = data['url']
    
    # Gọi pipeline để phân loại URL
    classifier_output = classifier(url)
    
    return jsonify(classifier_output)

if __name__ == '__main__':
    # Chạy server Flask
    app.run(host='0.0.0.0', port=5000)
