#!/bin/bash
#
# This script will retrieve necessary keys and properties from Azure Resources 
# deployed using "Deploy to Azure" button and will store them in a file named
# ".env" in the parent directory.

# Login to Azure
if [ -z "$(az account show)" ]; then
  echo "User not signed in Azure. Signin to Azure using 'az login' command."
  az login --use-device-code
fi

# Get the resource group name from the script parameter named resource-group
resourceGroupName=""

# Parse named parameters
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --resource-group) resourceGroupName="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if resourceGroupName is provided
if [ -z "$resourceGroupName" ]; then
    echo "Enter the resource group name where the resources are deployed:"
    read resourceGroupName
fi

# Get resource group deployments, find deployments starting with 'Microsoft.Template' and sort them by timestamp
echo "Getting the deployments in '$resourceGroupName'..."
deploymentName=$(az deployment group list --resource-group $resourceGroupName --query "[?contains(name, 'Microsoft.Template') || contains(name, 'azuredeploy')].{name:name}[0].name" --output tsv)
if [ $? -ne 0 ]; then
    echo "Error occurred while fetching deployments. Exiting..."
    exit 1
fi

# Get output parameters from last deployment using Azure CLI queries instead of jq
echo "Getting the output parameters from the last deployment '$deploymentName' in '$resourceGroupName'..."

# Extract the resource names directly using Azure CLI queries
echo "Extracting the resource names from the deployment outputs..."
storageAccountName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.storageAccountName.value" -o tsv 2>/dev/null || echo "")
logAnalyticsWorkspaceName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.logAnalyticsWorkspaceName.value" -o tsv 2>/dev/null || echo "")
searchServiceName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.searchServiceName.value" -o tsv 2>/dev/null || echo "")
aiFoundryHubName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.aiFoundryHubName.value" -o tsv 2>/dev/null || echo "")
aiFoundryProjectName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.aiFoundryProjectName.value" -o tsv 2>/dev/null || echo "")
keyVaultName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.keyVaultName.value" -o tsv 2>/dev/null || echo "")
containerRegistryName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.containerRegistryName.value" -o tsv 2>/dev/null || echo "")
applicationInsightsName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.applicationInsightsName.value" -o tsv 2>/dev/null || echo "")

# Extract endpoint URLs
searchServiceEndpoint=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.searchServiceEndpoint.value" -o tsv 2>/dev/null || echo "")
aiFoundryHubEndpoint=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.aiFoundryHubEndpoint.value" -o tsv 2>/dev/null || echo "")
aiFoundryProjectEndpoint=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.aiFoundryProjectEndpoint.value" -o tsv 2>/dev/null || echo "")



