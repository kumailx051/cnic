# Azure App Service Configuration
import os
from app import app

# This is required for Azure App Service
if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
