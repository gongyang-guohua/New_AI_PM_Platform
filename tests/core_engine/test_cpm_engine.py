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
    # Verify Critical Path
    assert "A" in critical_path
    assert "C" in critical_path
    assert "D" in critical_path
    assert "B" not in critical_path


def test_cpm_constraints():
    # Setup test activities with constraints
    act_a = Activity(id="A", duration=5, constraint_type="MSO", constraint_date=2)
    act_b = Activity(id="B", duration=10)
    act_c = Activity(id="C", duration=3, constraint_type="FNLT", constraint_date=12)
    
    activities = {
        "A": act_a,
        "B": act_b,
        "C": act_c
    }
    
    relationships = [
        Relationship(predecessor="A", successor="B", relation_type="FS"),
        Relationship(predecessor="A", successor="C", relation_type="FS")
    ]
    
    from core_engine.schedule.cpm_engine import WorkCalendar
    continuous_calendar = WorkCalendar(working_days={0, 1, 2, 3, 4, 5, 6})
    engine = CPMEngine(activities=activities, relationships=relationships, calendar=continuous_calendar)
    engine.run()
    
    # Verify MSO Constraint (Must Start On) -> ES of A should be forced to 2
    assert activities["A"].ES == 2
    assert activities["A"].EF == 7
    
    # B's ES should be pushed to 7
    assert activities["B"].ES == 7
    
    # C's ES should be 7, EF is 10
    assert activities["C"].ES == 7
    assert activities["C"].EF == 10
    
    # Verify FNLT Constraint (Finish No Later Than) -> LF of C should be forced to 12
    assert activities["C"].LF == 12
    assert activities["C"].LS == 9


def test_monte_carlo_engine():
    from core_engine.schedule.cpm_engine import MonteCarloEngine
    
    # Activity A has purely deterministic PERT data (min, mode, max all 10)
    act_a = Activity(id="A", duration=10, 
                     optimistic_duration=10, most_likely_duration=10, pessimistic_duration=10)
    
    # Activity B has varying PERT data (min 5, mode 10, max 20)
    act_b = Activity(id="B", duration=10,
                     optimistic_duration=5, most_likely_duration=10, pessimistic_duration=20)
                     
    activities = {"A": act_a, "B": act_b}
    relationships = [Relationship(predecessor="A", successor="B", relation_type="FS")]
    
    from core_engine.schedule.cpm_engine import WorkCalendar
    continuous_calendar = WorkCalendar(working_days={0, 1, 2, 3, 4, 5, 6})
    
    mc_engine = MonteCarloEngine(activities=activities, relationships=relationships, calendar=continuous_calendar)
    
    results = mc_engine.simulate(iterations=100)
    
    assert "p50_duration" in results
    assert "min_duration" in results
    assert "max_duration" in results
    assert "criticality_index" in results
    
    # Minimum duration should be at least A(10) + B_min(5) = 15
    assert results["min_duration"] >= 15
    # Maximum should be roughly up to A(10) + B_max(20) = 30
    assert results["max_duration"] <= 30
    
    # Because A -> B is the only path, both A and B must be on critical path 100% of the time (1.0)
    assert results["criticality_index"]["A"] == 1.0
    assert results["criticality_index"]["B"] == 1.0
