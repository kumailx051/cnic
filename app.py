from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import io
import base64
from PIL import Image
import os
import logging
from datetime import datetime

# Configure logging for Azure
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["*"])  # Configure CORS for production

# Azure App Service configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global model variable
model = None

def load_ml_model():
    """Load the ML model with error handling"""
    global model
    try:
        model_path = os.path.join(os.path.dirname(__file__), "cnic_model.h5")
        if not os.path.exists(model_path):
            # Try alternative path for Azure deployment
            model_path = "cnic_model.h5"
        
        logger.info(f"Loading model from: {model_path}")
        model = load_model(model_path)
        logger.info("Model loaded successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False

# Load model on startup
model_loaded = load_ml_model()

def preprocess_image(img):
    """Preprocess image for prediction"""
    try:
        # Resize image to match model input
        img = img.resize((224, 224))
        # Convert to array
        img_array = image.img_to_array(img)
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        # Normalize pixel values
        img_array = img_array / 255.0
        return img_array
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        raise

@app.route('/')
def home():
    return jsonify({
        "message": "CNIC Model API is running on Azure!",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": model is not None,
        "endpoints": {
            "/predict": "POST - Upload image for CNIC prediction",
            "/predict_base64": "POST - Base64 image for CNIC prediction", 
            "/health": "GET - Check API health"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "timestamp": datetime.utcnow().isoformat(),
        "memory_usage": "Available" if model is not None else "Model not loaded"
    })

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({
            "success": False,
            "error": "Model not loaded. Please check server logs."
        }), 503
    
    try:
        # Check if image is provided
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No image selected"}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False, 
                "error": f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            }), 400
        
        # Read and preprocess the image
        img = Image.open(file.stream)
        
        # Convert to RGB if needed (in case of RGBA or other formats)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Preprocess image
        img_array = preprocess_image(img)
        
        # Make prediction
        prediction = model.predict(img_array, verbose=0)[0][0]
        
        # Determine result - convert numpy types to Python types
        is_cnic = bool(prediction <= 0.5)
        confidence = float(1 - prediction) if is_cnic else float(prediction)
        
        logger.info(f"Prediction made: {is_cnic}, confidence: {confidence:.2f}")
        
        return jsonify({
            "success": True,
            "prediction": {
                "is_cnic": is_cnic,
                "label": "CNIC" if is_cnic else "NOT_CNIC",
                "confidence": round(confidence * 100, 2),
                "raw_score": float(prediction)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error during prediction"
        }), 500

@app.route('/predict_base64', methods=['POST'])
def predict_base64():
    """Alternative endpoint for base64 encoded images"""
    if model is None:
        return jsonify({
            "success": False,
            "error": "Model not loaded. Please check server logs."
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({"success": False, "error": "No image data provided"}), 400
        
        # Decode base64 image
        image_data = data['image']
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": "Invalid base64 image data"
            }), 400
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Preprocess image
        img_array = preprocess_image(img)
        
        # Make prediction
        prediction = model.predict(img_array, verbose=0)[0][0]
        
        # Determine result - convert numpy types to Python types
        is_cnic = bool(prediction <= 0.5)
        confidence = float(1 - prediction) if is_cnic else float(prediction)
        
        logger.info(f"Base64 prediction made: {is_cnic}, confidence: {confidence:.2f}")
        
        return jsonify({
            "success": True,
            "prediction": {
                "is_cnic": is_cnic,
                "label": "CNIC" if is_cnic else "NOT_CNIC",
                "confidence": round(confidence * 100, 2),
                "raw_score": float(prediction)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Base64 prediction error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error during prediction"
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "success": False,
        "error": "File too large. Maximum size is 16MB."
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    # Local development settings
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info("Starting CNIC Prediction API...")
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info("Endpoints:")
    logger.info("  GET  /          - API info")
    logger.info("  GET  /health    - Health check")
    logger.info("  POST /predict   - Image file prediction")
    logger.info("  POST /predict_base64 - Base64 image prediction")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
