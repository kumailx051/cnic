from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model
MODEL_PATH = "cnic_model.h5"
try:
    model = load_model(MODEL_PATH)
    logger.info("✅ Model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None

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
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        # Check if file is in request
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({"error": "No selected file"}), 400

        if not file or not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({"error": "Invalid file type. Use PNG, JPG, or JPEG"}), 400

        # Process the file
        filename = secure_filename(file.filename)
        file_path = os.path.join("uploads", filename)

        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        
        # Save uploaded file temporarily
        file.save(file_path)
        logger.info(f"File saved: {filename}")

        try:
            # Preprocess image
            img = image.load_img(file_path, target_size=(IMG_SIZE, IMG_SIZE))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0

            # Predict
            prediction = model.predict(img_array)[0][0]
            
            # Match the logic from your Kaggle test:
            # prediction > 0.5 = "not_cnic", prediction <= 0.5 = "cnic"
            if prediction > 0.5:
                label = "not_cnic"
                confidence = prediction  # Higher score means more confident it's not_cnic
            else:
                label = "cnic"
                confidence = 1 - prediction  # Lower score means more confident it's cnic

            logger.info(f"Prediction for {filename}: {label} (raw_score: {prediction:.4f}, confidence: {confidence:.4f})")

            # Delete file after prediction
            if os.path.exists(file_path):
                os.remove(file_path)

            return jsonify({
                "prediction_score": float(prediction),
                "predicted_label": label,
                "confidence": float(confidence),
                "raw_score": float(prediction)  # For debugging
            })

        except Exception as e:
            # Clean up file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Error processing image: {e}")
            return jsonify({"error": f"Error processing image: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "model_loaded": model is not None,
        "api_version": "1.0"
    }
    return jsonify(status)

if __name__ == "__main__":
    print("🚀 Starting CNIC Classifier Server...")
    print(f"📁 Model path: {MODEL_PATH}")
    print(f"🖼️  Image size: {IMG_SIZE}x{IMG_SIZE}")
    print(f"📋 Allowed extensions: {ALLOWED_EXTENSIONS}")
    
    if model is None:
        print("❌ WARNING: Model not loaded! Place 'cnic_model.h5' in the same directory.")
    else:
        print("✅ Model loaded successfully!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
