from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
from azure.identity import DefaultAzureCredential, AzureCliCredential
from agent_framework import ChatMessage, ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient
import asyncio
import os
import json
import re

from agents.cosmos_tools import get_document_by_claim_id
from dotenv import load_dotenv

load_dotenv(override=True)  


class ClaimRequest(BaseModel):
    claimId: str
    policyNumber: str


app = FastAPI(title="Claim API", version="0.1.0")

async def get_specialized_agents() -> Dict[str, Any]:
    """Get our specialized insurance processing agents using Microsoft Agent Framework."""
    
    print("🔧 Creating specialized insurance agents...")
    
    # Get environment variables
    # Try to use DefaultAzureCredential first, fall back to AzureCliCredential
    try:
        credential = DefaultAzureCredential()
    except Exception as e:
        print(f"⚠️  DefaultAzureCredential failed: {str(e)}, falling back to AzureCliCredential")
        credential = AzureCliCredential()
    
    # Create Azure OpenAI chat client
    # Agent Framework uses environment variables or explicit configuration
    chat_client = AzureOpenAIChatClient(credential=credential)
    
    # Create Claim Reviewer Agent with Cosmos DB access
    print("🔍 Creating Claim Reviewer Agent...")
    claim_reviewer_agent = chat_client.create_agent(
        instructions="""You are an expert Insurance Claim Reviewer Agent specialized in analyzing and validating insurance claims. 
        Your primary responsibilities include:
        1. Use the get_document_by_claim_id function to retrieve claim data by claim_id, then:
        2. Review all claim details (dates, amounts, descriptions).
        3. Verify completeness of documentation and supporting evidence.
        4. Analyze damage assessments and cost estimates for reasonableness.
        5. Validate claim details against policy requirements.
        6. Identify inconsistencies, missing info, or red flags.
        7. Provide a detailed assessment with specific recommendations.

        **Response Format**:
        A short paragraph description if the CLAIM STATUS is: VALID / QUESTIONABLE / INVALID ; Analysis: Summary of findings by component; Any missing Info / Concerns: List of issues or gaps;
        Next Steps: Clear, actionable recommendations
        """,
        name="ClaimReviewer",
        tools=[get_document_by_claim_id]
    )

    # Create Risk Analyzer Agent with Cosmos DB access
    print("⚠️ Creating Risk Analyzer Agent...")
    risk_analyzer_agent = chat_client.create_agent(
        instructions="""You are the Risk Analysis Agent. Your role is to evaluate the authenticity of insurance claims and detect potential fraud using available claim data.
        Core Functions:
        - Analyze historical and current claim data
        - Identify suspicious patterns, inconsistencies, or anomalies
        - Detect fraud indicators
        - Assess claim credibility and assign a risk score
        - Recommend follow-up actions if warranted

        Assessment Guidelines:
        - Use the get_document_by_claim_id function to access claim records
        - Look for unusual timing, inconsistent descriptions, irregular amounts, or clustering
        - Check for repeat claim behavior or geographic overlaps
        - Assess the overall risk profile of each claim

        Output Format:
        - Risk Level: LOW / MEDIUM / HIGH
        - Risk Analysis: Brief summary of findings
        - Indicators: List of specific fraud signals (if any)
        - Risk Score: 1–10 scale
        - Recommendation: Investigate / Monitor / No action needed
        """,
        name="RiskAnalyzer",
        tools=[get_document_by_claim_id]
    )

    # Create Policy Checker Agent
    print("📋 Creating Policy Checker Agent...")
    policy_checker_agent = chat_client.create_agent(
        instructions="""You are the Policy Checker Agent.

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
        """,
        name="PolicyChecker",
    )
    
    # Create Approver Agent for final decision
    print("✅ Creating Approver Agent...")
    approver_agent = chat_client.create_agent(
        instructions="""You must analyze and process insurance claims based on the information provided by specialized agents.
        You will provide a final decision on whether to approve or deny the claim, along with a detailed justification. 
        Your decision must be based on the specific findings and assessments from the Claim Reviewer, Risk Analyzer, and Policy Checker agents. 
        You must only approve if the claim is valid, risk is low or medium, and the policy covers the claim.
        Say 'APPROVED' or 'DENIED' followed by your reasoning.
        Format your response as a JSON object with 'decision' and 'justification' fields.
        """,
        name="ApproverAgent",
    )

    agents = {
        'claim_reviewer': claim_reviewer_agent,
        'risk_analyzer': risk_analyzer_agent,
        'policy_checker': policy_checker_agent,
        'approver': approver_agent,
        'chat_client': chat_client
    }

    print("✅ All specialized agents created successfully!")
    return agents

