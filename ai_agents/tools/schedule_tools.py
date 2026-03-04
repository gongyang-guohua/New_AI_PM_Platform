# ai_agents/tools/schedule_tools.py
import json
import httpx
from langchain_core.tools import tool
from typing import Dict, List, Any

# Points to our newly created stateless FastAPI Microservices
CPM_CALCULATE_URL = "http://localhost:8000/api/v1/engine/cpm/calculate"
MONTE_CARLO_URL = "http://localhost:8000/api/v1/engine/cpm/monte-carlo"

@tool
def calculate_cpm_schedule(activities_data: List[Dict[str, Any]], dependencies_data: List[Dict[str, Any]], request_ai_insight: bool = False) -> str:
    """
    Executes the deterministic Critical Path Method (CPM) calculation API to get schedule early/late dates and floats.
    
    Args:
        activities_data: List of dicts, must contain "id" (str), "duration" (int), and optionally "constraint_type", "constraint_date". Example: [{"id": "A", "duration": 5}]
        dependencies_data: List of dicts, must contain "predecessor", "successor", "relation_type" (e.g., "FS"), "lag". Example: [{"predecessor": "A", "successor": "B", "relation_type": "FS", "lag": 0}]
        request_ai_insight: Boolean flag, set True if you want the API to return expert management suggestions based on negative floats.
        
    Returns:
        JSON string containing the calculated engine output (total floats, critical path).
    """
    payload = {
        "activities": activities_data,
        "relationships": dependencies_data,
        "with_ai_insights": request_ai_insight
    }
    try:
        response = httpx.post(CPM_CALCULATE_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"CPM API Error: {str(e)}\nMake sure you accurately mapped the JSON Schema arrays."


@tool
def run_monte_carlo_simulation(activities_data: List[Dict[str, Any]], dependencies_data: List[Dict[str, Any]], request_ai_insight: bool = False) -> str:
    """
    Executes a Monte Carlo (PERT) risk simulation API on the project network. Use this when the user asks about risk, probability, P50/P80 completion, or probabilistic simulations.
    
    Args:
        activities_data: List of dicts. Must contain "id" (str), "duration" (int), "optimistic_duration" (int), "most_likely_duration" (int), "pessimistic_duration" (int).
        dependencies_data: List of dicts. Must contain "predecessor", "successor", "relation_type" (e.g., "FS"), "lag".
        request_ai_insight: Set True to trigger the server's AI agent to interpret the critical index findings.
        
    Returns:
        JSON string containing P50, P80, P95 milestones and criticality matrices.
    """
    payload = {
        "activities": activities_data,
        "relationships": dependencies_data,
        "with_ai_insights": request_ai_insight
    }
    try:
        response = httpx.post(MONTE_CARLO_URL, json=payload, timeout=45.0)
        response.raise_for_status()
        data = response.json()
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Monte Carlo API Error: {str(e)}"
