from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

# WBS Schemas
class WBSNodeBase(BaseModel):
    project_id: int
    wbs_id: str
    name: str
    level: int
    type: str
    parent_id: Optional[int] = None
    weight_percent: Optional[float] = None

class WBSNodeCreate(WBSNodeBase):
    pass

class WBSNodeResponse(WBSNodeBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Activity Schemas
class ActivityBase(BaseModel):
    project_id: int
    wbs_node_id: Optional[int] = None
    activity_id: str
    name: str
    type: str
    
    original_duration: Optional[float] = 0.0
    adjusted_duration: Optional[float] = 0.0
    resource_type: Optional[str] = None
    
    cwa_id: Optional[str] = None
    cwp_id: Optional[str] = None
    iwp_id: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: int
    early_start: Optional[datetime] = None
    early_finish: Optional[datetime] = None
    late_start: Optional[datetime] = None
    late_finish: Optional[datetime] = None
    total_float: Optional[float] = 0.0
    is_critical: Optional[bool] = False
    
    validation_health_status: Optional[str] = None
    awp_pull_variance_days: Optional[int] = None
    readiness_status: Optional[str] = "Planned"
    blocker_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Dependency Schemas
class DependencyBase(BaseModel):
    project_id: int
    source_id: int
    target_id: int
    relationship_type: Optional[str] = "FS"
    lag_days: Optional[float] = 0.0
    is_pull_constraint: Optional[bool] = False
    justification: Optional[str] = None

class DependencyCreate(DependencyBase):
    pass

class DependencyResponse(DependencyBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_start_date: Optional[datetime] = None
    baseline_finish_date: Optional[datetime] = None
    scale_factor: Optional[float] = 1.0
    complexity_factor: Optional[float] = 1.0
    crash_factor: Optional[float] = 1.0

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    
    wbs_nodes: List[WBSNodeResponse] = []
    activities: List[ActivityResponse] = []
    dependencies: List[DependencyResponse] = []

    model_config = ConfigDict(from_attributes=True)
