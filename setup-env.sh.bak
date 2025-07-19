#!/bin/bash

# Project root directory on the local machine
export PROJDIR=~/py/ai-python-scripts

# Azure resource group for all resources
export AGENTICAI_RG=agenticairg

# Azure region for resource deployment
export AZURE_LOCATION=eastus

# Azure subscription ID (will be set dynamically)
export SUBSCRIPTION_ID=""

# Azure CLI version (will be set dynamically)
export AZURE_CLI_VERSION=""

# App Service name for the chatbot interface
export AGENTICAI_APP_SRV=agenticai-app-srv

# Python script name for the App Service
export AGENTICAI_APP=agenticai-chat-bot

# Directory for App Service code
export AGENTICAI_APP_DIR=$PROJDIR/app-service

# Path to the App Service deployment zip file
export AGENTICAI_APP_ZIP=$AGENTICAI_APP_DIR/webapp.zip

# Port for the App Service application
export AGENTICAI_APP_PORT=8000

# Function App name for task management
export AGENTICAI_TASK_CHECKER_FN_APP=agenticai-task-checker-fn-app

# Directory for Function App code
export AGENTICAI_FN_DIR=$PROJDIR/function-app

# Path to the Function App deployment zip file
export AGENTICAI_FN_ZIP=$AGENTICAI_FN_DIR/function-app.zip

# Python script name for the Function App
export AGENTICAI_FN_SCRIPT=task-checker-fn

# Timeout for Function App execution (in seconds)
export AGENTICAI_FN_TIMEOUT=600

# Cosmos DB account name
export COSMOS_DB_ACCOUNT=agenticai-cosmos-db

# Cosmos DB endpoint URL (will be set dynamically)
export COSMOS_DB_ENDPOINT=""

# Cosmos DB primary key (will be set dynamically)
export COSMOS_DB_KEY=""

# Cosmos DB database name
export COSMOS_DATABASE_NAME=taskdb

# Cosmos DB container name
export COSMOS_CONTAINER_NAME=task

# Storage Account name for file storage
export STORAGE_ACCOUNT_NAME=agenticaistorage12345678

# Storage Account primary key (will be set dynamically)
export STORAGE_ACCOUNT_KEY=""

# Storage Account connection string for Function App (will be set dynamically)
export AGENTICAI_FN_STORAGE=""

# Blob container name for file storage
export STORAGE_CONTAINER_NAME=agenticai-files

# Application Insights resource name
export APP_INSIGHTS_NAME=agenticai-app-insights

# Application Insights instrumentation key (will be set dynamically)
export APP_INSIGHTS_KEY=""

# Hugging Face API URL for LLM integration (static, set based on model used)
export HF_API_URL=https://vdow3mpnreu0sh2y.us-east-1.aws.endpoints.huggingface.cloud

# Hugging Face API key (static, set after obtaining from Hugging Face)
export HF_API_KEY=""


# DEEP SEEK  API URL for LLM integration (static, set based on model used)
export DS_API_URL=""

# DEEP SEEK  API key 
export DS_API_KEY=""


# OpenAI resource name (optional, if used instead of Hugging Face)
export AGENTICAI_OPENAI=agenticai-openai

# OpenAI API key (optional, set after obtaining from OpenAI)
export OPENAI_API_KEY=""

# Log level for application logging
export AGENTICAI_LOG_LEVEL=INFO

# Environment identifier (e.g., dev, prod)
export AGENTICAI_ENV=dev


# Environment BUILD during deployment  
export SCM_DO_BUILD_DURING_DEPLOYMENT="true"


# Ensure Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI is not installed. Please install it before running this script."
    exit 1
fi

# Perform az login if not already logged in
echo "Checking Azure CLI login status..."
az account show &> /dev/null
if [ $? -ne 0 ]; then
    echo "Not logged in. Performing az login..."
    az login
else
    echo "Already logged in to Azure CLI."
fi

