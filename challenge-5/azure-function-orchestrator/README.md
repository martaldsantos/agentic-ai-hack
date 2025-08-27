# Azure Function with Semantic Kernel Orchestrator

This Azure Function provides HTTP endpoints for processing insurance claims using a multi-agent semantic kernel orchestration system.

## 🏗️ Architecture

The function integrates three specialized AI agents:
- **Claim Reviewer**: Validates claim documentation and completeness
- **Risk Analyzer**: Assesses fraud risk and authenticity  
- **Policy Checker**: Determines coverage eligibility

## 📁 Project Structure

```
azure-function-orchestrator/
├── host.json                      # Function host configuration
├── local.settings.json           # Development settings (template)
├── requirements.txt               # Python dependencies
├── function_app.py               # Main Azure Function entry point
├── orchestrator/
│   ├── __init__.py
│   ├── semantic_orchestrator.py  # Core orchestration logic
│   └── tools.py                 # Cosmos DB plugin
└── tests/
    └── test_orchestrator.py      # Test suite
```

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.9+
- Azure Functions Core Tools v4
- Azure subscription with:
  - Azure AI Foundry project
  - Cosmos DB instance
  - Azure identity credentials

### 2. Environment Configuration

Update `local.settings.json` with your Azure credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "AI_FOUNDRY_PROJECT_ENDPOINT": "https://your-ai-foundry-endpoint",
    "MODEL_DEPLOYMENT_NAME": "gpt-4.1-mini",
    "COSMOS_ENDPOINT": "https://your-cosmos-account.documents.azure.com:443/",
    "COSMOS_KEY": "your-cosmos-primary-key",
    "AZURE_CLIENT_ID": "your-app-registration-client-id",
    "AZURE_CLIENT_SECRET": "your-app-registration-secret",
    "AZURE_TENANT_ID": "your-tenant-id"
  }
}
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Local Development

Start the function locally:

```bash
func start
```

The function will be available at:
- `http://localhost:7071/api/claim` - Main claim processing endpoint
- `http://localhost:7071/api/health` - Health check endpoint
- `http://localhost:7071/api/test-cosmos` - Cosmos DB connection test

## 📡 API Endpoints

### POST /api/claim
Process insurance claims with multi-agent analysis.

**Request Body:**
```json
{
  "claim_details": "Vehicle collision resulting in $15,000 damage...",
  "claim_id": "CL002"  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "claim_details": "Vehicle collision resulting in $15,000 damage...",
  "claim_id": "CL002",
  "agent_analyses": [
    {
      "agent_name": "ClaimReviewer",
      "analysis": "CLAIM STATUS: VALID..."
    },
    {
      "agent_name": "RiskAnalyzer", 
      "analysis": "RISK LEVEL: LOW..."
    },
    {
      "agent_name": "PolicyChecker",
      "analysis": "COVERAGE: COVERED..."
    }
  ],
  "comprehensive_analysis": "# Insurance Claim Analysis Report...",
  "timestamp": "1234567890.123"
}
```

### GET /api/claim
Alternative GET method with query parameters:

```
GET /api/claim?claim_details=Vehicle collision...&claim_id=CL002
```

### GET /api/health
Health check endpoint:

```json
{
  "status": "healthy",
  "timestamp": "1234567890.123",
  "service": "Insurance Claim Orchestrator",
  "version": "1.0.0"
}
```

### GET /api/test-cosmos
Test Cosmos DB connectivity:

```json
{
  "status": "success",
  "cosmos_test_result": "✅ Cosmos DB connection successful!...",
  "timestamp": "1234567890.123"
}
```

## 🧪 Testing

### Local Testing
Run the test suite:

```bash
python tests/test_orchestrator.py
```

### cURL Examples

**Process a claim:**
```bash
curl -X POST http://localhost:7071/api/claim \
  -H "Content-Type: application/json" \
  -d '{
    "claim_details": "Vehicle collision on highway resulting in $15,000 damage to front end.",
    "claim_id": "CL002"
  }'
```

**Health check:**
```bash
curl http://localhost:7071/api/health
```

**Test Cosmos DB:**
```bash
curl http://localhost:7071/api/test-cosmos
```

## 🚀 Deployment

### Deploy to Azure

1. Create an Azure Function App:
```bash
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-location westus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name myInsuranceClaimFunction \
  --storage-account mystorageaccount
  --os-type Linux
```

2. Configure application settings:
```bash
az functionapp config appsettings set \
  --name myInsuranceClaimFunction \
  --resource-group myResourceGroup \
  --settings @appsettings.json
```

3. Deploy the function:
```bash
func azure functionapp publish myInsuranceClaimFunction
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint URL |
| `MODEL_DEPLOYMENT_NAME` | AI model deployment name (default: gpt-4.1-mini) |
| `COSMOS_ENDPOINT` | Cosmos DB account endpoint |
| `COSMOS_KEY` | Cosmos DB primary access key |
| `AZURE_CLIENT_ID` | Service principal client ID |
| `AZURE_CLIENT_SECRET` | Service principal secret |
| `AZURE_TENANT_ID` | Azure tenant ID |

### Function Configuration

The `host.json` file configures:
- Extension bundles version: `[4.*, 5.0.0)`
- Function timeout: 10 minutes
- Logging level: Information

## 🔍 Monitoring and Logging

The function includes comprehensive logging using Azure Functions' built-in logging:

- **Info level**: Normal operation flow
- **Error level**: Errors and exceptions
- **Orchestration events**: Agent creation, task assignment, results

Monitor logs in:
- Local development: Function runtime output
- Azure: Application Insights and Function logs

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Azure credentials in `local.settings.json`
   - Check service principal permissions

2. **Cosmos DB Connection Issues**
   - Verify endpoint and key configuration
   - Test with `/api/test-cosmos` endpoint

3. **AI Foundry Errors**
   - Confirm project endpoint URL
   - Verify model deployment name

4. **Timeout Issues**
   - Increase timeout in `host.json` if needed
   - Monitor function execution duration

## 📚 Dependencies

Key packages:
- `azure-functions`: Azure Functions runtime
- `azure-cosmos`: Cosmos DB client
- `azure-identity`: Azure authentication
- `semantic-kernel`: AI orchestration framework

## 🤝 Contributing

1. Follow Azure Functions best practices
2. Maintain async/await patterns
3. Include comprehensive error handling
4. Add tests for new functionality
5. Update documentation

## 📄 License

This project follows the same license as the parent repository.
