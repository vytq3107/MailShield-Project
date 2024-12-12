from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from transformers import pipeline, BertTokenizer

app = Flask(__name__)
CORS(app)

# Initialize the text classification pipeline
try:
    pipe = pipeline("text-classification", model="Nhieu123/final_model_continued")
    tokenizer = BertTokenizer.from_pretrained("Nhieu123/final_model_continued")
except Exception as e:
    raise RuntimeError(f"Failed to load model or tokenizer: {str(e)}")

# Function to split text into chunks based on token limit
def chunk_text(text):
    words = text.split()
    chunks, current_chunk = [], []

    for word in words:
        current_chunk.append(word)
        if len(tokenizer.encode(" ".join(current_chunk), add_special_tokens=True)) > 512:
            current_chunk.pop()  # Remove last word to fit the token limit
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

@app.route('/classify', methods=['POST'])
def predict():
    try:
        # Parse input JSON
        data = request.get_json(force=True)
        text = data.get("email_text", "")
        if not text:
            return jsonify({"error": "No text provided"}), 400
    except Exception as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400

    # Split text into chunks and classify
    chunks = chunk_text(text)
    phishing_count, safe_count = 0, 0
    phishing_scores, safe_scores = [], []

    for chunk in chunks:
        results = pipe(chunk)
        for res in results:
            if res['label'] == 'Phishing Email':
                phishing_count += 1
                phishing_scores.append(res['score'])
            elif res['label'] == 'Safe Email':
                safe_count += 1
                safe_scores.append(res['score'])

    # Determine final classification
    if phishing_count > safe_count:
        avg_score = sum(phishing_scores) / len(phishing_scores)
        return jsonify({"label": "phishing", "score": avg_score})
    elif safe_count > phishing_count:
        avg_score = sum(safe_scores) / len(safe_scores)
        return jsonify({"label": "safe", "score": avg_score})
    else:
        avg_phishing = sum(phishing_scores) / len(phishing_scores) if phishing_scores else 0
        avg_safe = sum(safe_scores) / len(safe_scores) if safe_scores else 0
        label = "phishing" if avg_phishing > avg_safe else "safe"
        avg_score = max(avg_phishing, avg_safe)
        return jsonify({"label": label, "score": avg_score})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