# If deployment outputs are empty, try to discover resources by type
if [ -z "$storageAccountName" ] || [ -z "$logAnalyticsWorkspaceName" ] || [ -z "$apiManagementName" ] || [ -z "$keyVaultName" ] || [ -z "$containerRegistryName" ]; then
    echo "Some deployment outputs not found, discovering missing resources by type..."
    
    if [ -z "$storageAccountName" ]; then
        storageAccountName=$(az storage account list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$logAnalyticsWorkspaceName" ]; then
        logAnalyticsWorkspaceName=$(az monitor log-analytics workspace list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$searchServiceName" ]; then
        searchServiceName=$(az search service list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$apiManagementName" ]; then
        apiManagementName=$(az apim list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$aiFoundryHubName" ]; then
        aiFoundryHubName=$(az cognitiveservices account list --resource-group $resourceGroupName --query "[?kind=='AIServices'].name | [0]" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$keyVaultName" ]; then
        keyVaultName=$(az keyvault list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$containerRegistryName" ]; then
        containerRegistryName=$(az acr list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
    
    if [ -z "$applicationInsightsName" ]; then
        applicationInsightsName=$(az resource list --resource-group $resourceGroupName --resource-type "Microsoft.Insights/components" --query "[0].name" -o tsv 2>/dev/null || echo "")
    fi
fi

# Get Cosmos DB service information (better retrieval)
echo "Getting Cosmos DB service information..."
cosmosDbAccountName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.cosmosDbAccountName.value" -o tsv 2>/dev/null || echo "")
if [ -z "$cosmosDbAccountName" ]; then
    cosmosDbAccountName=$(az cosmosdb list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
fi

if [ -n "$cosmosDbAccountName" ]; then
    cosmosDbEndpoint=$(az cosmosdb show --name $cosmosDbAccountName --resource-group $resourceGroupName --query documentEndpoint -o tsv 2>/dev/null || echo "")
    cosmosDbKey=$(az cosmosdb keys list --name $cosmosDbAccountName --resource-group $resourceGroupName --query primaryMasterKey -o tsv 2>/dev/null || echo "")
    
    # Construct the connection string properly
    if [ -n "$cosmosDbEndpoint" ] && [ -n "$cosmosDbKey" ]; then
        cosmosDbConnectionString="AccountEndpoint=${cosmosDbEndpoint};AccountKey=${cosmosDbKey};"
    else
        cosmosDbConnectionString=""
    fi
else
    echo "Warning: No Cosmos DB account found in resource group. You may need to deploy one."
    cosmosDbEndpoint=""
    cosmosDbKey=""
    cosmosDbConnectionString=""
fi

# Get the keys from the resources
echo "Getting the keys from the resources..."

# Storage account
if [ -n "$storageAccountName" ]; then
    storageAccountKey=$(az storage account keys list --account-name $storageAccountName --resource-group $resourceGroupName --query "[0].value" -o tsv 2>/dev/null || echo "")
    # Construct the connection string in the correct format
    storageAccountConnectionString="DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net"
else
    echo "Warning: Storage account not found"
    storageAccountKey=""
    storageAccountConnectionString=""
fi

# AI Foundry/Cognitive Services
if [ -n "$aiFoundryHubName" ]; then
    aiFoundryEndpoint=$(az cognitiveservices account show --name $aiFoundryHubName --resource-group $resourceGroupName --query properties.endpoint -o tsv 2>/dev/null || echo "")
    aiFoundryKey=$(az cognitiveservices account keys list --name $aiFoundryHubName --resource-group $resourceGroupName --query key1 -o tsv 2>/dev/null || echo "")
else
    echo "Warning: AI Foundry Hub not found"
    aiFoundryEndpoint=""
    aiFoundryKey=""
fi

# Search service
if [ -n "$searchServiceName" ]; then
    searchServiceKey=$(az search admin-key show --resource-group $resourceGroupName --service-name $searchServiceName --query primaryKey -o tsv 2>/dev/null || echo "")
    if [ -z "$searchServiceEndpoint" ]; then
        searchServiceEndpoint="https://${searchServiceName}.search.windows.net"
    fi
else
    echo "Warning: Search service not found"
    searchServiceKey=""
    searchServiceEndpoint=""
fi

# Application Insights
if [ -n "$applicationInsightsName" ]; then
    appInsightsInstrumentationKey=$(az resource show --resource-group $resourceGroupName --name $applicationInsightsName --resource-type "Microsoft.Insights/components" --query properties.InstrumentationKey -o tsv 2>/dev/null || echo "")
else
    echo "Warning: Application Insights not found"
    appInsightsInstrumentationKey=""
fi

# Get Document Intelligence service name and keys
echo "Getting Document Intelligence service information..."
docIntelServiceName=$(az deployment group show --resource-group $resourceGroupName --name $deploymentName --query "properties.outputs.documentIntelligenceName.value" -o tsv 2>/dev/null || echo "")
if [ -z "$docIntelServiceName" ]; then
    docIntelServiceName=$(az cognitiveservices account list --resource-group $resourceGroupName --query "[?kind=='FormRecognizer'].name | [0]" -o tsv 2>/dev/null || echo "")
fi

if [ -n "$docIntelServiceName" ]; then
    docIntelEndpoint=$(az cognitiveservices account show --name $docIntelServiceName --resource-group $resourceGroupName --query properties.endpoint -o tsv 2>/dev/null || echo "")
    docIntelKey=$(az cognitiveservices account keys list --name $docIntelServiceName --resource-group $resourceGroupName --query key1 -o tsv 2>/dev/null || echo "")
else
    echo "Warning: No Document Intelligence (FormRecognizer) service found in resource group. You may need to deploy one."
    docIntelEndpoint=""
    docIntelKey=""
fi



# Add this section after getting the search service information (around line 100)

# Get Azure AI Search connection ID
# Note: The 'az cognitiveservices account connection' command is not available in all Azure CLI versions
# We'll construct the connection ID manually later in the script
echo "Skipping Azure AI Search connection query (will construct manually)..."
azureAIConnectionId=""


if [ -z "$storageAccountName" ] || [ -z "$aiFoundryProjectName" ]; then
    if [ -z "$storageAccountName" ]; then
        echo "Deployment outputs not found, discovering resources by type..."
    fi
    if [ -z "$aiFoundryProjectName" ]; then
        echo "AI Foundry Project Name not found in deployment outputs, attempting discovery..."
    fi
    
    storageAccountName=$(az storage account list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    searchServiceName=$(az search service list --resource-group $resourceGroupName --query "[0].name" -o tsv 2>/dev/null || echo "")
    aiFoundryHubName=$(az cognitiveservices account list --resource-group $resourceGroupName --query "[?kind=='AIServices'].name | [0]" -o tsv 2>/dev/null || echo "")
    applicationInsightsName=$(az resource list --resource-group $resourceGroupName --resource-type "Microsoft.Insights/components" --query "[0].name" -o tsv 2>/dev/null || echo "")
fi

# Construct Azure AI Search connection ID directly
if [ -n "$aiFoundryHubName" ] && [ -n "$searchServiceName" ]; then
    echo "Constructing Azure AI Search connection ID..."
    
    # Get subscription ID
    subscriptionId=$(az account show --query id -o tsv 2>/dev/null || echo "")
    
    if [ -n "$subscriptionId" ]; then
        # Construct the connection ID based on the pattern: aiFoundryHubName + "-aisearch"
        # Pattern: /subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{aiFoundryHub}/connections/{aiFoundryHub}-aisearch
        azureAIConnectionId="/subscriptions/${subscriptionId}/resourceGroups/${resourceGroupName}/providers/Microsoft.CognitiveServices/accounts/${aiFoundryHubName}/connections/${aiFoundryHubName}-aisearch"
        echo "Constructed connection ID: $azureAIConnectionId"
    else
        echo "Warning: Could not get subscription ID"
        azureAIConnectionId=""
    fi
else
    echo "Warning: Cannot construct Azure AI connection ID - AI Foundry Hub or Search Service not found"
    azureAIConnectionId=""
fi

# Construct AI Foundry Project Endpoint if not found in deployment outputs
if [ -z "$aiFoundryProjectEndpoint" ] && [ -n "$aiFoundryHubName" ] && [ -n "$aiFoundryProjectName" ]; then
    echo "Constructing AI Foundry Project Endpoint..."
    aiFoundryProjectEndpoint="https://${aiFoundryHubName}.services.ai.azure.com/api/projects/${aiFoundryProjectName}"
    echo "Constructed project endpoint: $aiFoundryProjectEndpoint"
elif [ -n "$aiFoundryProjectEndpoint" ] && [[ "$aiFoundryProjectEndpoint" == *"ai.azure.com/build/overview"* ]]; then
    # If we got a web UI URL from deployment outputs, convert it to API endpoint
    echo "Converting web UI URL to API endpoint..."
    aiFoundryProjectEndpoint="https://${aiFoundryHubName}.services.ai.azure.com/api/projects/${aiFoundryProjectName}"
    echo "Converted project endpoint: $aiFoundryProjectEndpoint"
fi

# Overwrite the existing .env file
if [ -f ../.env ]; then
    rm ../.env
fi

# Store the keys and properties in a file
echo "Storing the keys and properties in '.env' file..."

# Azure Storage (with both naming conventions)
echo "AZURE_STORAGE_ACCOUNT_NAME=\"$storageAccountName\"" >> ../.env
echo "AZURE_STORAGE_ACCOUNT_KEY=\"$storageAccountKey\"" >> ../.env
echo "AZURE_STORAGE_CONNECTION_STRING=\"$storageAccountConnectionString\"" >> ../.env

# Azure Document Intelligence
echo "AZURE_DOC_INTEL_ENDPOINT=\"$docIntelEndpoint\"" >> ../.env
echo "AZURE_DOC_INTEL_KEY=\"$docIntelKey\"" >> ../.env

# Other Azure services
echo "LOG_ANALYTICS_WORKSPACE_NAME=\"$logAnalyticsWorkspaceName\"" >> ../.env
echo "SEARCH_SERVICE_NAME=\"$searchServiceName\"" >> ../.env
echo "SEARCH_SERVICE_ENDPOINT=\"$searchServiceEndpoint\"" >> ../.env
echo "SEARCH_ADMIN_KEY=\"$searchServiceKey\"" >> ../.env
echo "AI_FOUNDRY_HUB_NAME=\"$aiFoundryHubName\"" >> ../.env
echo "AI_FOUNDRY_PROJECT_NAME=\"$aiFoundryProjectName\"" >> ../.env
echo "AI_FOUNDRY_ENDPOINT=\"$aiFoundryEndpoint\"" >> ../.env
echo "AI_FOUNDRY_KEY=\"$aiFoundryKey\"" >> ../.env

# Construct AI Foundry Hub Endpoint if missing
if [ -z "$aiFoundryHubEndpoint" ] && [ -n "$aiFoundryHubName" ]; then
    echo "Constructing AI Foundry Hub Endpoint..."
    subscriptionId=$(az account show --query id -o tsv 2>/dev/null || echo "")
    if [ -n "$subscriptionId" ]; then
        aiFoundryHubEndpoint="https://ml.azure.com/home?wsid=/subscriptions/${subscriptionId}/resourceGroups/${resourceGroupName}/providers/Microsoft.CognitiveServices/accounts/${aiFoundryHubName}"
        echo "Constructed hub endpoint: $aiFoundryHubEndpoint"
    fi
fi
echo "AI_FOUNDRY_HUB_ENDPOINT=\"$aiFoundryHubEndpoint\"" >> ../.env

# Construct AI Foundry Project Endpoint if not found in deployment outputs
if [ -z "$aiFoundryProjectEndpoint" ] && [ -n "$aiFoundryHubName" ] && [ -n "$aiFoundryProjectName" ]; then
    echo "Constructing AI Foundry Project Endpoint..."
    aiFoundryProjectEndpoint="https://${aiFoundryHubName}.services.ai.azure.com/api/projects/${aiFoundryProjectName}"
    echo "Constructed project endpoint: $aiFoundryProjectEndpoint"
elif [ -n "$aiFoundryProjectEndpoint" ] && [[ "$aiFoundryProjectEndpoint" == *"ai.azure.com/build/overview"* ]]; then
    # If we got a web UI URL from deployment outputs, convert it to API endpoint
    echo "Converting web UI URL to API endpoint..."
    aiFoundryProjectEndpoint="https://${aiFoundryHubName}.services.ai.azure.com/api/projects/${aiFoundryProjectName}"
    echo "Converted project endpoint: $aiFoundryProjectEndpoint"
fi
echo "AI_FOUNDRY_PROJECT_ENDPOINT=\"$aiFoundryProjectEndpoint\"" >> ../.env
echo "AZURE_AI_CONNECTION_ID=\"$azureAIConnectionId\"" >> ../.env
# Azure Cosmos DB
echo "COSMOS_ENDPOINT=\"$cosmosDbEndpoint\"" >> ../.env
echo "COSMOS_KEY=\"$cosmosDbKey\"" >> ../.env
echo "COSMOS_CONNECTION_STRING=\"$cosmosDbConnectionString\"" >> ../.env

# For backward compatibility, also set OpenAI-style variables pointing to AI Foundry
echo "AZURE_OPENAI_SERVICE_NAME=\"$aiFoundryHubName\"" >> ../.env
echo "AZURE_OPENAI_ENDPOINT=\"$aiFoundryEndpoint\"" >> ../.env
echo "AZURE_OPENAI_KEY=\"$aiFoundryKey\"" >> ../.env
echo "AZURE_OPENAI_DEPLOYMENT_NAME=\"gpt-4.1-mini\"" >> ../.env
echo "MODEL_DEPLOYMENT_NAME=\"gpt-4.1-mini\"" >> ../.env

echo "Keys and properties are stored in '.env' file successfully."

# Display summary of what was configured
echo ""
echo "=== Configuration Summary ==="
echo "Storage Account: $storageAccountName"
echo "Log Analytics Workspace: $logAnalyticsWorkspaceName"
echo "Search Service: $searchServiceName"
echo "API Management: $apiManagementName"
echo "AI Foundry Hub: $aiFoundryHubName"
echo "AI Foundry Project: $aiFoundryProjectName"
echo "Key Vault: $keyVaultName"
echo "Container Registry: $containerRegistryName"
echo "Application Insights: $applicationInsightsName"
if [ -n "$docIntelServiceName" ]; then
    echo "Document Intelligence: $docIntelServiceName"
else
    echo "Document Intelligence: NOT FOUND - You may need to deploy this service"
fi
if [ -n "$cosmosDbAccountName" ]; then
    echo "Cosmos DB: $cosmosDbAccountName"
else
    echo "Cosmos DB: NOT FOUND - You may need to deploy this service"
fi
echo "Environment file created: ../.env"

# Show what needs to be deployed
missing_services=""
if [ -z "$storageAccountName" ]; then missing_services="$missing_services Storage"; fi
if [ -z "$searchServiceName" ]; then missing_services="$missing_services Search"; fi
if [ -z "$aiFoundryHubName" ]; then missing_services="$missing_services AI-Foundry"; fi
if [ -z "$docIntelServiceName" ]; then missing_services="$missing_services Document-Intelligence"; fi
if [ -z "$cosmosDbAccountName" ]; then missing_services="$missing_services Cosmos-DB"; fi

if [ -n "$missing_services" ]; then
    echo ""
    echo "⚠️  Missing services:$missing_services"
    echo "You may need to deploy these services manually or check your deployment template."
fi