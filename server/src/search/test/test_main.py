# Import centralized definitions
from src import (
    Person, Task, Assignment, logger, display_dataframe_to_user,
    start_of_week, daterange, epoch_to_date
)
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
from src.search._search import (
    PlanStore, WeeklyScheduler, cache_schedule, pretty_assignments
)

# -----------------------
# Sample data
# -----------------------
def mk_people() -> List[Person]:
    mk = lambda pid, name, skills: Person(pid, name, set(skills))
    return [
        mk("p1", "Alex Chen", {"RN", "Triage"}),
        mk("p2", "Priya Singh", {"MD", "ER"}),
        mk("p3", "Diego Ramirez", {"RN", "ICU"}),
        mk("p4", "Fatima Ali", {"DevOps", "Python"}),
        mk("p5", "Liam O'Connor", {"Python", "Frontend"}),
        mk("p6", "Janelle Brooks", {"RN", "MD"}),
        mk("p7", "Sofia Rossi", {"Frontend", "UX"}),
        mk("p8", "Marcus Lee", {"DevOps", "Network"}),
        mk("p9", "Hannah Park", {"Python", "Data"}),
        mk("p10", "Omar Nasser", {"MD", "ICU"}),
        mk("p11", "Grace Kim", {"RN", "ICU"}),
        mk("p12", "Noah Patel", {"Python", "DevOps"}),
        mk("p13", "Ava Martinez", {"RN"}),
        mk("p14", "Ethan Zhao", {"Frontend", "UX"}),
        mk("p15", "Maya Kapoor", {"Data", "Python"}),
    ]

def date_to_epoch(d: date, hour: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, hour, 0, 0).timestamp())

def mk_tasks(week_start: date) -> List[Task]:
    mk = lambda tid, name, s, e, req: Task(tid, name, s, e, req)
    er_start = date_to_epoch(week_start - timedelta(days=28))
    er_end = date_to_epoch(week_start + timedelta(days=60), 23)
    icu_start = date_to_epoch(week_start - timedelta(days=9))
    icu_end = date_to_epoch(week_start + timedelta(days=17), 23)
    data_start = date_to_epoch(week_start)
    data_end = date_to_epoch(week_start + timedelta(days=4), 23)
    fe_start = date_to_epoch(week_start)
    fe_end = date_to_epoch(week_start + timedelta(days=6), 23)
    net_start = date_to_epoch(week_start + timedelta(days=3))
    net_end = date_to_epoch(week_start + timedelta(days=5), 23)
    return [
        mk("t1", "ER Day Shift", er_start, er_end, {"RN": 2, "MD": 1}),
        mk("t2", "ICU Night", icu_start, icu_end, {"RN": 1, "ICU": 1}),
        mk("t3", "Data Migration", data_start, data_end, {"Python": 2, "DevOps": 1}),
        mk("t4", "Frontend Sprint", fe_start, fe_end, {"Frontend": 2, "UX": 1}),
        mk("t5", "Network Maintenance", net_start, net_end, {"Network": 1, "DevOps": 1}),
    ]

