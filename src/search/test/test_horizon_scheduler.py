from src.search._search import *
from datetime import datetime, timezone, date

def _mk_ts(year, month, day):
    return datetime(year, month, day, tzinfo=timezone.utc).timestamp()

def test_not_utilized():
    people = [
        Person(person_id="p1", skills={"python", "java"}, preworked_in_last_7=0),
        Person(person_id="p2", skills={"python"}, preworked_in_last_7=0),
    ]
    tasks = [
        Task(task_id="t1", required_skills={"python": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
        Task(task_id="t2", required_skills={"java": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
    ]
    scheduler = HorizonScheduler(
        people=people,
        tasks=tasks,
        start_day=date(2024, 1, 2),
        span_days=3,
        current_ts=_mk_ts(2024, 1, 2),
        allow_future=True,
    )
    schedule = scheduler.build()
    assert schedule.feasible
    assert len(schedule.days) == 3
    for day in schedule.days:        
        assert len(day.assignments) == 2
        assignment_ids = {assignment.task_id for assignment in day.assignments}
        assert assignment_ids == {"t1", "t2"}
        for assignment in day.assignments:
            if assignment.task_id == "t1":
                assert "python" in assignment.skill_coverage
                assert len(assignment.skill_coverage["python"]) == 1
                assert assignment.skill_coverage["python"][0] in {"p1", "p2"}
            elif assignment.task_id == "t2":
                assert "java" in assignment.skill_coverage
                assert len(assignment.skill_coverage["java"]) == 1
                assert assignment.skill_coverage["java"][0] == "p1"

def test_utilized():
    people = [
        Person(person_id="p1", skills={"python", "java"}, preworked_in_last_7=0),
        Person(person_id="p2", skills={"python"}, preworked_in_last_7=0),
    ]
    tasks = [
        Task(task_id="t1", required_skills={"python": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
        Task(task_id="t2", required_skills={"java": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
       # Task(task_id="t3", required_skills={"python": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
    ]
    scheduler = HorizonScheduler(
        people=people,
        tasks=tasks,
        start_day=date(2024, 1, 2),
        span_days=3,
        current_ts=_mk_ts(2024, 1, 2),
        allow_future=True,
    )
    schedule = scheduler.build()
    assert schedule.feasible
    assert len(schedule.days) == 3
    for day in schedule.days:        
        assert len(day.assignments) == 2
        assignment_ids = {assignment.task_id for assignment in day.assignments}
        assert assignment_ids <= {"t1", "t2", "t3"}
        for assignment in day.assignments:
            if assignment.task_id == "t1":
                assert "python" in assignment.skill_coverage
                assert len(assignment.skill_coverage["python"]) == 1
                assert assignment.skill_coverage["python"][0] in {"p1", "p2"}
            elif assignment.task_id == "t2":
                assert "java" in assignment.skill_coverage
                assert len(assignment.skill_coverage["java"]) == 1
                assert assignment.skill_coverage["java"][0] == "p1"
            elif assignment.task_id == "t3":
                assert "python" in assignment.skill_coverage
                assert len(assignment.skill_coverage["python"]) == 1
                assert assignment.skill_coverage["python"][0] in {"p1", "p2"}

def test_pto_available():
    people = [
        Person(person_id="p1", skills={"python", "java"}, preworked_in_last_7=0),
        Person(person_id="p2", skills={"python"}, preworked_in_last_7=1),
    ]
    tasks = [
        Task(task_id="t1", required_skills={"python": 1}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
    ]
    scheduler = HorizonScheduler(
        people=people,
        tasks=tasks,
        start_day=date(2024, 1, 2),
        span_days=3,
        current_ts=_mk_ts(2024, 1, 2),
        allow_future=True,
    )
    schedule = scheduler.build()
    assert schedule.feasible
    assert len(schedule.days) == 3
    for day in schedule.days:
        assert len(day.assignments) == 1
        assignment = day.assignments[0]
        assert assignment.task_id == "t1"
        assert "python" in assignment.skill_coverage
        assert len(assignment.skill_coverage["python"]) == 1
        assert assignment.skill_coverage["python"][0] in {"p1", "p2"}

def test_pto_not_available():
    people = [
        Person(person_id="p1", skills={"python", "java"}, preworked_in_last_7=0),
        Person(person_id="p2", skills={"python"}, preworked_in_last_7=5),
    ]
    tasks = [
        Task(task_id="t1", required_skills={"python": 2}, start_ts=_mk_ts(2024, 1, 1), end_ts=_mk_ts(2024, 1, 10)),
    ]
    scheduler = HorizonScheduler(
        people=people,
        tasks=tasks,
        start_day=date(2024, 1, 2),
        span_days=3,
        current_ts=_mk_ts(2024, 1, 2),
        allow_future=True,
    )
    schedule = scheduler.build()
    assert not schedule.feasible
    assert len(schedule.days) == 3
    for day in schedule.days:
        assert len(day.assignments) == 0
