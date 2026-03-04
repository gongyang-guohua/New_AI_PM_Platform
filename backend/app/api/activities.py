from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.api import schemas
from app.api.deps import get_db

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.post("/", response_model=schemas.ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == activity.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # WBS Validation is optional but good if provided
    if activity.wbs_node_id:
        wbs = db.query(models.WBSNode).filter(models.WBSNode.id == activity.wbs_node_id).first()
        if not wbs:
            raise HTTPException(status_code=404, detail="WBS Node not found")

    db_activity = models.Activity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.get("/", response_model=List[schemas.ActivityResponse])
def get_activities(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    activities = db.query(models.Activity).filter(models.Activity.project_id == project_id).offset(skip).limit(limit).all()
    return activities

@router.get("/{activity_id}", response_model=schemas.ActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.post("/batch", response_model=List[schemas.ActivityResponse], status_code=status.HTTP_201_CREATED)
def create_activities_batch(activities: List[schemas.ActivityCreate], db: Session = Depends(get_db)):
    if not activities:
        return []
    
    project_id = activities[0].project_id
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db_activities = [models.Activity(**act.model_dump()) for act in activities]
    db.add_all(db_activities)
    db.commit()
    
    for act in db_activities:
        db.refresh(act)
        
    return db_activities
