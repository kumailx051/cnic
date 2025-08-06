from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow Flutter app access

# Global variables for model and vectorizer
model = None
vectorizer = None

def load_models():
    """Load the trained model and vectorizer with enhanced error handling"""
    global model, vectorizer
    
    try:
        # Get current working directory for debugging
        current_dir = os.getcwd()
        print(f"🔍 Current working directory: {current_dir}")
        
        # List files in current directory
        files = os.listdir('.')
        print(f"📁 Files in current directory: {files}")
        
        # Check if model files exist
        model_file = 'spam_model.pkl'
        vectorizer_file = 'vectorizer.pkl'
        
        if not os.path.exists(model_file):
            print(f"❌ {model_file} not found in {current_dir}")
            return False
            
        if not os.path.exists(vectorizer_file):
            print(f"❌ {vectorizer_file} not found in {current_dir}")
            return False
        
        print(f"✅ Both model files found")
        
        # Load the spam detection model
        print(f"🤖 Loading {model_file}...")
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ Model loaded successfully! Type: {type(model)}")
        
        # Load the TF-IDF vectorizer
        print(f"🔤 Loading {vectorizer_file}...")
        with open(vectorizer_file, 'rb') as f:
            vectorizer = pickle.load(f)
        print(f"✅ Vectorizer loaded successfully! Type: {type(vectorizer)}")
        
        # Test a quick prediction to ensure everything works
        test_text = "test message"
        processed_text = preprocess_text(test_text)
        features = vectorizer.transform([processed_text])
        test_prediction = model.predict(features)[0]
        print(f"🧪 Model test successful - prediction: {test_prediction}")
        
        print("✅ All models loaded and tested successfully!")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ File not found error: {e}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Directory contents: {os.listdir('.')}")
        return False
    except ImportError as e:
        print(f"❌ Import error (missing dependencies): {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error loading models: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def preprocess_text(text):
    """Enhanced text preprocessing for spam detection (same as training)"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Keep URLs as features (important for spam detection)
    text = re.sub(r'http[s]?://\S+', 'URL_TOKEN', text)
    text = re.sub(r'www\.\S+', 'URL_TOKEN', text)
    
    # Keep phone numbers as features (important for spam detection)
    text = re.sub(r'\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', 'PHONE_TOKEN', text)
    text = re.sub(r'\b\d{10,11}\b', 'PHONE_TOKEN', text)
    
    # Keep email patterns
    text = re.sub(r'\S+@\S+', 'EMAIL_TOKEN', text)
    
    # Keep money/currency patterns (important for spam)
    text = re.sub(r'\$\d+', 'MONEY_TOKEN', text)
    text = re.sub(r'\b\d+\s?(dollar|pound|euro|rupee)s?\b', 'MONEY_TOKEN', text)
    
    # Keep numbers as potential features
    text = re.sub(r'\b\d+\b', 'NUMBER_TOKEN', text)
    
    # Strip and return
    return text.strip()

def predict_spam(message):
    """Predict if a message is spam"""
    if model is None or vectorizer is None:
        raise ValueError("Models not loaded")
    
    # Preprocess and vectorize
    processed = preprocess_text(message)
    features = vectorizer.transform([processed])
    
    # Get prediction and probability
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0]
    
    return {
        'is_spam': bool(prediction),
        'spam_probability': round(float(probability[1]), 4),
        'ham_probability': round(float(probability[0]), 4),
        'confidence': round(float(max(probability)), 4),
        'confidence_percentage': round(float(max(probability)) * 100, 2),
        'processed_text': processed,
        'timestamp': datetime.now().isoformat()
    }

@app.route('/', methods=['GET'])
def home():
    """API information endpoint"""
    return jsonify({
        'success': True,
        'message': 'Spam Detection API is running!',
        'version': '1.0.0',
        'endpoints': {
            'predict': {
                'url': '/api/predict',
                'method': 'POST',
                'description': 'Analyze single message for spam'
            },
            'batch_predict': {
                'url': '/api/batch-predict',
                'method': 'POST',
                'description': 'Analyze multiple messages for spam'
            },
            'health': {
                'url': '/api/health',
                'method': 'GET',
                'description': 'Check API health status'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Single message spam prediction endpoint for Flutter"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'MISSING_DATA'
            }), 400
        
        if 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'No message field provided',
                'code': 'MISSING_MESSAGE'
            }), 400
        
        message = data['message']
        
        if not message or not message.strip():
            return jsonify({
                'success': False,
                'error': 'Empty message provided',
                'code': 'EMPTY_MESSAGE'
            }), 400
        
        if len(message) > 1000:
            return jsonify({
                'success': False,
                'error': 'Message too long (max 1000 characters)',
                'code': 'MESSAGE_TOO_LONG'
            }), 400
        
        # Make prediction
        result = predict_spam(message)
        
        # Format response for Flutter
        response = {
            'success': True,
            'data': {
                'original_message': message,
                'is_spam': result['is_spam'],
                'spam_probability': result['spam_probability'],
                'ham_probability': result['ham_probability'],
                'confidence': result['confidence'],
                'confidence_percentage': result['confidence_percentage'],
                'classification': 'SPAM' if result['is_spam'] else 'HAM',
                'risk_level': get_risk_level(result['spam_probability']),
                'processed_text': result['processed_text'],
                'timestamp': result['timestamp']
            },
            'message': 'Message analyzed successfully'
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'PREDICTION_ERROR'
        }), 500

def get_risk_level(spam_probability):
    """Get risk level based on spam probability"""
    if spam_probability >= 0.8:
        return 'HIGH'
    elif spam_probability >= 0.5:
        return 'MEDIUM'
    elif spam_probability >= 0.3:
        return 'LOW'
    else:
        return 'VERY_LOW'

@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """Batch message spam prediction endpoint for Flutter"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'MISSING_DATA'
            }), 400
        
        if 'messages' not in data:
            return jsonify({
                'success': False,
                'error': 'No messages field provided',
                'code': 'MISSING_MESSAGES'
            }), 400
        
        messages = data['messages']
        
        if not isinstance(messages, list):
            return jsonify({
                'success': False,
                'error': 'Messages must be a list',
                'code': 'INVALID_FORMAT'
            }), 400
        
        if len(messages) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty messages list provided',
                'code': 'EMPTY_LIST'
            }), 400
        
        if len(messages) > 50:
            return jsonify({
                'success': False,
                'error': 'Too many messages (max 50)',
                'code': 'TOO_MANY_MESSAGES'
            }), 400
        
        # Make predictions for all messages
        predictions = []
        for i, message in enumerate(messages):
            try:
                if not message or not message.strip():
                    predictions.append({
                        'index': i,
                        'original_message': message,
                        'success': False,
                        'error': 'Empty message'
                    })
                    continue
                
                result = predict_spam(message)
                prediction = {
                    'index': i,
                    'success': True,
                    'data': {
                        'original_message': message,
                        'is_spam': result['is_spam'],
                        'spam_probability': result['spam_probability'],
                        'ham_probability': result['ham_probability'],
                        'confidence': result['confidence'],
                        'confidence_percentage': result['confidence_percentage'],
                        'classification': 'SPAM' if result['is_spam'] else 'HAM',
                        'risk_level': get_risk_level(result['spam_probability']),
                        'processed_text': result['processed_text'],
                        'timestamp': result['timestamp']
                    }
                }
                predictions.append(prediction)
                
            except Exception as e:
                predictions.append({
                    'index': i,
                    'original_message': message,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'data': {
                'total_messages': len(messages),
                'processed_count': len(predictions),
                'predictions': predictions
            },
            'message': f'Analyzed {len(predictions)} messages successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'BATCH_PREDICTION_ERROR'
        }), 500

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check server status and file system"""
    try:
        import sys
        debug_data = {
            'success': True,
            'data': {
                'python_version': sys.version,
                'current_directory': os.getcwd(),
                'directory_contents': os.listdir('.'),
                'model_loaded': model is not None,
                'vectorizer_loaded': vectorizer is not None,
                'model_type': str(type(model)) if model else None,
                'vectorizer_type': str(type(vectorizer)) if vectorizer else None,
                'environment': dict(os.environ),
                'sys_path': sys.path
            },
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(debug_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint with model status for Flutter"""
    model_status = 'loaded' if model is not None and vectorizer is not None else 'not loaded'
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'model_status': model_status,
            'server': 'Flask Spam Detection API',
            'version': '1.0.0',
            'endpoints_available': 3,
            'uptime': 'running',
            'timestamp': datetime.now().isoformat()
        },
        'message': 'API is healthy and ready to process requests'
    })

