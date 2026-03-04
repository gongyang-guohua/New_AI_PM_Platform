import os
import sys
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Project, WBSNode, Activity, Dependency
from app.api.engine import run_schedule_engine

# 1. Setup in-memory SQLite for the demo
print("=== Initializing Local SQLite Database ===")
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=== Setting up Mock EPC Project ===")
# 2. Create Project and WBS
proj = Project(name="ProjectMaster AI - Demo Plant EPC", base_start_date=datetime(2026, 4, 1, 8, 0))
db.add(proj)
db.commit()
db.refresh(proj)

wbs = WBSNode(project_id=proj.id, wbs_id="WBS-100", name="Foundation Phase", level=1, type="phase")
db.add(wbs)
db.commit()
db.refresh(wbs)

print("=== Creating Activities ===")
# 3. Create Activities
activities = [
    Activity(project_id=proj.id, wbs_node_id=wbs.id, activity_id="ENG-01", name="Foundation Design", type="engineering", original_duration=10.0),
    Activity(project_id=proj.id, wbs_node_id=wbs.id, activity_id="ENG-02", name="Procure Rebar", type="procurement", original_duration=15.0),
    Activity(project_id=proj.id, wbs_node_id=wbs.id, activity_id="CON-01", name="Site Excavation", type="construction", original_duration=5.0),
    Activity(project_id=proj.id, wbs_node_id=wbs.id, activity_id="CON-02", name="Pour Concrete", type="construction", original_duration=7.0),
    Activity(project_id=proj.id, wbs_node_id=wbs.id, activity_id="CON-03", name="Curing", type="construction", original_duration=3.0),
]
db.add_all(activities)
db.commit()

# Map IDs for easy relationship creation
act_map = {a.activity_id: a.id for a in activities}

print("=== Wiring up Dependencies (The Network Graph) ===")
# 4. Create Dependencies (Edges)
deps = [
    # Excavation and Design can start independently, but let's say Design must finish before Rebar is procured
    Dependency(project_id=proj.id, source_id=act_map["ENG-01"], target_id=act_map["ENG-02"], relationship_type="FS", lag_days=0.0), # Design -> Procure Rebar
    
    # Concrete cannot be poured until Excavation is done AND Rebar is procured
    Dependency(project_id=proj.id, source_id=act_map["CON-01"], target_id=act_map["CON-02"], relationship_type="FS", lag_days=0.0), # Excavation -> Pour Concrete
    Dependency(project_id=proj.id, source_id=act_map["ENG-02"], target_id=act_map["CON-02"], relationship_type="FS", lag_days=0.0), # Rebar -> Pour Concrete
    
    # Curing happens after Pouring
    Dependency(project_id=proj.id, source_id=act_map["CON-02"], target_id=act_map["CON-03"], relationship_type="FS", lag_days=0.0), # Pour -> Curing
]
db.add_all(deps)
db.commit()

print("=== Triggering the CPM Math Engine ===")
# 5. Run the schedule engine
# We simulate calling the FastAPI endpoint, but bypass the HTTP layer by calling the function directly
try:
    result = run_schedule_engine(project_id=proj.id, db=db)
    print(f"\nEngine Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    print(f"Critical Path Activity IDs (DB IDs): {result['critical_path_activities']}\n")
except Exception as e:
    print(f"Error running engine: {e}")

# Wait, the DB IDs in critical path are internal. Let's map them to readable Activity IDs.
db.commit() # Ensure session reflects engine updates

print("+" + "-"*96 + "+")
print("| {:<10} | {:<20} | {:<12} | {:<12} | {:<12} | {:<10} |".format(
    "Act ID", "Name", "Total Float", "Early Start", "Early Finish", "Critical?"
))
print("+" + "-"*96 + "+")

final_activities = db.query(Activity).filter(Activity.project_id == proj.id).order_by(Activity.early_start).all()
for a in final_activities:
    cr = "YES" if a.is_critical else "NO"
    es = a.early_start.strftime("%Y-%m-%d") if a.early_start else "N/A"
    ef = a.early_finish.strftime("%Y-%m-%d") if a.early_finish else "N/A"
    tf = f"{a.total_float} d" if a.total_float is not None else "N/A"
    
    print("| {:<10} | {:<20} | {:<12} | {:<12} | {:<12} | {:<10} |".format(
        a.activity_id, a.name[:20], tf, es, ef, cr
    ))

print("+" + "-"*96 + "+\n")
print("Demo Completed Successfully!")
