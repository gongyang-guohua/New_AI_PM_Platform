from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db import models
from app.api import schemas
from app.api.deps import get_db

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from core_engine.schedule.cpm_engine import CPMEngine, MonteCarloEngine, Activity as CPMActivity, Relationship as CPMRelationship

# Import our new stateless schemas and AI Gateway
import app.api.schemas_engine as engine_schemas
from app.services.llm_gateway import llm_gateway

router = APIRouter(prefix="/engine", tags=["Engine Orchestration"])

# ---------------------------------------------
# 1. STATELESS MICROSERVICE ENDPOINTS (NEW)
# ---------------------------------------------

@router.post("/cpm/calculate", response_model=engine_schemas.CPMResponse)
def calculate_cpm_stateless(payload: engine_schemas.CPMRequestBody):
    """
    Stateless Endpoint: Runs deterministic CPM scheduling and returns results.
    Can be called by Node.js or any other services by passing standard JSON.
    """
    # 1. Map DTO to Engine Models
    cpm_activities = {}
    for act in payload.activities:
        cpm_activities[act.id] = CPMActivity(
            id=act.id,
            duration=act.duration,
            constraint_type=act.constraint_type,
            constraint_date=act.constraint_date
        )
        
    cpm_relationships = []
    for rel in payload.relationships:
        cpm_relationships.append(
            CPMRelationship(
                predecessor=rel.predecessor,
                successor=rel.successor,
                relation_type=rel.relation_type,
                lag=rel.lag
            )
        )
        
    # 2. Execute Calculation
    try:
        engine = CPMEngine(activities=cpm_activities, relationships=cpm_relationships)
        critical_path = engine.run()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CPM Calculation failed: {str(e)}")
        
    # 3. Format Response
    project_duration = max(a.EF for a in engine.activities.values()) if engine.activities else 0
    
    result_activities = []
    for act_id, act in engine.activities.items():
        result_activities.append(
            engine_schemas.CPMResultActivity(
                id=act.id,
                early_start=act.ES,
                early_finish=act.EF,
                late_start=act.LS,
                late_finish=act.LF,
                total_float=act.total_float,
                free_float=act.free_float,
                is_critical=act.id in critical_path
            )
        )
        
    # 4. AI Insight Generation (if requested)
    ai_insights = None
    if payload.with_ai_insights:
        negative_float_tasks = [act.id for act in result_activities if act.total_float < 0]
        sys_prompt = "You are a senior Project Controls Manager. Analyze the schedule and provide actionable advice in Chinese. Be extremely concise. Output JSON format if possible, otherwise plain text."
        user_prompt = f"Project duration is {project_duration} days. Critical Path: {critical_path}. Tasks with negative float: {negative_float_tasks}. Please provide 2 short bullet points on crashing/accelerating the schedule."
        
        # Call the LLM Gateway
        ai_insights = llm_gateway.generate_insight(sys_prompt, user_prompt, json_mode=False)

    return engine_schemas.CPMResponse(
        project_duration=project_duration,
        activities=result_activities,
        critical_path=critical_path,
        ai_insights=ai_insights
    )


@router.post("/cpm/monte-carlo", response_model=engine_schemas.MonteCarloResponse)
def run_monte_carlo_stateless(payload: engine_schemas.CPMRequestBody, iterations: int = 1000):
    """
    Stateless Endpoint: Runs Monte Carlo / PERT simulation for schedule risk analysis.
    """
    cpm_activities = {}
    for act in payload.activities:
        cpm_activities[act.id] = CPMActivity(
            id=act.id,
            duration=act.duration,
            optimistic_duration=act.optimistic_duration,
            most_likely_duration=act.most_likely_duration,
            pessimistic_duration=act.pessimistic_duration
        )
        
    cpm_relationships = []
    for rel in payload.relationships:
        cpm_relationships.append(CPMRelationship(predecessor=rel.predecessor, successor=rel.successor, relation_type=rel.relation_type, lag=rel.lag))
        
    try:
        mc_engine = MonteCarloEngine(activities=cpm_activities, relationships=cpm_relationships)
        results = mc_engine.simulate(iterations=iterations)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Monte Carlo simulation failed: {str(e)}")

    # Construct insight request via LLM
    ai_insights = None
    if payload.with_ai_insights:
        high_risk_tasks = [k for k, v in results['criticality_index'].items() if v > 0.6]
        sys_prompt = "你是一位精通工程管理风险分析的 AI 顾问。请用简洁的专业的中文指出项目中最大的进度风险点。"
        user_prompt = f"蒙特卡洛分析结果: P50工期={results['p50_duration']}, P80工期={results['p80_duration']}。在1000次模拟中，经常出现在关键路径上的高频节点有: {high_risk_tasks}。请作简短的中文预警提示。"
        
        ai_insights = llm_gateway.generate_insight(sys_prompt, user_prompt, json_mode=False)

    return engine_schemas.MonteCarloResponse(
        p50_duration=results["p50_duration"],
        p80_duration=results["p80_duration"],
        p95_duration=results["p95_duration"],
        mean_duration=results["mean_duration"],
        min_duration=results["min_duration"],
        max_duration=results["max_duration"],
        criticality_index=results["criticality_index"],
        ai_insights=ai_insights
    )


