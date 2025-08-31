# CNIC Model API - Azure Deployment Guide

## 🚀 Azure Deployment Instructions

### Prerequisites
1. Azure subscription
2. Azure CLI installed
3. Git repository (optional but recommended)

### Method 1: Azure App Service (Recommended)

#### Step 1: Create Resource Group
```bash
az group create --name cnic-api-rg --location "East US"
```

#### Step 2: Create App Service Plan
```bash
az appservice plan create \
    --name cnic-api-plan \
    --resource-group cnic-api-rg \
    --sku B1 \
    --is-linux
```

#### Step 3: Create Web App
```bash
az webapp create \
    --resource-group cnic-api-rg \
    --plan cnic-api-plan \
    --name cnic-api-app \
    --runtime "PYTHON|3.11"
```

#### Step 4: Configure App Settings
```bash
az webapp config appsettings set \
    --resource-group cnic-api-rg \
    --name cnic-api-app \
    --settings FLASK_ENV=production \
               SCM_DO_BUILD_DURING_DEPLOYMENT=true \
               WEBSITES_PORT=8000
```

#### Step 5: Deploy Code
```bash
# Option A: From local Git repository
az webapp deployment source config-local-git \
    --name cnic-api-app \
    --resource-group cnic-api-rg

# Then push your code
git remote add azure <git-clone-url>
git push azure main

# Option B: From GitHub (if you have a repository)
az webapp deployment source config \
    --name cnic-api-app \
    --resource-group cnic-api-rg \
    --repo-url <your-github-repo> \
    --branch main \
    --manual-integration
```

### Method 2: Azure Container Instances

#### Step 1: Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "api:app"]
```

#### Step 2: Build and Push to Azure Container Registry
```bash
# Create ACR
az acr create --resource-group cnic-api-rg --name cnicapiregistry --sku Basic

# Build and push
az acr build --registry cnicapiregistry --image cnic-api:v1 .
```

#### Step 3: Deploy to Container Instances
```bash
az container create \
    --resource-group cnic-api-rg \
    --name cnic-api-container \
    --image cnicapiregistry.azurecr.io/cnic-api:v1 \
    --cpu 1 \
    --memory 2 \
    --ports 8000 \
    --dns-name-label cnic-api-unique
```

## 📁 Files Required for Deployment

### Core Files
- `api.py` - Main Flask application (Azure-optimized)
- `cnic_model.h5` - Your trained model file
- `requirements.txt` - Python dependencies
- `main.py` - Entry point for Azure App Service

### Deployment Files
- `Procfile` - For Heroku-style deployment
- `runtime.txt` - Python version specification
- `azure_config.md` - This configuration guide

## 🔧 Environment Variables

Set these in Azure App Service Configuration:

| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Flask environment |
| `WEBSITES_PORT` | `8000` | Port for Azure App Service |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Enable build during deployment |

## 🌐 API Endpoints

Once deployed, your API will be available at:
`https://your-app-name.azurewebsites.net`

### Endpoints:
- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Image file prediction
- `POST /predict_base64` - Base64 image prediction

## 📊 Monitoring and Logging

### Enable Application Insights
```bash
az webapp config appsettings set \
    --resource-group cnic-api-rg \
    --name cnic-api-app \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=<your-key>
```

### View Logs
```bash
az webapp log tail --resource-group cnic-api-rg --name cnic-api-app
```

## 💰 Cost Optimization

### Recommended Pricing Tiers:
- **Development**: Basic B1 ($13/month)
- **Production**: Standard S1 ($56/month)
- **High Performance**: Premium P1V2 ($146/month)

### Auto-scaling Configuration:
```bash
az monitor autoscale create \
    --resource-group cnic-api-rg \
    --resource cnic-api-app \
    --min-count 1 \
    --max-count 3 \
    --count 1
```

## 🔒 Security Considerations

1. **Enable HTTPS Only**:
```bash
az webapp update --resource-group cnic-api-rg --name cnic-api-app --https-only true
```

2. **Configure Custom Domain** (Optional):
```bash
az webapp config hostname add \
    --webapp-name cnic-api-app \
    --resource-group cnic-api-rg \
    --hostname your-domain.com
```

3. **API Key Authentication** (Recommended for production):
Add API key validation in your Flask app.

## 🚨 Troubleshooting

### Common Issues:

1. **Model Loading Errors**:
   - Ensure `cnic_model.h5` is in the same directory as `api.py`
   - Check file size limits (Azure App Service has a 1GB limit)

2. **Memory Issues**:
   - Upgrade to higher tier plan
   - Optimize model size using TensorFlow Lite

3. **Timeout Issues**:
   - Increase timeout in `Procfile`
   - Use async processing for large images

4. **Cold Start Issues**:
   - Use "Always On" setting in Azure App Service
   - Implement warming endpoints

## 📞 Support

For issues specific to:
- **Azure**: Check Azure documentation or support
- **API**: Check application logs in Azure portal
- **Model**: Verify model compatibility and preprocessing

## 🎯 Next Steps

1. Deploy to Azure using Method 1 (App Service)
2. Test all endpoints
3. Set up monitoring and alerts
4. Configure custom domain (optional)
5. Implement API authentication
6. Set up CI/CD pipeline
