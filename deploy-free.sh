#!/bin/bash
# DeployAI — Azure App Service (FREE tier) Deployment
# No Docker needed. Deploys Python directly.

APP_NAME="deployai-$(shuf -i 1000-9999 -n 1)"
RESOURCE_GROUP="deployai-rg"
LOCATION="eastus"

echo "=== Creating Resource Group ==="
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "=== Creating App Service (Free F1) ==="
az appservice plan create --name deployai-plan --resource-group $RESOURCE_GROUP --sku F1 --is-linux

echo "=== Creating Web App ==="
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan deployai-plan \
  --runtime "PYTHON:3.11"

echo "=== Configuring Startup Command ==="
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "streamlit run app/main.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true"

echo "=== Setting App Settings ==="
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_ENDPOINT="your-endpoint" \
    AZURE_OPENAI_KEY="your-key" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
    AZURE_OPENAI_API_VERSION="2024-12-01-preview" \
    WEBSITES_PORT=8000

echo "=== Deploying Code ==="
az webapp deployment source config-local-git \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

echo "=== App URL ==="
echo "https://${APP_NAME}.azurewebsites.net"
echo ""
echo "To deploy code, push to the git remote shown above."
echo "Or use: az webapp up --name $APP_NAME"
