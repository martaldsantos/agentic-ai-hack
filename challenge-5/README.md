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
| **Claim Reviewer Agent** | Analyzes insurance claims and damage assessments | Cosmos DB data | Azure AI Agent Service + SK Plugins |
| **Policy Checker Agent** | Validates coverage against insurance policies | Azure AI Search connection | Azure AI Agent Service |
| **Risk Analyzer Agent** | Evaluates risk factors and provides recommendations | Cosmos DB data | Azure AI Agent Service + SK Plugins |
| **Master Orchestrator Agent** | Coordinates the three agents and synthesizes their outputs | Combined Plugins + Tools | Semantic Kernel Orchestration |

### Understanding Implementation Approaches: Azure AI Agent Service vs Semantic Kernel Integration

When building intelligent agents, you have two primary implementation approaches available in the Azure ecosystem. **Azure AI Agent Service with direct tool connections** provides a streamlined, low-code approach where agents are configured through the Azure AI Foundry portal with direct connections to Azure services like Azure AI Search, enabling rapid prototyping and deployment with built-in enterprise features like security, monitoring, and compliance. This approach is ideal for straightforward scenarios where agents need to access specific Azure services without complex custom logic. In contrast, **Azure AI Agents with Semantic Kernel integration** offers a more flexible, code-first approach that combines the enterprise-grade capabilities of Azure AI Agent Service with Semantic Kernel's powerful plugin framework. This hybrid approach allows developers to create custom plugins with complex business logic, advanced data processing capabilities, and sophisticated integrations (like our Cosmos DB plugin for retrieving structured claim data), while still benefiting from Azure's managed infrastructure and security features. The Semantic Kernel approach is particularly valuable when you need custom data transformations, complex orchestration patterns, or when integrating with *non-Azure* services.

## Exercise Guide - Time to Orchestrate!

## Part 1- Create your Semantic Kernel Orchestrator
Time to build your orchestrator! Please jump over to `orchestration.ipynb` file for a demonstration on how we will integrated our troop of agents to help us solve our pickle! 
This notebook is composed of only two cells of code. The first one will have in it 4 core components: 3 are dedicated to the creation of the 3 agents we have defined and the last piece is a `task` will be the orchestrator, that defines specific instructions to orchestrate the 3 agent.

In Semantic Kernel's Orchestration, [`tasks`](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python#invoke-the-orchestration-1) revolve around integrating AI capabilities with traditional programming through a **modular** architecture. Core tasks include creating and managing skills (collections of related AI functions), designing and using prompts for both natural language and code generation, orchestrating planners to break down goals into executable steps, and using connectors to interface with external services like APIs or databases. Developers also manage memory for context retention, handle input/output pipelines, and coordinate execution flows that combine multiple skills or plugins. These components enable building intelligent, context-aware agents that can reason, plan, and act autonomously.


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

   1. **Configure environment variables**: Before running the application, you need to add the following environment variables manually to your `.env` file or set them in your shell environment:

   ```bash
   CLAIM_REV_AGENT_ID=""
   RISK_ANALYZER_AGENT_ID=""
   POLICY_CHECKER_AGENT_ID=""
   ```

   > **📍 How to get Agent IDs from Azure AI Foundry:**
   > 1. Go to the [Azure AI Foundry portal](https://ai.azure.com)
   > 2. Navigate to your project
   > 3. In the left menu, select **Agents** under the "Build and customize" section
   > 4. You will see a list of all your created agents (Claim Reviewer, Risk Analyzer, Policy Checker)
   > 5. Click on each agent to view its details and copy the **Agent ID** from the agent's overview page
   > 6. Paste each Agent ID into the corresponding environment variable in your `.env` file

   2. Copy the .env file in root to the challenge-5 directory 

   3. Move to challenge-5 directory, create and activate a Python 3.11 virtual environment:

   ```bash
   cd challenge-5
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

   4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   5. Run the app:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

   6. Open a new terminal and test your new app with curl:

   ```bash
   CLAIM_ID="CL001"
   POLICY_NUMBER="LIAB-AUTO-001"
   curl -sS -X POST "http://127.0.0.1:8000/process-claim"   -H "Content-Type: application/json"   -d "{\"claimId\":\"$CLAIM_ID\",\"policyNumber\":\"$POLICY_NUMBER\"}" | jq
   ```

### Part 2.2 - Build and Run with Docker locally

> ⚠️ **Important**: Before running the Docker container, make sure to stop the FastAPI server from Part 2.1 (if still running) to free up port 8000. Press `Ctrl+C` in the terminal where `uvicorn` is running.

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

   > 📝 **After running the script**, copy the environment variables from the terminal output into your `.env` file. The output will look like:
   > ```
   > Environment Variables for .env file:
   > ============================================
   > AZURE_CLIENT_ID="<your-client-id>"
   > AZURE_CLIENT_SECRET="<your-client-secret>"
   > AZURE_TENANT_ID="<your-tenant-id>"
   > ```
   > Make sure to add these three variables to your `.env` file before proceeding.

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

Congratulations! You've successfully built a multi-agent orchestration system that coordinates three specialized insurance agents through a Master Orchestrator. Your system now handles complete insurance claim processing workflows using GroupChat orchestration patterns with Semantic Kernel.

**Key Achievements:**
- Implemented a GroupChat orchestration for  agent processing
- Created a Master Orchestrator that synthesizes outputs from multiple agents
- Built hybrid solutions combining Azure AI Agent Service with custom Semantic Kernel plugins
- Developed a production-ready framework for intelligent insurance claim processing
- Prepared the system for enterprise deployment to an Azure Container App with scalability and monitoring capabilities