# Legacy endpoint for backward compatibility
@app.route('/health', methods=['GET'])
def health_legacy():
    """Legacy health check endpoint"""
    model_status = 'loaded' if model is not None and vectorizer is not None else 'not loaded'
    return jsonify({
        'status': 'healthy',
        'model_status': model_status,
        'server': 'Flask Spam Detection API'
    })

# Legacy predict endpoint for backward compatibility
@app.route('/predict', methods=['POST'])
def predict_legacy():
    """Legacy single message spam prediction endpoint"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'message' not in data:
            return jsonify({'error': 'No message field provided'}), 400
        
        message = data['message']
        
        if not message or not message.strip():
            return jsonify({'error': 'Empty message provided'}), 400
        
        # Make prediction
        result = predict_spam(message)
        
        # Add original message to response (legacy format)
        result['original_message'] = message
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND',
        'available_endpoints': {
            'predict': '/api/predict (POST)',
            'batch_predict': '/api/batch-predict (POST)',
            'health': '/api/health (GET)',
            'home': '/ (GET)'
        }
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    print("🚀 Starting Flutter-Ready Spam Detection API...")
    
    # Load models on startup
    if not load_models():
        print("❌ Failed to load models. Please ensure spam_model.pkl and vectorizer.pkl exist.")
        exit(1)
    
    # Get port from environment variable for Azure deployment
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🌐 Starting server on port {port}")
    print("� Flutter-Ready API Endpoints:")
    print("  GET  /                    - API information")
    print("  GET  /api/health          - Health check")
    print("  POST /api/predict         - Single message prediction")
    print("  POST /api/batch-predict   - Batch message prediction")
    print("\n� Legacy Endpoints (backward compatibility):")
    print("  GET  /health              - Legacy health check")
    print("  POST /predict             - Legacy single prediction")
    print("\n📱 Flutter HTTP Examples:")
    print(f"  POST http://localhost:{port}/api/predict")
    print("  Body: {\"message\": \"Your message here\"}")
    print("\n✅ CORS enabled for Flutter app access")
    
    # Run the Flask app with host 0.0.0.0 for external access
    app.run(host='0.0.0.0', port=port, debug=False)
