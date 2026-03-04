import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

from app.main import app as main_app
from app.db.session import SessionLocal, engine as default_engine
from app.db.models import Base
from app.api.deps import get_db

# Override database URL with an SQLite memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    # Explicitly import all models so Base metadata knows about them
    from app.db.models import Project, WBSNode, Activity, Dependency
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_app.dependency_overrides[get_db] = override_get_db
    with TestClient(main_app) as c:
        yield c
    main_app.dependency_overrides.clear()

def test_full_agent_flow(client, db_session):
    # 1. WBS Agent (Mock Project setup via DB session directly for speed, or we can add an endpoint if we made one)
    from app.db.models import Project, WBSNode
    proj = Project(name="Methanol Plant EPC")
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)
    project_id = proj.id
    
    wbs = WBSNode(project_id=project_id, wbs_id="WBS-5000", name="Construction", level=2, type="phase")
    db_session.add(wbs)
    db_session.commit()
    db_session.refresh(wbs)

    
    # 2. Construction/AWP Agent -> POST Activities
    act1_res = client.post("/api/v1/activities/", json={
        "project_id": project_id,
        "wbs_node_id": wbs.id,
        "activity_id": "STRUC-D02",
        "name": "Foundation Drawing IFC",
        "type": "engineering",
        "original_duration": 10.0
    })
    assert act1_res.status_code == 201
    act1_id = act1_res.json()["id"]

    act2_res = client.post("/api/v1/activities/", json={
        "project_id": project_id,
        "wbs_node_id": wbs.id,
        "activity_id": "CONST-003",
        "name": "Foundation Excavation",
        "type": "construction",
        "cwa_id": "CWA-01",
        "original_duration": 25.0
    })
    assert act2_res.status_code == 201
    act2_id = act2_res.json()["id"]
    
    # 3. AWP PoC Agent -> POST Dependencies
    dep_res = client.post("/api/v1/dependencies/", json={
        "project_id": project_id,
        "source_id": act1_id,
        "target_id": act2_id,
        "relationship_type": "FS",
        "is_pull_constraint": True,
        "justification": "Must have drawings before digging"
    })
    assert dep_res.status_code == 201
    
    # 4. Schedule Agent -> Trigger Engine & Update Results
    sched_trigger = client.post(f"/api/v1/engine/schedule/run/{project_id}")
    assert sched_trigger.status_code == 200
    sched_data = sched_trigger.json()
    assert act1_id in sched_data["critical_path_activities"] or "critical_path" in sched_data.get("message", "").lower() or sched_data.get("status") == "success"
    
    # 5. Readiness Agent -> Trigger Engine & Update Results
    readiness_update = client.post(f"/api/v1/engine/readiness/update-results/{project_id}", json={
        "readiness_checks": [
            {
                "activity_id": "CONST-003",
                "final_readiness_status": "Blocked",
                "check_results": {"engineering_clear": False}
            }
        ]
    })
    assert readiness_update.status_code == 200
    
    # Final checks
    final_act_res = client.get(f"/api/v1/activities/{act2_id}")
    final_act = final_act_res.json()
    assert final_act["activity_id"] == "CONST-003"
    assert final_act["readiness_status"] == "Blocked"
