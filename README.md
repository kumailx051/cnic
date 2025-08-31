# 🛡️ CNIC Detection API

A machine learning API built with Flask and TensorFlow to detect whether an uploaded image is a Pakistani CNIC (National Identity Card) or not.

## 🚀 Features

- **Image Classification**: Detects CNIC vs Non-CNIC images
- **Multiple Input Formats**: Supports file upload and base64 encoded images
- **Azure-Ready**: Optimized for Azure App Service deployment
- **Production-Grade**: Includes logging, error handling, and monitoring
- **Cross-Platform**: Docker support for containerized deployment

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **ML Framework**: TensorFlow/Keras
- **Image Processing**: PIL (Pillow)
- **Deployment**: Azure App Service
- **Server**: Gunicorn (Production)

## 📋 API Endpoints

### Base URL
```
https://your-app-name.azurewebsites.net
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Health check and model status |
| POST | `/predict` | Upload image file for prediction |
| POST | `/predict_base64` | Send base64 encoded image for prediction |

## 📝 API Usage

### 1. File Upload Prediction
```bash
curl -X POST \
  https://your-app-name.azurewebsites.net/predict \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@path/to/your/image.jpg'
```

### 2. Base64 Prediction
```bash
curl -X POST \
  https://your-app-name.azurewebsites.net/predict_base64 \
  -H 'Content-Type: application/json' \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
  }'
```

### Response Format
```json
{
  "success": true,
  "prediction": {
    "is_cnic": true,
    "label": "CNIC",
    "confidence": 95.67,
    "raw_score": 0.0433
  },
  "timestamp": "2025-08-31T12:34:56.789Z"
}
```

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone https://github.com/kumailx051/cnic.git
cd cnic
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## ☁️ Azure Deployment

### Quick Deploy to Azure App Service

1. **Create Azure Resources**:
```bash
az group create --name cnic-api-rg --location "East US"
az appservice plan create --name cnic-api-plan --resource-group cnic-api-rg --sku B1 --is-linux
az webapp create --resource-group cnic-api-rg --plan cnic-api-plan --name cnic-api-app --runtime "PYTHON|3.11"
```

2. **Configure App Settings**:
```bash
az webapp config appsettings set \
    --resource-group cnic-api-rg \
    --name cnic-api-app \
    --settings FLASK_ENV=production SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000
```

3. **Deploy from Git**:
```bash
az webapp deployment source config \
    --name cnic-api-app \
    --resource-group cnic-api-rg \
    --repo-url https://github.com/kumailx051/cnic.git \
    --branch main \
    --manual-integration
```

For detailed deployment instructions, see [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

## 📊 Model Information

- **Model Type**: Convolutional Neural Network (CNN)
- **Input Size**: 224x224 RGB images
- **Framework**: TensorFlow/Keras
- **Model File**: `cnic_model.h5`

## 🔒 Security Features

- File type validation
- File size limits (16MB)
- Input sanitization
- Error handling without exposing internals

## 📈 Monitoring

### Health Check
```bash
curl https://your-app-name.azurewebsites.net/health
```

### Logs
- Azure App Service logs available in Azure Portal
- Application logs include timestamps and request details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Kumail Raza**
- GitHub: [@kumailx051](https://github.com/kumailx051)

## 🆘 Support

For support and questions:
1. Check the [Azure Deployment Guide](AZURE_DEPLOYMENT.md)
2. Open an issue on GitHub
3. Check Azure App Service logs for debugging

---

**⭐ If this project helped you, please give it a star!**
