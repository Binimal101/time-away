from datetime import datetime, timedelta
from src.sss import Person, Task, WeeklyScheduler, validate_schedule, _day_interval
from dataclasses import asdict
import json, os

from src import _TZ, logger

# -------- Demo + Tests --------
def _mk_ts(year, month, day, hour=0, minute=0, second=0):
    dt = datetime(year, month, day, hour, minute, second, tzinfo=_TZ)
    return int(dt.timestamp())

def run_demo_and_tests():
    current_ts = _mk_ts(2025, 9, 24, 12, 0, 0)  # Wed noon ET

    people = [
        Person("alice", {"frontend", "backend"}),
        Person("bob", {"backend", "qa"}),
        Person("carl", {"frontend", "qa"}),
        Person("dina", {"data", "backend"}),
        Person("emma", {"frontend", "data", "qa"}),
    ]

    week_monday = datetime(2025, 9, 22, 0, 0, 0, tzinfo=_TZ)
    mon = int(week_monday.timestamp())
    tue = int((week_monday + timedelta(days=1)).timestamp())
    wed = int((week_monday + timedelta(days=2)).timestamp())
    thu = int((week_monday + timedelta(days=3)).timestamp())
    fri = int((week_monday + timedelta(days=4)).timestamp())
    next_mon = int((week_monday + timedelta(days=7)).timestamp())

    tasks = [
        Task("T1", {"frontend": 1, "backend": 1}, start_ts=mon, end_ts=next_mon),
        Task("T2", {"qa": 1, "data": 1}, start_ts=mon, end_ts=fri),
        Task("T3", {"frontend": 2}, start_ts=tue, end_ts=thu + 24*3600),
    ]

    sched = WeeklyScheduler(people, tasks, current_ts)
    ws = sched.build()
    ok, errs = validate_schedule(people, tasks, ws)
    assert ok, f"Validation failed: {errs}"
    assert ws.feasible, f"Scheduler reported infeasible but validation passed; violations: {ws.violations}"

    # Insufficient resources test
    scarce_tasks = [Task("X", {"data": 3}, start_ts=mon, end_ts=wed + 24*3600)]
    scarce_people = [Person("p1", {"data"}), Person("p2", {"data"}), Person("p3", {"qa"})]
    scarce_sched = WeeklyScheduler(scarce_people, scarce_tasks, current_ts)
    scarce_ws = scarce_sched.build()
    ok2, errs2 = validate_schedule(scarce_people, scarce_tasks, scarce_ws)
    assert not scarce_ws.feasible or not ok2, "Expected infeasible schedule due to insufficient skills."

    # Weekly cap scenario up to current_ts (Mon–Wed only)
    cap_tasks = [Task("C", {"frontend": 1}, start_ts=mon, end_ts=next_mon)]
    cap_people = [Person("solo", {"frontend"})]
    cap_sched = WeeklyScheduler(cap_people, cap_tasks, current_ts)
    cap_ws = cap_sched.build()
    ok3, errs3 = validate_schedule(cap_people, cap_tasks, cap_ws)
    assert ok3, f"Cap case should validate: {errs3}"
    # Count days assigned up to Wed inclusive
    # Expect at most 3 (Mon/Tue/Wed)
    start_dt = datetime.fromisoformat(cap_ws.week_start_iso)
    intervals = [(_day_interval(start_dt + timedelta(days=i))) for i in range(7)]
    assigned_days = 0
    for di, day in enumerate(cap_ws.days):
        day_start, _ = intervals[di]
        if day_start <= current_ts:
            for apt in day.assignments:
                if "solo" in apt.people_contributions:
                    assigned_days += 1
    assert assigned_days <= 3, f"Assigned more than allowed up to current_ts: {assigned_days}"

    return ws

ws2 = run_demo_and_tests()
out_path = os.path.join(os.getcwd(), "data", "weekly_schedule.json")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(asdict(ws2), f, indent=2)

print("All tests passed ✅")
print(f"Feasible: {ws2.feasible}")
print(f"Violations: {ws2.violations}")
print(f"Days scheduled: {[d.date for d in ws2.days]}")
print(f"Download: {out_path}")
