import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import sys
import os

# Add backend to path to import models and session
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, '../../backend'))
sys.path.insert(0, backend_path)

from app.db.models import Base, Project, WBSNode, Activity, Dependency

@pytest.fixture(scope="module")
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

def test_project_creation(session):
    project = Project(
        name="Test Project",
        description="A test PM project",
        base_start_date=datetime(2026, 6, 1)
    )
    session.add(project)
    session.commit()
    
    assert project.id is not None
    assert project.base_start_date == datetime(2026, 6, 1)

def test_wbs_hierarchy(session):
    project = Project(name="Test WBS Project")
    session.add(project)
    session.commit()
    
    wbs_root = WBSNode(
        project_id=project.id,
        wbs_id="WBS-1000",
        name="Root Level",
        level=1,
        type="project"
    )
    session.add(wbs_root)
    session.commit()
    
    wbs_child = WBSNode(
        project_id=project.id,
        wbs_id="WBS-1000.10",
        name="Phase Level",
        level=2,
        type="phase",
        parent_id=wbs_root.id
    )
    session.add(wbs_child)
    session.commit()
    
    assert wbs_child.parent.id == wbs_root.id
    assert wbs_root.children[0].id == wbs_child.id

def test_activity_and_dependency(session):
    project = Project(name="Test AWP Project")
    session.add(project)
    session.commit()
    
    wbs_node = WBSNode(
        project_id=project.id,
        wbs_id="WBS-5000",
        name="Construction",
        level=2,
        type="phase"
    )
    session.add(wbs_node)
    session.commit()
    
    activity_ewp = Activity(
        project_id=project.id,
        wbs_node_id=wbs_node.id,
        activity_id="STRUC-D02",
        name="Foundation Drawing IFC",
        type="engineering",
        original_duration=10.0
    )
    
    activity_iwp = Activity(
        project_id=project.id,
        wbs_node_id=wbs_node.id,
        activity_id="CONST-003",
        name="Foundation Setting Out",
        type="construction",
        cwa_id="CWA-01",
        cwp_id="CWP-01-CIVIL",
        iwp_id="IWP-01-CIV-001",
        original_duration=25.0
    )
    session.add_all([activity_ewp, activity_iwp])
    session.commit()
    
    dependency = Dependency(
        project_id=project.id,
        source_id=activity_ewp.id,
        target_id=activity_iwp.id,
        is_pull_constraint=True,
        justification="Must provide drawings"
    )
    session.add(dependency)
    session.commit()
    
    assert dependency.source_activity.activity_id == "STRUC-D02"
    assert dependency.target_activity.activity_id == "CONST-003"
    assert dependency.project_id == project.id
    assert activity_iwp.cwa_id == "CWA-01"
