import pytest
from core_engine.schedule.cpm_engine import Activity, Relationship, CPMEngine

def test_cpm_forward_backward_pass():
    # Setup test activities
    act_a = Activity(id="A", duration=5)
    act_b = Activity(id="B", duration=10)
    act_c = Activity(id="C", duration=3)
    act_d = Activity(id="D", duration=8)
    
    activities = {
        "A": act_a,
        "B": act_b,
        "C": act_c,
        "D": act_d
    }
    
    # Setup relationships A->B, A->C, C->D
    relationships = [
        Relationship(predecessor="A", successor="B", relation_type="FS"),
        Relationship(predecessor="A", successor="C", relation_type="FS"),
        Relationship(predecessor="C", successor="D", relation_type="FS")
    ]
    
    from core_engine.schedule.cpm_engine import WorkCalendar
    
    # Use a 7-day continuous calendar so math is straightforward
    continuous_calendar = WorkCalendar(working_days={0, 1, 2, 3, 4, 5, 6})
    engine = CPMEngine(activities=activities, relationships=relationships, calendar=continuous_calendar)
    critical_path = engine.run()
    
    # Path 1: A(5) + B(10) = 15
    # Path 2: A(5) + C(3) + D(8) = 16 (Critical Path)
    
    # Verify Early Starts
    assert activities["A"].ES == 0
    assert activities["B"].ES == 5
    assert activities["C"].ES == 5
    assert activities["D"].ES == 8
    
    # Verify Total Float
    assert activities["A"].total_float == 0
    assert activities["B"].total_float == 1  # 16 - 15 = 1
    assert activities["C"].total_float == 0
    assert activities["D"].total_float == 0
    
    # Verify Critical Path
    assert "A" in critical_path
    assert "C" in critical_path
    assert "D" in critical_path
    assert "B" not in critical_path
