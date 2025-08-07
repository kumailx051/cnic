from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Load model
MODEL_PATH = "cnic_model.h5"
model = load_model(MODEL_PATH)

# Image size used during training
IMG_SIZE = 224

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return "✅ CNIC Classifier API is up and running!"

@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join("uploads", filename)

        # Save uploaded file temporarily
        os.makedirs("uploads", exist_ok=True)
        file.save(file_path)

        # Preprocess image
        img = image.load_img(file_path, target_size=(IMG_SIZE, IMG_SIZE))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0

        # Predict
        prediction = model.predict(img_array)[0][0]
        label = "not_cnic" if prediction > 0.5 else "cnic"

        # Delete file after prediction
        os.remove(file_path)

        return jsonify({
            "prediction_score": float(prediction),
            "predicted_label": label
        })

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    app.run(debug=True)
