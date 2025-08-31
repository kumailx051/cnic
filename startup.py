#!/usr/bin/env python3
"""
Startup script for Azure App Service
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
