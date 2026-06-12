#!/bin/bash
# DeployAI — Azure Deployment Script
# Prerequisites: az cli logged in, Docker installed

# Variables — UPDATE THESE
RESOURCE_GROUP="deployai-rg"
LOCATION="eastus"
ACR_NAME="deployaiacr"
APP_NAME="deployai"
ENVIRONMENT="deployai-env"

echo "=== Step 1: Create Resource Group ==="
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "=== Step 2: Create Azure Container Registry ==="
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

echo "=== Step 3: Build & Push Docker Image ==="
az acr build --registry $ACR_NAME --image deployai:latest .

echo "=== Step 4: Create Container Apps Environment ==="
az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

echo "=== Step 5: Deploy Container App ==="
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --image "${ACR_NAME}.azurecr.io/deployai:latest" \
  --registry-server "${ACR_NAME}.azurecr.io" \
  --registry-username $ACR_NAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8501 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint \
    AZURE_OPENAI_KEY=secretref:openai-key \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o \
    AZURE_OPENAI_API_VERSION=2024-12-01-preview

echo "=== Done ==="
echo "App URL:"
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv
