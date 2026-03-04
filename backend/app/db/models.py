from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum
from sqlalchemy import Enum as SQLAlchemyEnum

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # CPM / Schedule Parameters
    base_start_date = Column(DateTime, nullable=True)
    baseline_finish_date = Column(DateTime, nullable=True)
    scale_factor = Column(Float, default=1.0)
    complexity_factor = Column(Float, default=1.0)
    crash_factor = Column(Float, default=1.0)
    
    wbs_nodes = relationship("WBSNode", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    dependencies = relationship("Dependency", back_populates="project", cascade="all, delete-orphan")

class WBSNode(Base):
    __tablename__ = "wbs_nodes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    wbs_id = Column(String, index=True, nullable=False) # e.g., WBS-1000
    name = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    type = Column(String, nullable=False) # e.g., 'project', 'phase'
    parent_id = Column(Integer, ForeignKey("wbs_nodes.id", ondelete="CASCADE"), nullable=True)
    weight_percent = Column(Float, nullable=True)

    project = relationship("Project", back_populates="wbs_nodes")
    parent = relationship("WBSNode", remote_side=[id], back_populates="children")
    children = relationship("WBSNode", back_populates="parent")
    activities = relationship("Activity", back_populates="wbs_node")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id", ondelete="SET NULL"), nullable=True)
    
    activity_id = Column(String, index=True, nullable=False) # e.g., CONST-001
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # permit, engineering, procurement, construction, milestone
    
    # Resource & Duration
    original_duration = Column(Float, default=0.0)
    adjusted_duration = Column(Float, default=0.0)
    resource_type = Column(String, nullable=True)
    
    # AWP Spatial Tags
    cwa_id = Column(String, nullable=True) # e.g., CWA-01
    cwp_id = Column(String, nullable=True) # e.g., CWP-01-CIVIL
    iwp_id = Column(String, nullable=True) # e.g., IWP-01-CIV-001
    
    # CPM Fields
    early_start = Column(DateTime, nullable=True)
    early_finish = Column(DateTime, nullable=True)
    late_start = Column(DateTime, nullable=True)
    late_finish = Column(DateTime, nullable=True)
    total_float = Column(Float, default=0.0)
    is_critical = Column(Boolean, default=False)
    
    # Validation / Execution Fields
    validation_health_status = Column(String, nullable=True) # e.g., NORMAL, DELAYED
    awp_pull_variance_days = Column(Integer, nullable=True)
    readiness_status = Column(String, default="Planned") # Planned, Blocked, Ready for Construction
    blocker_reason = Column(Text, nullable=True)
    
    project = relationship("Project", back_populates="activities")
    wbs_node = relationship("WBSNode", back_populates="activities")
    
    # Relationships for Dependencies definition
    source_dependencies = relationship("Dependency", foreign_keys="[Dependency.source_id]", back_populates="source_activity", cascade="all, delete-orphan")
    target_dependencies = relationship("Dependency", foreign_keys="[Dependency.target_id]", back_populates="target_activity", cascade="all, delete-orphan")

class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Predecessor
    source_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    
    # Successor
    target_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    
    relationship_type = Column(String, default="FS") # FS, SS, FF, SF. EWP->IWP pull links are often just standard dependencies or special markers.
    lag_days = Column(Float, default=0.0)
    
    # AWP / Constraint Info
    is_pull_constraint = Column(Boolean, default=False)
    justification = Column(Text, nullable=True)
    
    project = relationship("Project", back_populates="dependencies")
    
    source_activity = relationship("Activity", foreign_keys=[source_id], back_populates="source_dependencies")
    target_activity = relationship("Activity", foreign_keys=[target_id], back_populates="target_dependencies")