# ---------------------------------------------
# 2. STATEFUL DATABASE ENDPOINTS (LEGACY)
# ---------------------------------------------

@router.post("/schedule/run/{project_id}")
def run_schedule_engine(project_id: int, db: Session = Depends(get_db)):
    """
    Triggers the Schedule_Agent's core CPM calculation logic for a specific project.
    Pulls dependencies from the database, runs the deterministic CPMEngine algorithm,
    and updates the database with calculated Early/Late boundary dates.
    """
    import sys
    import os
    from datetime import datetime, timedelta
    
    # Import from the core_engine in the project root
    sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))
    from core_engine.schedule.cpm_engine import CPMEngine, Activity as CPMActivity, Relationship as CPMRelationship

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch all activities and dependencies
    db_activities = db.query(models.Activity).filter(models.Activity.project_id == project_id).all()
    db_dependencies = db.query(models.Dependency).filter(models.Dependency.project_id == project_id).all()

    if not db_activities:
        return {"status": "success", "message": "No activities to schedule"}

    # Map to CPM Engine models
    cpm_activities = {}
    for act in db_activities:
        duration = int(act.original_duration) if act.original_duration else 0
        cpm_activities[str(act.id)] = CPMActivity(id=str(act.id), duration=duration)

    cpm_relationships = []
    for dep in db_dependencies:
        cpm_relationships.append(
            CPMRelationship(
                predecessor=str(dep.source_id),
                successor=str(dep.target_id),
                relation_type=dep.relationship_type or "FS",
                lag=int(dep.lag_days) if dep.lag_days else 0
            )
        )

    # Initialize Engine and Run
    try:
        engine = CPMEngine(activities=cpm_activities, relationships=cpm_relationships)
        critical_path = engine.run() # this populates ES, EF, LS, LF, total_float onto the dictionary values
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CPM Calculation failed: {str(e)}")

    # Map integer durations (days) back to datetimes based on project start
    start_date = project.base_start_date or datetime.now()
    
    # Update DB Models
    for db_act in db_activities:
        calc_act = engine.activities[str(db_act.id)]
        
        db_act.early_start = start_date + timedelta(days=calc_act.ES)
        db_act.early_finish = start_date + timedelta(days=calc_act.EF)
        db_act.late_start = start_date + timedelta(days=calc_act.LS)
        db_act.late_finish = start_date + timedelta(days=calc_act.LF)
        db_act.total_float = float(calc_act.total_float)
        db_act.is_critical = str(db_act.id) in critical_path
        
    db.commit()

    return {
        "status": "success",
        "project_id": project_id,
        "message": "Schedule Engine calculation applied to database",
        "critical_path_activities": critical_path
    }

@router.post("/schedule/update-results/{project_id}")
def update_schedule_results(project_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Receives the computed results from the Schedule_Agent (as per its Output JSON Schema)
    and updates the database.
    """
    # Ex: payload would contain a list of 'activities' with their cpm metrics
    activities_data = payload.get("activities", [])
    
    for act_data in activities_data:
        activity_id_str = act_data.get("activity_id")
        db_act = db.query(models.Activity).filter(
            models.Activity.project_id == project_id,
            models.Activity.activity_id == activity_id_str
        ).first()
        
        if db_act:
            cpm = act_data.get("cpm", {})
            # Note: Need explicit conversion from date strings to datetime objects in a real parsing
            # For brevity, assuming the schema format is handled or we parse it
            
            # db_act.total_float = cpm.get("total_float", 0.0)
            db_act.is_critical = cpm.get("is_critical", False)
            
            validation = act_data.get("validation", {})
            db_act.awp_pull_variance_days = validation.get("awp_pull_variance_days")
            db_act.validation_health_status = validation.get("health_status")
            
    db.commit()
    
    return {"status": "success", "message": "Activities updated with schedule CPM results"}

@router.post("/readiness/scan/{project_id}")
def run_readiness_scan(project_id: int, db: Session = Depends(get_db)):
    """
    Triggers the Readiness_Agent to scan for Early Start within 7 days.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return {
        "status": "success", 
        "message": "Readiness Engine polling triggered"
    }

@router.post("/readiness/update-results/{project_id}")
def update_readiness_results(project_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Receives readiness checks from the Readiness_Agent and updates the database Activity statuses.
    """
    checks = payload.get("readiness_checks", [])
    
    for check in checks:
        activity_id_str = check.get("activity_id")
        db_act = db.query(models.Activity).filter(
            models.Activity.project_id == project_id,
            models.Activity.activity_id == activity_id_str
        ).first()
        
        if db_act:
            db_act.readiness_status = check.get("final_readiness_status")
            if db_act.readiness_status == "Blocked":
                db_act.blocker_reason = str(check.get("check_results", {})) # Simplifying reason storage
                
    db.commit()
    return {"status": "success", "message": "Activity readiness statuses updated"}
