#!/bin/bash

# Variables
resourceGroup="sales-pipeline-rg"
location="eastus"
dataFactoryName="salesDataFactory"
storageAccountName="salesdatalake$(date +%s)"
dataLakeName="salesdatalake"
databricksWorkspaceName="sales-databricks"
synapseWorkspaceName="sales-synapse"
eventHubNamespace="sales-eventhub-ns"
eventHubName="sales-events"
streamAnalyticsJobName="sales-stream-job"
analysisServicesName="sales-analysis"
machineLearningWorkspaceName="sales-ml"
powerBIName="sales-powerbi"

# Step 1: Create Resource Group
echo "Creating resource group: $resourceGroup"
az group create --name $resourceGroup --location $location

# Step 2: Create Azure Data Lake Storage Gen2
echo "Creating storage account: $storageAccountName"
az storage account create \
  --name $storageAccountName \
  --resource-group $resourceGroup \
  --location $location \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-hierarchical-namespace true

# Create containers (Bronze, Silver, Gold)
az storage container create --name bronze --account-name $storageAccountName
az storage container create --name silver --account-name $storageAccountName
az storage container create --name gold --account-name $storageAccountName

# Step 3: Create Azure Data Factory
echo "Creating Azure Data Factory: $dataFactoryName"
az datafactory create \
  --name $dataFactoryName \
  --resource-group $resourceGroup \
  --location $location

# Step 4: Create Azure Databricks Workspace
echo "Creating Azure Databricks workspace: $databricksWorkspaceName"
az databricks workspace create \
  --name $databricksWorkspaceName \
  --resource-group $resourceGroup \
  --location $location \
  --sku standard

# Step 5: Create Azure Synapse Analytics Workspace
echo "Creating Azure Synapse Analytics workspace: $synapseWorkspaceName"
az synapse workspace create \
  --name $synapseWorkspaceName \
  --resource-group $resourceGroup \
  --storage-account $storageAccountName \
  --location $location \
  --sql-admin-login-user user_id \
  --sql-admin-login-password "your_password"

# Step 6: Create Azure Event Hubs Namespace and Event Hub
echo "Creating Event Hubs namespace: $eventHubNamespace"
az eventhubs namespace create \
  --name $eventHubNamespace \
  --resource-group $resourceGroup \
  --location $location \
  --sku Basic

echo "Creating Event Hub: $eventHubName"
az eventhubs eventhub create \
  --name $eventHubName \
  --namespace-name $eventHubNamespace \
  --resource-group $resourceGroup \
  --partition-count 2

# Step 7: Create Azure Stream Analytics Job
echo "Creating Stream Analytics job: $streamAnalyticsJobName"
az stream-analytics job create \
  --name $streamAnalyticsJobName \
  --resource-group $resourceGroup \
  --location $location \
  --output-error-policy Drop \
  --events-outoforder-policy Drop \
  --events-late-arrival-max-delay 5 \
  --events-outoforder-max-delay 5

# Step 8: Create Azure Analysis Services
echo "Creating Azure Analysis Services: $analysisServicesName"
az analysis-services server create \
  --name $analysisServicesName \
  --resource-group $resourceGroup \
  --location $location \
  --sku B1 \
  --admin-users "user_id@example.com"

# Step 9: Create Azure Machine Learning Workspace
echo "Creating Azure Machine Learning workspace: $machineLearningWorkspaceName"
az ml workspace create \
  --name $machineLearningWorkspaceName \
  --resource-group $resourceGroup \
  --location $location

# Step 10: Output instructions for Power BI
echo "Power BI setup: Use Power BI Desktop to connect to Azure Synapse Analytics and Azure Analysis Services. Create a workspace in Power BI Service after signing in with your Azure account."

echo "Setup complete! Check the Azure Portal to configure pipelines and services."
