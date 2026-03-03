# ai_agents/tools/schedule_tools.py
import json
from langchain.tools import tool
from typing import Dict, List, Any
from core_engine.schedule.cpm_engine import CPMEngine, Activity, Relationship, WorkCalendar

@tool
def calculate_cpm_schedule(activities_data: List[Dict[str, Any]], dependencies_data: List[Dict[str, Any]]) -> str:
    """
    Executes the deterministic Critical Path Method (CPM) calculation.
    
    Args:
        activities_data: List of dicts, e.g., [{"id": "A", "duration": 5}]
        dependencies_data: List of dicts, e.g., [{"predecessor": "A", "successor": "B", "relation_type": "FS"}]
        
    Returns:
        JSON string containing the calculated Early Start, Early Finish, Total Float, and Critical Path.
    """
    try:
        activities = {}
        for act in activities_data:
            activities[act["id"]] = Activity(id=act["id"], duration=act["duration"])
            
        relationships = []
        for dep in dependencies_data:
            relationships.append(Relationship(
                predecessor=dep["predecessor"],
                successor=dep["successor"],
                relation_type=dep.get("relation_type", "FS")
            ))
            
        # Using enterprise 5-day work week default calendar
        engine = CPMEngine(activities=activities, relationships=relationships)
        critical_path = engine.run()
        
        results = {
            "status": "success",
            "critical_path": critical_path,
            "project_duration": max(a.EF for a in engine.activities.values()),
            "activities": {
                a.id: {
                    "early_start": a.ES,
                    "early_finish": a.EF,
                    "late_start": a.LS,
                    "late_finish": a.LF,
                    "total_float": a.total_float,
                    "is_critical": a.total_float <= 0
                } for a in engine.activities.values()
            }
        }
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
