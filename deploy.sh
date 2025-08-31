#!/bin/bash

# Azure App Service deployment script for Python Flask app

echo "Starting deployment for CNIC Detection API..."

# Set up environment
export FLASK_APP=app.py
export FLASK_ENV=production

# Install dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Deployment completed successfully!"
echo "Application will start with: gunicorn --bind 0.0.0.0:\$PORT app:app"
