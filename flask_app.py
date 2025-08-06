#!/usr/bin/env python3
"""
Azure-compatible Flask app entry point
This file loads the Flask application from app.py
"""

# Import the Flask app instance from app.py
from app import app

# This is what Azure will call
if __name__ == '__main__':
    # Get port from environment variable for Azure deployment
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🌐 Starting Flask app on port {port}")
    print("📱 API ready for requests")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
