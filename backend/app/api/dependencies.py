from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.api import schemas
from app.api.deps import get_db

router = APIRouter(prefix="/dependencies", tags=["Dependencies"])

@router.post("/", response_model=schemas.DependencyResponse, status_code=status.HTTP_201_CREATED)
def create_dependency(dependency: schemas.DependencyCreate, db: Session = Depends(get_db)):
    # Validate project
    project = db.query(models.Project).filter(models.Project.id == dependency.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate source and target activities
    source_act = db.query(models.Activity).filter(models.Activity.id == dependency.source_id).first()
    target_act = db.query(models.Activity).filter(models.Activity.id == dependency.target_id).first()
    
    if not source_act or not target_act:
        raise HTTPException(status_code=404, detail="Source or Target Activity not found")
        
    if source_act.project_id != dependency.project_id or target_act.project_id != dependency.project_id:
        raise HTTPException(status_code=400, detail="Activities do not belong to the specified project")

    db_dependency = models.Dependency(**dependency.model_dump())
    db.add(db_dependency)
    db.commit()
    db.refresh(db_dependency)
    return db_dependency

@router.get("/", response_model=List[schemas.DependencyResponse])
def get_dependencies(project_id: int, db: Session = Depends(get_db)):
    dependencies = db.query(models.Dependency).filter(models.Dependency.project_id == project_id).all()
    return dependencies

@router.post("/batch", response_model=List[schemas.DependencyResponse], status_code=status.HTTP_201_CREATED)
def create_dependencies_batch(dependencies: List[schemas.DependencyCreate], db: Session = Depends(get_db)):
    if not dependencies:
        return []
    
    project_id = dependencies[0].project_id
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db_deps = [models.Dependency(**dep.model_dump()) for dep in dependencies]
    db.add_all(db_deps)
    db.commit()
    
    for dep in db_deps:
        db.refresh(dep)
        
    return db_deps
