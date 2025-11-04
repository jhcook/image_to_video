# Azure AI Foundry Sora Backend Guide

Complete guide to using Sora-2 through Azure AI Foundry (Azure OpenAI Service).

## Overview

Azure AI Foundry provides enterprise deployment of OpenAI's Sora-2 models with Azure's security, compliance, and governance features. Key benefits:

- **Enterprise security** with Azure Active Directory integration
- **Compliance** with SOC 2, HIPAA, and other certifications
- **RBAC** (Role-Based Access Control) for team management
- **Private endpoints** for secure network access
- **Azure billing** integrated with your organization
- **Regional deployment** for data residency requirements

## Prerequisites

- **Azure Subscription**: Active Azure subscription
- **AI Foundry Access**: Access to Azure AI Foundry
- **Sora Deployment**: Sora-2 model deployed in your resource
- **Permissions**: Contributor or Cognitive Services User role

## Getting Started

### Step 1: Create Azure OpenAI Resource

**Via Azure Portal:**

1. Navigate to [Azure Portal](https://portal.azure.com/)
2. Click "Create a resource"
3. Search for "Azure OpenAI"
4. Click "Create"
5. Configure:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose region (e.g., East US, West Europe)
   - **Name**: Unique name for your resource
   - **Pricing Tier**: Standard

**Via Azure CLI:**

```bash
# Set variables
RESOURCE_GROUP="video-gen-rg"
LOCATION="eastus"
RESOURCE_NAME="my-sora-resource"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kind OpenAI \
  --sku S0 \
  --custom-domain $RESOURCE_NAME
```

### Step 2: Deploy Sora-2 Model

**Via Azure AI Foundry Studio:**

1. Go to [Azure AI Foundry](https://ai.azure.com/)
2. Select your resource
3. Navigate to "Deployments"
4. Click "Create new deployment"
5. Select:
   - **Model**: sora-2 or sora-2-pro
   - **Deployment name**: sora-2 (or custom name)
   - **Model version**: Latest available
6. Click "Create"

**Via Azure CLI:**

```bash
# Deploy Sora-2 model
az cognitiveservices account deployment create \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name sora-2 \
  --model-name sora-2 \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name Standard
```

### Step 3: Get Credentials

**Via Azure Portal:**

1. Navigate to your Azure OpenAI resource
2. Go to "Keys and Endpoint"
3. Copy:
   - **Key 1** (API key)
   - **Endpoint** (e.g., https://your-resource.openai.azure.com/)

**Via Azure CLI:**

```bash
# Get endpoint
ENDPOINT=$(az cognitiveservices account show \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.endpoint" \
  --output tsv)

# Get API key
API_KEY=$(az cognitiveservices account keys list \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "key1" \
  --output tsv)

echo "Endpoint: $ENDPOINT"
echo "API Key: $API_KEY"
```

## Configuration

### Environment Variables

**Method 1: .env File (Recommended)**

```bash
# Create or edit .env file
cat > .env << EOF
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview
EOF
```

**Method 2: Export Variables**

```bash
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-10-01-preview"  # Optional, has default
```

**Method 3: Azure CLI Authentication**

For organizations using Azure AD:

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# The tool can use Azure CLI credentials automatically
# No need to set AZURE_OPENAI_API_KEY if using managed identity
```

### Configuration Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes* | - | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | - | Your resource endpoint URL |
| `AZURE_OPENAI_API_VERSION` | No | 2024-10-01-preview | API version to use |

*Not required if using Azure CLI authentication with managed identity

### Verify Configuration

```bash
# Test configuration
./image2video.py --backend azure-sora --list-models

# Expected output:
# Available models for backend 'azure-sora':
#   - sora-2 (default)
#   - sora-2-pro
```

## Available Models

Azure AI Foundry supports the same Sora-2 models as OpenAI:

### sora-2 (Standard)

```bash
./image2video.py --backend azure-sora --model sora-2 \
  -i "image.jpg" "Your prompt"
```

**Characteristics:**
- High quality video generation
- Standard generation time (~2-5 minutes)
- Best for most use cases

### sora-2-pro (Advanced)

```bash
./image2video.py --backend azure-sora --model sora-2-pro \
  -i "image.jpg" "Your prompt"
```

**Characteristics:**
- Superior quality with enhanced detail
- Standard generation time (~2-5 minutes)
- Best for high-end production work

## Basic Usage

### Text-to-Video

```bash
./image2video.py --backend azure-sora \
  "A peaceful mountain landscape at sunrise"
```

### Image-to-Video

```bash
# Single image
./image2video.py --backend azure-sora \
  -i "reference.jpg" \
  "Cinematic pan across the scene"

# Multiple images
./image2video.py --backend azure-sora \
  -i "img1.jpg,img2.jpg,img3.jpg" \
  "Smooth camera movement through the space"
```

### With Model Selection

```bash
# Standard model
./image2video.py --backend azure-sora --model sora-2 \
  -i "test.jpg" "Test prompt"

# Pro model for production
./image2video.py --backend azure-sora --model sora-2-pro \
  -i "hero.jpg" "Final production prompt"
```

## Video Parameters

All Sora-2 parameters work with Azure deployment:

```bash
# Duration
./image2video.py --backend azure-sora --duration 10 "Prompt"

# Resolution
./image2video.py --backend azure-sora \
  --width 1920 --height 1080 "Prompt"

# Portrait for mobile
./image2video.py --backend azure-sora \
  --width 1080 --height 1920 "Prompt"

# Seed for reproducibility
./image2video.py --backend azure-sora --seed 42 "Prompt"

# Loop
./image2video.py --backend azure-sora --loop true "Prompt"
```

See **[OpenAI Sora Guide](openai-sora.md)** for detailed parameter documentation.

## Azure-Specific Features

### Regional Deployment

Deploy in different regions for:
- **Data residency** compliance
- **Latency optimization**
- **Redundancy** and disaster recovery

```bash
# Deploy in multiple regions
az cognitiveservices account create \
  --name "sora-eastus" \
  --location eastus \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0

az cognitiveservices account create \
  --name "sora-westeurope" \
  --location westeurope \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0
```

Switch between regions by changing endpoint:

```bash
# Use East US deployment
export AZURE_OPENAI_ENDPOINT="https://sora-eastus.openai.azure.com/"

# Use West Europe deployment
export AZURE_OPENAI_ENDPOINT="https://sora-westeurope.openai.azure.com/"
```

### Private Endpoints

Secure your API access with private endpoints:

```bash
# Create virtual network
az network vnet create \
  --name video-gen-vnet \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --address-prefix 10.0.0.0/16 \
  --subnet-name default \
  --subnet-prefix 10.0.0.0/24

# Create private endpoint
az network private-endpoint create \
  --name sora-private-endpoint \
  --resource-group $RESOURCE_GROUP \
  --vnet-name video-gen-vnet \
  --subnet default \
  --private-connection-resource-id "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME" \
  --group-id account \
  --connection-name sora-connection
```

### Managed Identity

Use Azure Managed Identity for keyless authentication:

```bash
# Enable system-assigned managed identity
az cognitiveservices account identity assign \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP

# Grant permissions to managed identity
IDENTITY_ID=$(az cognitiveservices account identity show \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId \
  --output tsv)

az role assignment create \
  --assignee $IDENTITY_ID \
  --role "Cognitive Services User" \
  --scope "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME"
```

### RBAC (Role-Based Access Control)

Control team access with Azure RBAC:

```bash
# Grant user access
USER_EMAIL="user@example.com"
USER_ID=$(az ad user show --id $USER_EMAIL --query id --output tsv)

az role assignment create \
  --assignee $USER_ID \
  --role "Cognitive Services User" \
  --scope "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME"

# Available roles:
# - Cognitive Services User: Can use the service
# - Cognitive Services Contributor: Can manage deployments
# - Cognitive Services Administrator: Full control
```

### Monitoring and Logging

Enable diagnostics for usage tracking:

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --workspace-name video-gen-logs \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --workspace-name video-gen-logs \
  --resource-group $RESOURCE_GROUP \
  --query id \
  --output tsv)

# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name sora-diagnostics \
  --resource "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME" \
  --workspace $WORKSPACE_ID \
  --logs '[{"category":"RequestResponse","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

## Cost Management

### Monitoring Usage

**Via Azure Portal:**
1. Go to your Azure OpenAI resource
2. Navigate to "Metrics"
3. View usage data and costs

**Via Azure CLI:**

```bash
# Get usage for last 30 days
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --resource-group $RESOURCE_GROUP \
  --query "[?contains(instanceName, 'sora')]"
```

### Setting Budget Alerts

```bash
# Create budget
az consumption budget create \
  --budget-name sora-monthly-budget \
  --amount 1000 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date $(date -d '+1 year' +%Y-%m-01) \
  --resource-group $RESOURCE_GROUP \
  --contact-emails admin@example.com
```

### Cost Optimization Tips

**Use lower-cost options during development:**
```bash
# Standard model for testing
./image2video.py --backend azure-sora --model sora-2 \
  --width 1280 --height 720 \
  --duration 5 \
  -i "test.jpg" "Test prompt"

# Pro model only for production
./image2video.py --backend azure-sora --model sora-2-pro \
  --width 3840 --height 2160 \
  --duration 15 \
  -i "final.jpg" "Production prompt"
```

## Troubleshooting

### Authentication Issues

**Error: "Invalid API key"**

```bash
# Verify key is set
echo $AZURE_OPENAI_API_KEY

# Get fresh key from Azure
az cognitiveservices account keys list \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP
```

**Error: "Endpoint not found"**

```bash
# Verify endpoint format
echo $AZURE_OPENAI_ENDPOINT
# Should be: https://your-resource.openai.azure.com/

# Get correct endpoint
az cognitiveservices account show \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.endpoint"
```

**Error: "Access denied"**

```bash
# Check your role assignment
az role assignment list \
  --scope "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME" \
  --assignee YOUR-USER-ID

# Grant necessary permissions
az role assignment create \
  --assignee YOUR-USER-ID \
  --role "Cognitive Services User" \
  --scope "/subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$RESOURCE_NAME"
```

### Deployment Issues

**Error: "Deployment not found"**

```bash
# List deployments
az cognitiveservices account deployment list \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP

# Create deployment if missing
az cognitiveservices account deployment create \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name sora-2 \
  --model-name sora-2 \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 1 \
  --sku-name Standard
```

**Error: "Insufficient quota"**

```bash
# Check current quota
az cognitiveservices usage list \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP

# Request quota increase via Azure Support portal
```

### API Version Issues

**Error: "API version not supported"**

```bash
# Try latest API version
export AZURE_OPENAI_API_VERSION="2024-10-01-preview"

# Or use stable version
export AZURE_OPENAI_API_VERSION="2024-06-01"
```

### Network Issues

**Error: "Connection timeout"**

- Check if private endpoint is configured correctly
- Verify NSG (Network Security Group) rules
- Ensure firewall allows outbound HTTPS
- Check if resource is in correct region

**For private endpoint users:**

```bash
# Verify private endpoint connection
az network private-endpoint show \
  --name sora-private-endpoint \
  --resource-group $RESOURCE_GROUP

# Check DNS resolution
nslookup your-resource.openai.azure.com
```

## Security Best Practices

### Key Management

**Rotate keys regularly:**

```bash
# Regenerate key 2
az cognitiveservices account keys regenerate \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --key-name key2

# Update application to use new key
export AZURE_OPENAI_API_KEY="new-key-2"

# Regenerate key 1
az cognitiveservices account keys regenerate \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --key-name key1
```

**Use Key Vault:**

```bash
# Create Key Vault
az keyvault create \
  --name video-gen-kv \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Store API key
az keyvault secret set \
  --vault-name video-gen-kv \
  --name AzureOpenAIKey \
  --value "your-api-key"

# Retrieve key in scripts
AZURE_OPENAI_API_KEY=$(az keyvault secret show \
  --vault-name video-gen-kv \
  --name AzureOpenAIKey \
  --query value \
  --output tsv)
```

### Network Security

**Enable firewall:**

```bash
# Set default action to deny
az cognitiveservices account update \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --default-action Deny

# Add allowed IP
az cognitiveservices account network-rule add \
  --name $RESOURCE_NAME \
  --resource-group $RESOURCE_GROUP \
  --ip-address "YOUR-IP-ADDRESS"
```

### Compliance

Azure AI Foundry is compliant with:
- SOC 2 Type 2
- ISO 27001
- HIPAA
- GDPR
- FedRAMP (select regions)

**Check compliance status:**
- [Azure Compliance Documentation](https://docs.microsoft.com/azure/compliance/)
- [Trust Center](https://www.microsoft.com/trust-center)

## Comparison: Azure vs OpenAI Direct

| Feature | Azure AI Foundry | OpenAI Direct |
|---------|------------------|---------------|
| **Security** | Enterprise-grade, Azure AD | Standard API key |
| **Compliance** | SOC 2, HIPAA, etc. | OpenAI policies |
| **Network** | Private endpoints available | Public internet only |
| **Billing** | Azure invoicing | OpenAI billing |
| **RBAC** | Full Azure RBAC | Organization management |
| **Regional** | Choose deployment region | Fixed regions |
| **Support** | Azure Support plans | OpenAI support |
| **API** | Same Sora-2 API | Same Sora-2 API |
| **Pricing** | Azure pricing | OpenAI pricing |

**Choose Azure when:**
- Need enterprise security and compliance
- Want private network access
- Require data residency in specific regions
- Already using Azure services
- Need RBAC for team management

**Choose OpenAI Direct when:**
- Simple authentication is sufficient
- Don't need enterprise features
- Prefer OpenAI billing
- Want fastest access to new features

## Examples

### Example 1: Enterprise Setup with Managed Identity

```bash
# Setup (one-time)
az login
az account set --subscription "your-subscription"

# No API key needed - uses Azure CLI credentials
./image2video.py --backend azure-sora \
  -i "corporate_photo.jpg" \
  "Professional corporate video"
```

### Example 2: Multi-Region Deployment

```bash
# US deployment for Americas
export AZURE_OPENAI_ENDPOINT="https://sora-eastus.openai.azure.com/"
./image2video.py --backend azure-sora "Prompt"

# EU deployment for Europe (data residency)
export AZURE_OPENAI_ENDPOINT="https://sora-westeurope.openai.azure.com/"
./image2video.py --backend azure-sora "Prompt"
```

### Example 3: Automated Pipeline with Key Vault

```bash
#!/bin/bash
# Production script with Key Vault integration

# Get credentials from Key Vault
export AZURE_OPENAI_API_KEY=$(az keyvault secret show \
  --vault-name video-gen-kv \
  --name AzureOpenAIKey \
  --query value \
  --output tsv)

export AZURE_OPENAI_ENDPOINT=$(az keyvault secret show \
  --vault-name video-gen-kv \
  --name AzureOpenAIEndpoint \
  --query value \
  --output tsv)

# Generate video
./image2video.py --backend azure-sora --model sora-2-pro \
  -i "input/*.jpg" \
  "$(cat prompt.txt)"
```

## Additional Resources

- 📖 **[OpenAI Sora Guide](openai-sora.md)** - Same API, detailed usage
- 🔧 **[Troubleshooting](../advanced/troubleshooting.md)** - General troubleshooting
- 📚 **[User Guide](../user-guide.md)** - Complete usage guide

## External Links

- [Azure AI Foundry](https://ai.azure.com/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Portal](https://portal.azure.com/)
- [Azure CLI Documentation](https://learn.microsoft.com/cli/azure/)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [Azure Compliance](https://docs.microsoft.com/azure/compliance/)

---

**Need help?** Check the **[Troubleshooting Guide](../advanced/troubleshooting.md)** or open an [Azure Support ticket](https://azure.microsoft.com/support/create-ticket/).
