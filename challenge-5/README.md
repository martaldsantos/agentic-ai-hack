# Challenge 5: Agent Orchestration

**Expected Duration:** 60 minutes

## Introduction
By this point we have created **the three agents** and have seen how to evaluate and observe one specific agent. As you know, our use case is a bit more complex and, therefore, we will now create the rest of our architecture to actually make it a multi-agent architecture and not just 3 separate agents. The key word for this challenge will be **Orchestration**.

## What's orchestration and what types are there?
Orchestration in AI agent systems is the process of coordinating multiple specialized agents to work together on complex tasks that a single agent cannot handle alone. It helps break down problems, delegate work efficiently, and ensure that each part of a workflow is managed by the agent best suited for it. 

Some common Orchestration Patterns are:

| Pattern                  | Simple Description                                                                  |
|--------------------------|------------------------------------------------------------------------------------|
| Sequential Orchestration | Agents handle tasks one after the other in a fixed order, passing results along.   |
| Concurrent Orchestration | Many agents work at the same time on similar or different parts of a task.         |
| Group Chat Orchestration | Agents (and people, if needed) discuss and collaborate in a shared conversation.   |
| Handoff Orchestration    | Each agent works until it can’t continue, then hands off the task to another agent.|
| Magentic Orchestration   | A manager agent plans and assigns tasks on the fly as new needs and solutions arise.|

If you want deeper details into orchestration patterns click on this [link](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns?toc=%2Fazure%2Fdeveloper%2Fai%2Ftoc.json&bc=%2Fazure%2Fdeveloper%2Fai%2Fbreadcrumb%2Ftoc.json) to learn more.

Now you might be wondering... ok great... but, **how do I decide on an Orchestration Pattern?** The answer to that question is mostly related to your use case. 
Let's have a look at the 2 most common Orchestration patterns:

| Pattern                    | Flow                                   |
|----------------------------|----------------------------------------|
| Sequential Orchestration   | Agent A → Agent B → Agent C            |
| Concurrent Orchestration   | Agent A + Agent B + Agent C → Combine Results |

In `Sequential Orchestration` the Agents are dependent on a task performed from the previous agent. This is very common in workflows like document processing or step-by-step procedures. With `Concurrent Orchestration` the agents are not dependent on each other and therefore it makes this a great orchestration for parallel processing, multi-source research and so on.

## Let's come back to our use case...
We will have 3 agents that are each responsible for gathering and processing specialized information on different matters from different datasources in our knowledge base. In this challenge, we will create a 4th agent that is responsible for Orchestrating these 3 agents and create the final output that we need. Please have a look at the table underneath and review how we have created our 3 agents.

| Agent | Function | Data Source/Technology | Implementation |
|-------|----------|----------------------|----------------|
| **Claim Reviewer Agent** | Analyzes insurance claims and damage assessments | Cosmos DB data | Azure OpenAI + Custom Plugins |
| **Policy Checker Agent** | Validates coverage against insurance policies | Azure AI Search connection | Azure OpenAI |
| **Risk Analyzer Agent** | Evaluates risk factors and provides recommendations | Cosmos DB data | Azure OpenAI + Custom Plugins |
| **Master Orchestrator** | Coordinates the three agents and synthesizes their outputs | Combined Tools | Microsoft Agent Framework Concurrent Orchestration |

### Understanding Implementation Approaches: Microsoft Agent Framework

**Microsoft Agent Framework** provides a modern, code-first approach to building and orchestrating AI agents. The framework offers powerful concurrent orchestration capabilities through the `ConcurrentBuilder` class, which enables multiple agents to work in parallel on the same task. This approach is ideal for scenarios where you need:

- **True Parallelism**: Multiple agents analyzing the same input simultaneously from different perspectives
- **Ensemble Reasoning**: Combining insights from multiple specialized agents for comprehensive analysis
- **Flexible Integration**: Easy integration with Azure OpenAI, custom tools, and data sources
- **Event-based Results**: Streaming results as they become available from each agent

The Agent Framework approach is particularly valuable when you need custom orchestration patterns, sophisticated error handling, and when integrating with various data sources (like our Cosmos DB plugin for retrieving structured claim data).

## Exercise Guide - Time to Orchestrate!

## Part 1- Create your Microsoft Agent Framework Orchestrator
Time to build your orchestrator! Please jump over to `orchestration.ipynb` file for a demonstration on how we will integrate our troop of agents to help us solve our challenge! 

This notebook demonstrates concurrent orchestration using Microsoft Agent Framework. The implementation includes:

