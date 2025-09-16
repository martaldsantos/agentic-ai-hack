import asyncio
import os
import time
import asyncio
import json
from typing import Dict, Any
from datetime import timedelta
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import (
    AzureAIAgent, 
    ConcurrentOrchestration
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from azure.ai.agents.models import AzureAISearchQueryType, AzureAISearchTool, ListSortOrder, MessageRole
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from azure.identity import AzureCliCredential  # async credential
from typing import Annotated
from semantic_kernel.functions import kernel_function

# Import the Cosmos DB plugin
from dotenv import load_dotenv

load_dotenv(override=True)  

class CosmosDBPlugin:
    """
    A production-ready Cosmos DB plugin that connects to real Azure Cosmos DB.
    This plugin retrieves actual JSON documents from your database.
    """
    
    def __init__(self, endpoint: str = None, key: str = None, database_name: str = "MyDatabase", container_name: str = "MyContainer"):
        """
        Initialize the Cosmos DB plugin with connection details.
        For production, use environment variables or Azure Key Vault for credentials.
        """
        self.endpoint = endpoint or os.environ.get("COSMOS_ENDPOINT")
        self.key = key or os.environ.get("COSMOS_KEY") 
        self.database_name = "insurance_claims"
        self.container_name = "crash_reports"
    
    def _get_cosmos_client(self):
        """Create and return a Cosmos DB client."""
        if not self.endpoint or not self.key:
            raise Exception("Cosmos DB endpoint and key must be configured. Please set COSMOS_ENDPOINT and COSMOS_KEY environment variables.")
        
        try:
            from azure.cosmos import CosmosClient
            return CosmosClient(self.endpoint, self.key)
        except ImportError:
            raise ImportError("azure-cosmos package not installed. Run: pip install azure-cosmos")
        except Exception as e:
            raise Exception(f"Failed to create Cosmos DB client: {str(e)}")
    
    @kernel_function(description="Test Cosmos DB connection and list available claims")
    def test_connection(self) -> Annotated[str, "Connection test result and available claims"]:
        """Test the Cosmos DB connection and show what claims are available."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Test with a simple query to get all claim IDs
            query = "SELECT c.claim_id, c.id FROM c"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=10  # Limit to first 10 for testing
            ))
            
            if not items:
                return f"✅ Connection successful but no documents found in container '{self.container_name}'"
            
            claim_ids = [item.get('claim_id', 'N/A') for item in items]
            result = {
                "connection_status": "SUCCESS",
                "database": self.database_name,
                "container": self.container_name,
                "documents_found": len(items),
                "available_claim_ids": claim_ids
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"❌ Connection test failed: {str(e)}"
    
    @kernel_function(description="Retrieve a document by claim_id from Cosmos DB using cross-partition query")
    def get_document_by_claim_id(
        self, 
        claim_id: Annotated[str, "The claim_id to retrieve (not the partition key)"]
    ) -> Annotated[str, "JSON document from Cosmos DB"]:
        """Retrieve a document by its claim_id using a cross-partition query."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Use SQL query to find document by claim_id across all partitions
            query = "SELECT * FROM c WHERE c.claim_id = @claim_id"
            parameters = [{"name": "@claim_id", "value": claim_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=1  # We expect only one document with this claim_id
            ))
            
            if not items:
                # Try to find what claim IDs actually exist
                all_claims_query = "SELECT c.claim_id FROM c"
                all_items = list(container.query_items(
                    query=all_claims_query,
                    enable_cross_partition_query=True,
                    max_item_count=10
                ))
                available_ids = [item.get('claim_id', 'N/A') for item in all_items]
                
                return f"❌ No document found with claim_id '{claim_id}' in container '{self.container_name}'.\n\nAvailable claim IDs: {available_ids}\n\nPlease verify the claim ID exists in the database."
            
            # Return the first (and should be only) matching document
            document = items[0]
            return json.dumps(document, indent=2, ensure_ascii=False)
            
        except Exception as e:
            error_msg = str(e)
            if "endpoint and key must be configured" in error_msg:
                return f"❌ Cosmos DB not configured. Please set COSMOS_ENDPOINT and COSMOS_KEY environment variables. Error: {error_msg}"
            elif "Unauthorized" in error_msg or "401" in error_msg:
                return f"❌ Authentication failed. Please check your Cosmos DB credentials. Error: {error_msg}"
            elif "Forbidden" in error_msg or "403" in error_msg:
                return f"❌ Access denied. Please check your Cosmos DB permissions. Error: {error_msg}"
            elif "azure-cosmos package not installed" in error_msg:
                return f"❌ Missing dependency. Please run: pip install azure-cosmos"
            else:
                return f"❌ Error retrieving document by claim_id '{claim_id}': {error_msg}"
    
    @kernel_function(description="Retrieve a JSON document by partition key and document ID from Cosmos DB")
    def get_document_by_id(
        self, 
        document_id: Annotated[str, "The document ID to retrieve"],
        partition_key: Annotated[str, "The partition key value (optional, will use cross-partition query if not provided)"] = None
    ) -> Annotated[str, "JSON document from Cosmos DB"]:
        """Retrieve a specific document by its ID and optionally partition key from Cosmos DB."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            if partition_key:
                # Direct read using partition key - most efficient
                item = container.read_item(item=document_id, partition_key=partition_key)
                return json.dumps(item, indent=2, ensure_ascii=False)
            else:
                # Cross-partition query when partition key is unknown
                query = "SELECT * FROM c WHERE c.id = @document_id"
                parameters = [{"name": "@document_id", "value": document_id}]
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=1
                ))
                
                if not items:
                    return f"❌ Document with ID '{document_id}' not found in container '{self.container_name}'"
                
                return json.dumps(items[0], indent=2, ensure_ascii=False)
            
        except Exception as e:
            error_msg = str(e)
            if "NotFound" in error_msg or "404" in error_msg:
                return f"❌ Document with ID '{document_id}' not found in container '{self.container_name}'"
            elif "Unauthorized" in error_msg or "401" in error_msg:
                return f"❌ Authentication failed. Please check your Cosmos DB credentials."
            elif "Forbidden" in error_msg or "403" in error_msg:
                return f"❌ Access denied. Please check your Cosmos DB permissions."
            else:
                return f"❌ Error retrieving document: {error_msg}"
    
    @kernel_function(description="Query documents with a custom SQL query in Cosmos DB")
    def query_documents(
        self, 
        sql_query: Annotated[str, "SQL query to execute (e.g., 'SELECT * FROM c WHERE c.category = \"electronics\"')"]
    ) -> Annotated[str, "Query results as JSON"]:
        """Execute a custom SQL query against the Cosmos DB container."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Execute the query
            items = list(container.query_items(
                query=sql_query,
                enable_cross_partition_query=True  # Enable if your query spans partitions
            ))
            
            if not items:
                return f"🔍 No documents found matching query: {sql_query}"
            
            # Return results as formatted JSON
            result = {
                "query": sql_query,
                "count": len(items),
                "results": items
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            error_msg = str(e)
            if "Syntax error" in error_msg:
                return f"❌ SQL syntax error in query: {sql_query}\nError: {error_msg}"
            else:
                return f"❌ Error executing query: {error_msg}"
    
    @kernel_function(description="Get container information and statistics")
    def get_container_info(self) -> Annotated[str, "Container information and statistics"]:
        """Get information about the Cosmos DB container."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Get container properties
            container_props = container.read()
            
            # Get approximate document count (this is an estimate)
            count_query = "SELECT VALUE COUNT(1) FROM c"
            count_items = list(container.query_items(
                query=count_query,
                enable_cross_partition_query=True
            ))
            document_count = count_items[0] if count_items else "Unknown"
            
            info = {
                "database": self.database_name,
                "container": self.container_name,
                "partition_key": container_props.get("partitionKey", {}).get("paths", ["Unknown"]),
                "approximate_document_count": document_count,
                "indexing_policy": container_props.get("indexingPolicy", {}).get("indexingMode", "Unknown")
            }
            
            return json.dumps(info, indent=2)
            
        except Exception as e:
            return f"❌ Error getting container info: {str(e)}"
    
    @kernel_function(description="List recent documents (up to 100) from Cosmos DB")
    def list_recent_documents(
        self, 
        limit: Annotated[int, "Maximum number of documents to return (default: 10, max: 100)"] = 10
    ) -> Annotated[str, "List of recent documents"]:
        """List recent documents from the container."""
        try:
            # Ensure limit is within bounds
            limit = max(1, min(limit, 100))
            
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Query for documents (ordered by _ts if available)
            query = f"SELECT TOP {limit} * FROM c ORDER BY c._ts DESC"
            
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return "📭 No documents found in the container"
            
            result = {
                "container": self.container_name,
                "count": len(items),
                "documents": items
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"❌ Error listing documents: {str(e)}"
    
    @kernel_function(description="Search documents by field value")
    def search_by_field(
        self, 
        field_name: Annotated[str, "The field name to search in (e.g., 'name', 'category', 'status')"],
        field_value: Annotated[str, "The value to search for"]
    ) -> Annotated[str, "Documents matching the search criteria"]:
        """Search for documents where a specific field matches a value."""
        try:
            client = self._get_cosmos_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Use parameterized query for better security and performance
            query = f"SELECT * FROM c WHERE c.{field_name} = @field_value"
            parameters = [{"name": "@field_value", "value": field_value}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return f"🔍 No documents found where {field_name} = '{field_value}'"
            
            result = {
                "search_criteria": f"{field_name} = '{field_value}'",
                "count": len(items),
                "documents": items
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"❌ Error searching documents: {str(e)}"

async def create_specialized_agents():
    """Create our specialized insurance processing agents using Semantic Kernel."""
    
    print("🔧 Creating specialized insurance agents...")
    
    # Create Cosmos DB plugin instances for different agents
    cosmos_plugin_claims = CosmosDBPlugin()
    cosmos_plugin_risk = CosmosDBPlugin()
    
    # Get environment variables
    endpoint = os.environ.get("AI_FOUNDRY_PROJECT_ENDPOINT")
    model_deployment = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")
    
    agents = {}
    
    async with DefaultAzureCredential() as creds:
        client = AzureAIAgent.create_client(credential=creds, endpoint=endpoint)
        
        # Create Claim Reviewer Agent with Cosmos DB access
        print("🔍 Creating Claim Reviewer Agent...")
        claim_reviewer_definition = await client.agents.create_agent(
            model=model_deployment,
            name="ClaimReviewer",
            description="Expert Insurance Claim Reviewer Agent specialized in analyzing and validating insurance claims",
            instructions="""You are an expert Insurance Claim Reviewer Agent specialized in analyzing and validating insurance claims. 
            Your primary responsibilities include:
            1. Use the Cosmos DB plugin to retrieve claim data by claim_id, then:
            2.Review all claim details (dates, amounts, descriptions).
            3. Verify completeness of documentation and supporting evidence.
            4. Analyze damage assessments and cost estimates for reasonableness.
            5. Validate claim details against policy requirements.
            6. Identify inconsistencies, missing info, or red flags.
            7. Provide a detailed assessment with specific recommendations.

            **Response Format**:

            A short paragraph description if the CLAIM STATUS is: VALID / QUESTIONABLE / INVALID ; Analysis: Summary of findings by component; Any missing Info / Concerns: List of issues or gaps;
            Next Steps: Clear, actionable recommendations
    """
        )
        
        claim_reviewer_agent = AzureAIAgent(
            client=client,
            definition=claim_reviewer_definition,
            plugins=[cosmos_plugin_claims]
        )
        
        # Create Risk Analyzer Agent with Cosmos DB access
        print("⚠️ Creating Risk Analyzer Agent...")
        risk_analyzer_definition = await client.agents.create_agent(
            model=model_deployment,
            name="RiskAnalyzer",
            instructions="""You are the Risk Analysis Agent. Your role is to evaluate the authenticity of insurance claims and detect potential fraud using available claim data.
            Core Functions:
            - Analyze historical and current claim data
            - Identify suspicious patterns, inconsistencies, or anomalies
            - Detect fraud indicators
            - Assess claim credibility and assign a risk score
            - Recommend follow-up actions if warranted

            Assessment Guidelines:
            - Use the Cosmos DB plugin to access claim records
            - Look for unusual timing, inconsistent descriptions, irregular amounts, or clustering
            - Check for repeat claim behavior or geographic overlaps
            - Assess the overall risk profile of each claim

            Fraud Indicators to Watch For:
            - Claims with irregular timing
            - Contradictory or vague damage descriptions
            - Unusual or repetitive claim amounts
            - Multiple recent claims under same or related profiles
            - Geographic or temporal clustering of incidents

            Output Format:
            - Risk Level: LOW / MEDIUM / HIGH
            - Risk Analysis: Brief summary of findings
            - Indicators: List of specific fraud signals (if any)
            - Risk Score: 1–10 scale
            - Recommendation: Investigate / Monitor / No action needed

            Base all assessments strictly on the available claim data. Use structured reasoning and avoid assumptions beyond the data.
            """,
        )
        
        risk_analyzer_agent = AzureAIAgent(
            client=client,
            definition=risk_analyzer_definition,
            plugins=[cosmos_plugin_risk]
        )
        
        ai_agent_settings = AzureAIAgentSettings(model_deployment_name= os.environ.get("MODEL_DEPLOYMENT_NAME"), azure_ai_search_connection_id=os.environ.get("AZURE_AI_AGENT_ENDPOINT"))        
        ai_search = AzureAISearchTool(
            index_connection_id=os.environ.get("AZURE_AI_CONNECTION_ID"), 
            index_name="insurance-documents-index"
        )

        # Create agent definition
        policy_agent_definition = await client.agents.create_agent(
            name="PolicyChecker", 
            model=os.environ.get("MODEL_DEPLOYMENT_NAME"),
            instructions=""""
            You are the Policy Checker Agent.

            Your task is to summarize a policy based on policy number.

            Instructions:
            - Do not analyze claim details directly.
            - Use your search tool to locate policy documents by policy number or policy type.
            - Identify relevant exclusions, limits, and deductibles.
            - Base your determination only on the contents of the retrieved policy.

            Output Format:
            - Policy Number: [Policy number]
            - Main important details
            - Reference and quote specific policy sections that support your determination.
            - Clearly explain how the policy language leads to your conclusion.

            Be precise, objective, and rely solely on the policy content.
            """,
            tools=ai_search.definitions,
            tool_resources=ai_search.resources,
            headers={"x-ms-enable-preview": "true"},
        )

        policy_checker_agent = AzureAIAgent(
            client=client, 
            definition=policy_agent_definition
        )

        agents = {
            'claim_reviewer': claim_reviewer_agent,
            'risk_analyzer': risk_analyzer_agent,
            'policy_checker': policy_checker_agent
        }
        
        print("✅ All specialized agents created/loaded successfully!")
        return agents, client

async def run_insurance_claim_orchestration(claim_id: str, policy_number: str):
    """Orchestrate multiple agents to process an insurance claim concurrently using only the claim ID."""
    
    print(f"🚀 Starting Concurrent Insurance Claim Processing Orchestration")
    print(f"{'='*80}")
    
    # Create our specialized agents
    agents, client = await create_specialized_agents()
    
    # Create concurrent orchestration with all three agents
    orchestration = ConcurrentOrchestration(
        members=[agents['claim_reviewer'], agents['risk_analyzer'], agents['policy_checker']]
    )
    
    # Create and start runtime
    runtime = InProcessRuntime()
    runtime.start()
    
    try:        
        # Create task that instructs agents to retrieve claim details first
        task = f"""Analyze the insurance claim with ID: {claim_id} or the policy number {policy_number} and come back with a critical solution for if the credit should be approved.

CRITICAL: ALL AGENTS MUST USE THEIR AVAILABLE TOOLS TO RETRIEVE INFORMATION

AGENT-SPECIFIC INSTRUCTIONS:

Claim Reviewer Agent: 
- MUST USE: get_document_by_claim_id("{claim_id}") to retrieve claim details
- Review all claim documentation and assess completeness
- Validate damage estimates and repair costs against retrieved data
- Check for proper evidence and documentation in the claim data
- Cross-reference claim amounts with industry standards
- Provide VALID/QUESTIONABLE/INVALID determination with detailed reasoning

Risk Analyzer Agent:
- MUST USE: get_document_by_claim_id("{claim_id}") to retrieve claim data
- Analyze the retrieved data for fraud indicators and suspicious patterns
- Assess claim authenticity and credibility based on actual claim details
- Check for unusual timing, amounts, or circumstances in the data
- Look for inconsistencies between different parts of the claim
- Provide LOW/MEDIUM/HIGH risk assessment with specific evidence

Policy Checker Agent (policy_checker_agent):
- YOU DO NOT NEED TO LOOK INTO CLAIMS!
- MUST USE: Your search capabilities to find relevant policy documents by policy number ("{policy_number}") or type found in the claim data
- Search for policy documents using policy numbers
- Identify relevant exclusions, limits, or deductibles from actual policy documents
- Provide COVERED/NOT COVERED/PARTIAL COVERAGE determination with policy references
- Quote specific policy sections that support your determination

IMPORTANT: Each agent MUST actively use their tools to retrieve and analyze actual data. 
Do not provide generic responses - base your analysis on the specific claim data and policy documents retrieved through your tools.
"""
        # Invoke concurrent orchestration
        orchestration_result = await orchestration.invoke(
            task=task,
            runtime=runtime
        )
        
        # Get results from all agents
        results = await orchestration_result.get(timeout=300)  # 5 minute timeout
        
        print(f"\n🎉 All agents completed their analysis!")
        print(f"{'─'*60}")
        
        # Display individual results
        for i, result in enumerate(results, 1):
            agent_name = result.name if hasattr(result, 'name') else f"Agent {i}"
            content = str(result.content)
            print(f"\n🤖 {agent_name} Analysis:")
            print(f"{'─'*40}")
            print(content)
        
        # Create comprehensive analysis report
        comprehensive_analysis = f"""

{chr(10).join([f"### {result.name} Assessment:{chr(10)}{chr(10)}{result.content}{chr(10)}" for result in results])}

"""
        
        print(f"\n✅ Concurrent Insurance Claim Orchestration Complete!")
        return comprehensive_analysis
        
    except Exception as e:
        print(f"❌ Error during orchestration: {str(e)}")
        raise
        
    finally:
        await runtime.stop_when_idle()
        print(f"\n🧹 Orchestration cleanup complete.")

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.post("/orchestrate")
async def orchestrate_claim(
    claim_id: str = Query(..., description="Claim ID to process"),
    policy_number: str = Query(..., description="Policy number to process")
):
    try:
        result = await run_insurance_claim_orchestration(claim_id, policy_number)
        return JSONResponse(content={"analysis": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import os
    import sys
    # Optionally allow running as script or API
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        uvicorn.run("orchestration:app", host="0.0.0.0", port=8000, reload=True)
    else:
        # Get claim ID and policy number from environment variables or use defaults
        claim_id = os.environ.get("CLAIM_ID", "CL001")  # Use a real claim ID
        policy_number = os.environ.get("POLICY_NUMBER", "LIAB-AUTO-001")  # Use a real policy number
        print(f"Processing Claim ID: {claim_id}, Policy Number: {policy_number}")
        asyncio.run(run_insurance_claim_orchestration(claim_id, policy_number))