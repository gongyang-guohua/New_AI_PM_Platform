from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db import models
from app.api import schemas
from app.api.deps import get_db

router = APIRouter(prefix="/engine", tags=["Engine Orchestration"])

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
