# 🔧 Azure Deployment Fix Guide

## Problem: Static Site Detection Error

If you're getting this error:
```
ERROR: failed to push mcr.microsoft.com/***/appsvc/staticsite
```

This means Azure is trying to deploy your Python Flask app as a static site instead of a Python application.

## ✅ Solution: Proper Azure Configuration

### Step 1: Verify File Structure
Make sure your repository has these files:
```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies  
├── runtime.txt         # Python version (python-3.11.0)
├── web.config         # IIS configuration for Windows
├── startup.py         # Azure startup script
├── gunicorn.conf.py   # Gunicorn configuration
├── Procfile           # Process configuration
└── cnic_model.h5      # Your ML model
```

### Step 2: Configure Azure App Service Settings

In Azure Portal → Your App Service → Configuration → Application Settings, add:

| Name | Value |
|------|-------|
| `WEBSITES_PORT` | `8000` |
| `PYTHONPATH` | `/home/site/wwwroot` |
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

### Step 3: Set Runtime Stack

In Azure Portal → Your App Service → Configuration → General Settings:
- **Runtime stack**: `Python`
- **Version**: `3.11`
- **Startup Command**: `gunicorn -c gunicorn.conf.py app:app`

### Step 4: Azure CLI Commands (Alternative)

```bash
# Create the web app with Python runtime
az webapp create \
  --resource-group your-rg \
  --plan your-plan \
  --name your-app \
  --runtime "PYTHON|3.11"

# Configure app settings
az webapp config appsettings set \
  --resource-group your-rg \
  --name your-app \
  --settings \
    WEBSITES_PORT=8000 \
    PYTHONPATH=/home/site/wwwroot \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Set startup command
az webapp config set \
  --resource-group your-rg \
  --name your-app \
  --startup-file "gunicorn -c gunicorn.conf.py app:app"
```

### Step 5: Deployment from GitHub

1. **Fork/Clone**: Make sure your code is in GitHub
2. **Deployment Center**: Go to Azure Portal → Your App Service → Deployment Center
3. **Source**: Select GitHub
4. **Repository**: Select your repository
5. **Branch**: Select `main`
6. **Build Provider**: Choose "App Service build service"

### Step 6: Manual Deployment via Git

```bash
# Get deployment URL from Azure Portal
git remote add azure <your-azure-git-url>
git push azure main
```

## 🚨 Common Issues & Fixes

### Issue 1: Still detecting as static site
**Solution**: Delete and recreate the App Service with explicit Python runtime

### Issue 2: Build failures
**Solution**: Check `requirements.txt` has compatible versions:
```txt
Flask==3.0.0
flask-cors==4.0.0
tensorflow-cpu==2.15.0
gunicorn==21.2.0
```

### Issue 3: Model loading errors
**Solution**: Ensure `cnic_model.h5` is in the repository and path is correct in `app.py`

### Issue 4: Memory issues
**Solution**: Upgrade to higher tier (Standard S1 or Premium)

## 🔍 Debugging Steps

1. **Check Logs**:
```bash
az webapp log tail --resource-group your-rg --name your-app
```

2. **SSH into Container** (Linux App Service):
```bash
az webapp ssh --resource-group your-rg --name your-app
```

3. **Test Endpoints**:
```bash
curl https://your-app.azurewebsites.net/health
```

## 📝 Deployment Checklist

- [ ] Runtime set to Python 3.11
- [ ] Startup command configured
- [ ] Environment variables set
- [ ] Requirements.txt has compatible versions
- [ ] Model file included in repository
- [ ] web.config present for Windows hosting
- [ ] Build during deployment enabled

## 🆘 If All Else Fails

1. **Delete** the current App Service
2. **Create new** App Service with explicit Python runtime
3. **Configure** all settings before deployment
4. **Deploy** from GitHub with proper build service

The key is ensuring Azure recognizes this as a Python application from the start!