1. **Agent Creation**: Three specialized agents (Claim Reviewer, Risk Analyzer, Policy Checker) are created using the Azure OpenAI chat client
2. **Concurrent Workflow**: The `ConcurrentBuilder` class creates a workflow that runs all three agents in parallel
3. **Task Distribution**: Each agent receives the same task but applies their specialized perspective
4. **Result Aggregation**: Results are collected via an event stream as agents complete their analysis
5. **Final Decision**: An approver agent synthesizes all analyses to provide the final claim decision

In Microsoft Agent Framework, concurrent orchestration enables true parallel execution where multiple agents work simultaneously on the same problem, each applying their domain expertise. This is achieved through the `ConcurrentBuilder` which fans out the task to all participating agents and aggregates their responses.


## Part 2 - Now onto automation!

Time to create our endpoint! As seen on Part 1, this is a use case that can be run by providing our system the claim-number and policy-number and it will trigger the orchestration. In practical terms, we will be inputing and outputing json strings from our API. The response will contain a binary decision (APPROVED/NOT APPROVED) along with the justification from the agents.

```bash
POST /process-claim

Request body (application/json):
{
  "claimId": "string",
  "policyNumber": "string"
}

Response body (application/json):
{
  "decision": "string",
  "justification": "string"
}
```

### Part 2.1 Quick start

   1. **Install required packages**: Before running the application, install the Microsoft Agent Framework and required dependencies:

   ```bash
   pip install azure-identity agent-framework --pre
   ```
   
   Note: The `--pre` flag is required as Microsoft Agent Framework is currently in preview.

   2. **Configure environment variables**: Add the following environment variables to your `.env` file or set them in your shell environment:

   ```bash
   AZURE_OPENAI_ENDPOINT=""
   AZURE_OPENAI_KEY=""
   AZURE_OPENAI_DEPLOYMENT_NAME=""
   AZURE_OPENAI_API_VERSION="2024-10-01-preview"
   COSMOS_ENDPOINT=""
   COSMOS_KEY=""
   ```

   3. Copy the .env file in root to the challenge-5 directory 

   4. Move to challenge-5 directory, create and activate a Python 3.11 virtual environment:

   ```bash
   cd challenge-5
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

   5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   6. Run the app:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

   7. Open a new terminal and test your new app with curl:

   ```bash
   CLAIM_ID="CL001"
   POLICY_NUMBER="LIAB-AUTO-001"
   curl -sS -X POST "http://127.0.0.1:8000/process-claim"   -H "Content-Type: application/json"   -d "{\"claimId\":\"$CLAIM_ID\",\"policyNumber\":\"$POLICY_NUMBER\"}" | jq
   ```

### Part 2.2 - Build and Run with Docker locally

1. Build the Docker image (make sure you are still on the challenge-5 directory):

   ```bash
   docker build -t claim-manager:latest .
   ```

2. Run the Docker container:

   Create the Service Principal and assign role:

   ```bash
   cd challenge-5 && ./create-service-principal.sh
   ```
   If you run into any permission errors, first run `chmod +x challenge-5/create-service-principal.sh`

   Copy the outputed variables and paste them in your local `.env` file.
   Then, it's time to run the container with the necessary environment variables:

   ```bash
   # Source the .env file and run the Docker container
   set -a && source .env && set +a && docker run -p 8000:8000 \
      -e AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
      -e AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
      -e AZURE_TENANT_ID="$AZURE_TENANT_ID" \
      -e CLAIM_REV_AGENT_ID="$CLAIM_REV_AGENT_ID" \
      -e RISK_ANALYZER_AGENT_ID="$RISK_ANALYZER_AGENT_ID" \
      -e POLICY_CHECKER_AGENT_ID="$POLICY_CHECKER_AGENT_ID" \
      -e AI_FOUNDRY_PROJECT_ENDPOINT="$AI_FOUNDRY_PROJECT_ENDPOINT" \
      -e MODEL_DEPLOYMENT_NAME="$MODEL_DEPLOYMENT_NAME" \
      -e COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
      -e COSMOS_KEY="$COSMOS_KEY" \
      -e AZURE_AI_CONNECTION_ID="$AZURE_AI_CONNECTION_ID" \
      -e AZURE_AI_SEARCH_INDEX_NAME="$AZURE_AI_SEARCH_INDEX_NAME" \
      -e SEARCH_SERVICE_NAME="$SEARCH_SERVICE_NAME" \
      -e SEARCH_SERVICE_ENDPOINT="$SEARCH_SERVICE_ENDPOINT" \
      -e SEARCH_ADMIN_KEY="$SEARCH_ADMIN_KEY" \
      -e AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
      -e AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
      -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
      claim-manager
   ```

   3. Open a new terminal and test your docker with curl:

   ```bash
   CLAIM_ID="CL001"
   POLICY_NUMBER="LIAB-AUTO-001"
   curl -sS -X POST "http://127.0.0.1:8000/process-claim"   -H "Content-Type: application/json"   -d "{\"claimId\":\"$CLAIM_ID\",\"policyNumber\":\"$POLICY_NUMBER\"}" | jq
   ```

### Part 2.3 - Push to Azure Container Registry

1. Source environment variables and tag the Docker image:

   ```bash
   # Source environment variables from .env file
   set -a && source .env && set +a
   docker tag claim-manager:latest $ACR_NAME.azurecr.io/claim-manager:latest
   ```

2. Log in to Azure Container Registry:

   ```bash
   # ACR credentials are already loaded from .env file
   docker login $ACR_NAME.azurecr.io --username $ACR_USERNAME --password $ACR_PASSWORD
   ```

3. Push the Docker image:

   ```bash
   docker push $ACR_NAME.azurecr.io/claim-manager:latest
   ```

### Part 2.4 Run in Azure Container Apps


Create environment and container app using the pushed image and set the same environment variables as above.

1. Create the Container App environment (replace the first 3 lines with the appropriate credentials). Don't worry, it should take about 10 minutes to run:

   ```bash
   export RESOURCE_GROUP="<your-resource-group>"
   export LOCATION="<your-location>"
   export ENV_NAME="<your-env-name>"
   az containerapp env create --name $ENV_NAME --resource-group $RESOURCE_GROUP --location $LOCATION
   ```

2. Create a unique name for your app and create your Azure Container App:

   ```bash
   APP_NAME="<your-app-name>"
   az containerapp create --name $APP_NAME --resource-group $RESOURCE_GROUP \
   --environment $ENV_NAME --image $ACR_NAME.azurecr.io/claim-manager:latest \
   --cpu 0.5 --memory 1.0Gi --min-replicas 1 --max-replicas 1 \
   --ingress 'external' --target-port 8000 \
   --registry-server $ACR_NAME.azurecr.io \
   --registry-username $ACR_USERNAME --registry-password $ACR_PASSWORD \
   --env-vars COSMOS_ENDPOINT="$COSMOS_ENDPOINT" COSMOS_KEY="$COSMOS_KEY" \
   AI_FOUNDRY_PROJECT_ENDPOINT="$AI_FOUNDRY_PROJECT_ENDPOINT" AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
   AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
   CLAIM_REV_AGENT_ID="$CLAIM_REV_AGENT_ID" \
   RISK_ANALYZER_AGENT_ID="$RISK_ANALYZER_AGENT_ID" \
   POLICY_CHECKER_AGENT_ID="$POLICY_CHECKER_AGENT_ID" 

   ```

   Give permissions to the container app to access resources using a system assigned managed identity:

   ```bash
   az containerapp identity assign \
   --name $APP_NAME \
   --resource-group $RESOURCE_GROUP \
   --system-assigned

   PRINCIPAL_ID=$(az containerapp identity show \
   --name $APP_NAME \
   --resource-group $RESOURCE_GROUP \
   --query principalId --output tsv)

   az role assignment create \
   --assignee $PRINCIPAL_ID \
   --role "Cognitive Services User" \
   --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
   ```


3. Now it's time to test your container app directly:

   ```bash
   CLAIM_ID="CL001"
   POLICY_NUMBER="LIAB-AUTO-001"
   CLAIM_MANAGER_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
   curl -sS -X POST "https://$CLAIM_MANAGER_URL/process-claim"   -H "Content-Type: application/json"   -d "{\"claimId\":\"$CLAIM_ID\",\"policyNumber\":\"$POLICY_NUMBER\"}" | jq
   ```


   ## 🎯 Conclusion

Congratulations! You've successfully built a multi-agent orchestration system using Microsoft Agent Framework that coordinates three specialized insurance agents through concurrent orchestration. Your system now handles complete insurance claim processing workflows with true parallel execution.

**Key Achievements:**
- Implemented concurrent orchestration using Microsoft Agent Framework's ConcurrentBuilder
- Created a Master Orchestrator that synthesizes outputs from multiple agents running in parallel
- Built hybrid solutions combining Azure OpenAI with custom tool plugins
- Developed a production-ready framework for intelligent insurance claim processing
- Prepared the system for enterprise deployment to an Azure Container App with scalability and monitoring capabilities
- Leveraged modern agent orchestration patterns for efficient multi-perspective analysis