# Fetch Azure Subscription ID
echo "Fetching Subscription ID..."
export SUBSCRIPTION_ID=$(az account show --query id --output tsv)
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "Failed to fetch Subscription ID. Please check your Azure CLI login."
    exit 1
fi
echo "SUBSCRIPTION_ID set to $SUBSCRIPTION_ID"

# Fetch Azure CLI Version
echo "Fetching Azure CLI Version..."
export AZURE_CLI_VERSION=$(az --version | grep azure-cli | awk '{print $2}')
if [ -z "$AZURE_CLI_VERSION" ]; then
    echo "Failed to fetch Azure CLI Version."
    exit 1
fi
echo "AZURE_CLI_VERSION set to $AZURE_CLI_VERSION"

# Fetch Cosmos DB Endpoint
echo "Fetching Cosmos DB Endpoint..."
export COSMOS_DB_ENDPOINT=$(az cosmosdb show --name $COSMOS_DB_ACCOUNT --resource-group $AGENTICAI_RG --query documentEndpoint --output tsv)
if [ -z "$COSMOS_DB_ENDPOINT" ]; then
    echo "Failed to fetch Cosmos DB Endpoint. Please verify the Cosmos DB account '$COSMOS_DB_ACCOUNT' exists in resource group '$AGENTICAI_RG'."
    exit 1
fi
echo "COSMOS_DB_ENDPOINT set to $COSMOS_DB_ENDPOINT"

# Fetch Cosmos DB Primary Key
echo "Fetching Cosmos DB Primary Key..."
export COSMOS_DB_KEY=$(az cosmosdb keys list --name $COSMOS_DB_ACCOUNT --resource-group $AGENTICAI_RG --query primaryMasterKey --output tsv)
if [ -z "$COSMOS_DB_KEY" ]; then
    echo "Failed to fetch Cosmos DB Primary Key. Please verify the Cosmos DB account '$COSMOS_DB_ACCOUNT' exists in resource group '$AGENTICAI_RG'."
    exit 1
fi
echo "COSMOS_DB_KEY set (redacted for security)"

# Fetch Storage Account Primary Key
echo "Fetching Storage Account Primary Key..."
export STORAGE_ACCOUNT_KEY=$(az storage account keys list --account-name $STORAGE_ACCOUNT_NAME --resource-group $AGENTICAI_RG --query "[0].value" --output tsv)
if [ -z "$STORAGE_ACCOUNT_KEY" ]; then
    echo "Failed to fetch Storage Account Primary Key. Please verify the Storage Account '$STORAGE_ACCOUNT_NAME' exists in resource group '$AGENTICAI_RG'."
    exit 1
fi
echo "STORAGE_ACCOUNT_KEY set (redacted for security)"

# Fetch Storage Account Connection String
echo "Fetching Storage Account Connection String..."
export AGENTICAI_FN_STORAGE=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $AGENTICAI_RG --query connectionString --output tsv)
if [ -z "$AGENTICAI_FN_STORAGE" ]; then
    echo "Failed to fetch Storage Account Connection String. Please verify the Storage Account '$STORAGE_ACCOUNT_NAME' exists in resource group '$AGENTICAI_RG'."
    exit 1
fi
echo "AGENTICAI_FN_STORAGE set (redacted for security)"

# Fetch Application Insights Instrumentation Key
echo "Fetching Application Insights Instrumentation Key..."
export APP_INSIGHTS_KEY=$(az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $AGENTICAI_RG --query instrumentationKey --output tsv)
if [ -z "$APP_INSIGHTS_KEY" ]; then
    echo "Failed to fetch Application Insights Instrumentation Key. Please verify the Application Insights resource '$APP_INSIGHTS_NAME' exists in resource group '$AGENTICAI_RG'."
    exit 1
fi
echo "APP_INSIGHTS_KEY set (redacted for security)"

export COSMOS_CONNECTION_STRING="AccountEndpoint=$COSMOS_DB_ENDPOINT;AccountKey=$COSMOS_DB_KEY;"


echo "Environment variables successfully configured."