# -----------------------
# TESTS
# -----------------------
def run_more_tests():
    today = date(2025, 9, 28)
    week_start = start_of_week(today, week_start=0) + timedelta(days=7)  # next week
    now_epoch = int(datetime(2025, 9, 28, 12, 0, 0).timestamp())

    people = mk_people()
    tasks = mk_tasks(week_start)
    store = PlanStore()

    # Preload prior usage for rolling-window behavior
    preload_days = [week_start - timedelta(days=d) for d in range(1, 6)]
    preload = [Assignment(day=d, person_id="p1", task_id="t1") for d in preload_days]
    store.preload(preload)

    # ---------- Test A: PTO_map disallows assignment ----------
    pto_map = {
        week_start + timedelta(days=0): ["p6", "p11"],   # Janelle (RN/MD) + Grace (RN/ICU) on PTO Monday
        week_start + timedelta(days=1): ["p2"],          # Priya (MD/ER) on PTO Tuesday
    }
    ws = WeeklyScheduler(people, tasks, store, tz_offset_hours=0)
    assigns, unsat = ws.schedule_week(week_start, now_epoch, pto_map=pto_map)

    dfA = pretty_assignments(assigns, people, tasks)
    display_dataframe_to_user("PTO-aware Week Schedule", dfA)
    logger.info(f"PTO-aware week: {len(assigns)} assignments; UNSAT days: {[d.isoformat() for d,_ in unsat]}")

    # Ensure none of the PTO people are scheduled on their PTO days
    for d, plist in pto_map.items():
        ids = set(plist)
        bad = [a for a in assigns if a.day == d and a.person_id in ids]
        assert not bad, f"PTO violation: scheduled PTO people on {d}: {bad}"

    # ---------- Test B: cache_schedule hook merges pending PTO when accepted ----------
    pending_pto = {week_start + timedelta(days=2): ["p7", "p8"]}
    updated_pto = cache_schedule(store, assigns, pto_map=pto_map, pending_pto=pending_pto, accept_pto=True)
    assert (week_start + timedelta(days=2)) in updated_pto, "Pending PTO not merged when accepted"
    logger.info("cache_schedule merged pending PTO as expected.")

    # ---------- Test C: PTO feasibility checker (separate file) ----------
    # Simulate asking: can Priya Singh (p2 - key MD) take PTO on Tue+Wed without leaving deficits?
    from datetime import date as _date
    pto_days = [week_start + timedelta(days=1), week_start + timedelta(days=2)]
    # Inline "import" shim: call the function by executing pto_tools content in this environment
    # We'll define minimal wrappers here mirroring the separate file behavior.

    def can_approve_pto_local(person_id: str, pto_days: List[date]) -> Tuple[bool, Dict]:
        # Run week(s) covering pto_days with a fresh store and PTO-map excluding the person
        pto = {d: [person_id] for d in pto_days}
        # Plan from first week to last week touching the PTO
        first = min(pto_days); last = max(pto_days)
        cur = start_of_week(first, week_start=0)
        end = start_of_week(last, week_start=0)

        all_assignments: List[Assignment] = []
        any_unsat: List[Tuple[date, Dict[str, Dict[str, int]]]] = []
        while cur <= end:
            tmp_store = PlanStore()
            ws_local = WeeklyScheduler(people, tasks, tmp_store, tz_offset_hours=0)
            a, u = ws_local.schedule_week(cur, now_epoch, pto_map=pto)
            all_assignments.extend(a)
            any_unsat.extend(u)
            cur += timedelta(days=7)
        result = {
            "pto_person_id": person_id,
            "pto_days": [d.isoformat() for d in sorted(set(pto_days))],
            "feasible": len(any_unsat) == 0,
            "unsatisfied": [(d.isoformat(), deficits) for (d, deficits) in any_unsat],
            "assignments": [
                {"date": x.day.isoformat(), "person_id": x.person_id, "task_id": x.task_id}
                for x in all_assignments
            ]
        }
        return (len(any_unsat) == 0), result

    ok_pto, res_pto = can_approve_pto_local("p2", pto_days)
    logger.info(f"Priya PTO Tue+Wed feasible? {ok_pto}. Unsat: {res_pto['unsatisfied']}")
    # Display a condensed table of resulting assignments for visibility
    dfB = pd.DataFrame(res_pto["assignments"]) if res_pto["assignments"] else pd.DataFrame(columns=["date","person_id","task_id"])
    display_dataframe_to_user("PTO Feasibility Assignments (fresh store)", dfB)

    # ---------- Test D: Month view generation (does not overwrite variables; uses cache) ----------
    # Build tasks that span the month starting from week_start's month
    month_first = date(week_start.year, week_start.month, 1)
    assignments_month, unsat_month = [], []
    # Use a fresh store to isolate month-view behavior
    store_month = PlanStore()
    # Craft PTO for two scattered days in the month
    pto_month = {
        month_first + timedelta(days=3): ["p1"],
        month_first + timedelta(days=10): ["p11"],
    }
    # Month view by iterating weeks and committing to store_month
    # (Mirror pto_tools.generate_month_view behavior)
    ws_month = WeeklyScheduler(people, tasks, store_month, tz_offset_hours=0)
    # Iterate weeks that cover the month
    cur = start_of_week(month_first, week_start=0)
    last_day = (month_first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    while cur <= last_day:
        a, u = ws_month.schedule_week(cur, now_epoch, pto_map=pto_month)
        assignments_month.extend(a)
        unsat_month.extend(u)
        cur += timedelta(days=7)

    dfC = pretty_assignments(assignments_month, people, tasks)
    display_dataframe_to_user("Month View (uses cache + PTO)", dfC)
    logger.info(f"Month view: {len(assignments_month)} assignments; UNSAT days: {[d.isoformat() for d,_ in unsat_month]}")

    # Basic sanity asserts for month view
    # Ensure no PTO people scheduled on their PTO days in the month
    for d, plist in pto_month.items():
        ids = set(plist)
        bad = [a for a in assignments_month if a.day == d and a.person_id in ids]
        assert not bad, f"Month PTO violation on {d}: {bad}"

    return {
        "week_with_pto_assignments": len(assigns),
        "unsat_week_with_pto": [d.isoformat() for d,_ in unsat],
        "cache_schedule_pto_merged_day": (week_start + timedelta(days=2)).isoformat(),
        "can_approve_pto_ok": ok_pto,
        "unsat_days_pto_check": res_pto["unsatisfied"],
        "month_view_assignments": len(assignments_month),
        "month_unsat_days": [d.isoformat() for d,_ in unsat_month],
    }

results = run_more_tests()
results