async def run_insurance_claim_orchestration(claim_id: str, policy_number: str):
    """Orchestrate multiple agents to process an insurance claim concurrently using Microsoft Agent Framework."""

    print(f"🚀 Starting Concurrent Insurance Claim Processing Orchestration for claim ID: {claim_id} and policy number: {policy_number}")
    print(f"{'='*80}")
    
    # Create our specialized agents
    agents = await get_specialized_agents()
    
    # Create concurrent orchestration with the three analysis agents
    workflow = ConcurrentBuilder().participants([
        agents['claim_reviewer'],
        agents['risk_analyzer'],
        agents['policy_checker']
    ]).build()
    
    try:        
        # Create task that instructs agents to retrieve claim details first
        task = f"""Analyze the insurance claim with ID: {claim_id} and policy number {policy_number}.

AGENT-SPECIFIC INSTRUCTIONS:

Claim Reviewer Agent: 
- Use get_document_by_claim_id("{claim_id}") to retrieve claim details
- Review all claim documentation and assess completeness
- Provide VALID/QUESTIONABLE/INVALID determination with detailed reasoning

Risk Analyzer Agent:
- Use get_document_by_claim_id("{claim_id}") to retrieve claim data
- Analyze for fraud indicators and suspicious patterns
- Provide LOW/MEDIUM/HIGH risk assessment with specific evidence

Policy Checker Agent:
- Search for policy documents using policy number: "{policy_number}"
- Identify relevant exclusions, limits, or deductibles
- Provide COVERED/NOT COVERED/PARTIAL COVERAGE determination

Each agent must use their tools to retrieve and analyze actual data.
"""
        
        # Run concurrent orchestration
        print(f"\n🔄 Invoking concurrent orchestration...")
        events = await workflow.run(task)
        
        # Get outputs from the workflow
        outputs = events.get_outputs()
        
        # Collect results from all agents
        results = []
        if outputs:
            for output in outputs:
                # Output is a list of ChatMessage objects
                messages = output if isinstance(output, list) else [output]
                for msg in messages:
                    if hasattr(msg, 'text') and msg.text:
                        results.append(msg.text)
                        author = getattr(msg, 'author_name', 'Agent')
                        print(f"# {author} Response\n{msg.text}")
        
        # Now have the approver agent make final decision based on all analyses
        print(f"\n✅ Concurrent analysis complete. Running approver agent...")
        
        # Compile all analysis results for the approver
        all_analyses = "\n\n".join([f"Agent Analysis:\n{result}" for result in results])
        
        approver_task = f"""Based on the following analyses from specialized agents, provide a final decision on the insurance claim {claim_id}:

{all_analyses}

Provide your decision as a JSON object with 'decision' (APPROVED or DENIED) and 'justification' fields."""
        
        # Create a separate workflow for the approver agent
        approver_workflow = ConcurrentBuilder().participants([agents['approver']]).build()
        approver_events = await approver_workflow.run(approver_task)
        
        # Get approver result
        approver_outputs = approver_events.get_outputs()
        approver_result = None
        if approver_outputs:
            for output in approver_outputs:
                messages = output if isinstance(output, list) else [output]
                for msg in messages:
                    if hasattr(msg, 'text') and msg.text:
                        approver_result = msg.text
                        break

        print(f"\n✅ Insurance Claim Orchestration Complete!")
        return approver_result if approver_result else all_analyses
        
    except Exception as e:
        print(f"❌ Error during orchestration: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def _normalize_orchestration_result(result: Any) -> Dict[str, Any]:
    """Normalize whatever the orchestration returns into a simple dict.

    The orchestration may return: a dict, a JSON string, a ChatMessageContent-like
    object with a .content attribute, or a list/tuple containing one of the above.
    Printing the object may show the JSON payload, but returning the raw object
    lets FastAPI serialize the object's full structure. This function extracts
    the JSON payload (with 'decision' and 'justification' where possible) or
    falls back to a {'response': str(result)} dict.
    """

    # If it's already a dict with desired keys, return it
    if isinstance(result, dict):
        if "decision" in result and "justification" in result:
            return result
        # try to find nested dict that has the keys
        for v in result.values():
            if isinstance(v, dict) and "decision" in v and "justification" in v:
                return v

    # If it's a list/tuple, try to extract from the first meaningful element
    if isinstance(result, (list, tuple)) and result:
        for item in result:
            normalized = _normalize_orchestration_result(item)
            if "decision" in normalized:
                return normalized

    # If it's a string, try to parse JSON from it
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            return _normalize_orchestration_result(parsed)
        except json.JSONDecodeError:
            # Attempt to extract a JSON object substring that contains 'decision'
            m = re.search(r"(\{[\s\S]*?\})", result)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                    return _normalize_orchestration_result(parsed)
                except Exception:
                    pass
            return {"response": result}

    # If it has a 'content' attribute (e.g. ChatMessageContent-like), try that
    if hasattr(result, "content"):
        try:
            return _normalize_orchestration_result(result.content)
        except Exception:
            return {"response": str(result.content)}

    # If it has a 'message' attribute, inspect it
    if hasattr(result, "message"):
        try:
            return _normalize_orchestration_result(result.message)
        except Exception:
            return {"response": str(result.message)}

    # Fallback: return a simple response with a string representation
    return {"response": str(result)}


@app.post("/process-claim")
async def process_claim(req: ClaimRequest):
    """Process a claim request.

    Expects JSON body with 'claimId' and 'policyNumber' (both strings).
    Returns a JSON object with a single 'response' field (string).
    """

    # Run the orchestration to process the claim
    analysis_report = await run_insurance_claim_orchestration(req.claimId, req.policyNumber)

    print("Analysis Report:", analysis_report)

    # Normalize the orchestration output into a plain serializable dict
    normalized = _normalize_orchestration_result(analysis_report)

    print("Normalized response to return:", normalized)

    return normalized
