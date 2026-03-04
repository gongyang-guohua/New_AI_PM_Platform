from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --------------------------
# Request Models
# --------------------------

class CPMActivitySchema(BaseModel):
    id: str = Field(..., description="Unique activity identifier")
    duration: int = Field(..., description="Deterministic duration of the activity")
    constraint_type: Optional[str] = Field(None, description="Examples: SNET, FNLT, MSO, MFO")
    constraint_date: Optional[int] = Field(None, description="Absolute integer timeframe date for the constraint")
    
    # PERT Attributes for Monte Carlo
    optimistic_duration: Optional[int] = None
    most_likely_duration: Optional[int] = None
    pessimistic_duration: Optional[int] = None

class CPMRelationSchema(BaseModel):
    predecessor: str = Field(..., description="ID of preceding activity")
    successor: str = Field(..., description="ID of succeeding activity")
    relation_type: str = Field("FS", description="Relationship type: FS, SS, FF, SF")
    lag: int = Field(0, description="Lag duration")

class CPMRequestBody(BaseModel):
    activities: List[CPMActivitySchema]
    relationships: List[CPMRelationSchema]
    with_ai_insights: bool = Field(False, description="Flag to toggle LLM-powered diagnostics")

# --------------------------
# Response Models
# --------------------------

class CPMResultActivity(BaseModel):
    id: str
    early_start: int
    early_finish: int
    late_start: int
    late_finish: int
    total_float: int
    free_float: int
    is_critical: bool

class CPMResponse(BaseModel):
    project_duration: int
    activities: List[CPMResultActivity]
    critical_path: List[str]
    ai_insights: Optional[str] = Field(None, description="AI generated report for the schedule")

class MonteCarloResponse(BaseModel):
    p50_duration: float
    p80_duration: float
    p95_duration: float
    mean_duration: float
    min_duration: int
    max_duration: int
    criticality_index: Dict[str, float]
    ai_insights: Optional[str] = Field(None, description="AI generated risk analysis report")
