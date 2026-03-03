# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    activities = relationship("Activity", back_populates="project")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    activity_code = Column(String, index=True)
    name = Column(String)
    
    # CPM Fields
    original_duration = Column(Float, default=0.0)
    early_start = Column(DateTime, nullable=True)
    early_finish = Column(DateTime, nullable=True)
    late_start = Column(DateTime, nullable=True)
    late_finish = Column(DateTime, nullable=True)
    total_float = Column(Float, default=0.0)
    is_critical = Column(Boolean, default=False)
    
    project = relationship("Project", back_populates="activities")
    # Missing dependencies, resources etc. for now, will expand later.
