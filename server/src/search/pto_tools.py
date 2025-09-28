from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional, Union, Iterable, Set, Any, Callable

# Import from centralized src module
from src import (
    Person, Task, Assignment, logger, start_of_week, daterange
)
from src.search._search import (
    PlanStore, WeeklyScheduler, DaySolver, is_task_active_on_day, 
    pretty_assignments, normalize_pto_map
)

# -----------------------
# Optional FastMCP wiring (kept lightweight; not used in tests)
# -----------------------
try:
    import fastmcp
    from fastmcp import FastMCP
    MCP_AVAILABLE = True
    mcp = FastMCP("PTO Tools")
except ImportError:
    MCP_AVAILABLE = False
    FastMCP = None
    mcp = None
    logger.warning("FastMCP not available - handlers will not be registered")


# ---------- Parsing helpers ----------
def _as_set(x: Union[Set[str], List[str]]) -> Set[str]:
    return set(x) if isinstance(x, set) else set(list(x))

def custom_person_constructor(data: Union[Person, dict]) -> Person:
    if isinstance(data, Person):
        return data
    if not isinstance(data, dict):
        raise TypeError(f"Person payload must be dict or Person; got {type(data)}.")
    pid = data.get("person_id", data.get("id"))
    name = data.get("name")
    skills = data.get("skills", [])
    if pid is None or name is None:
        raise ValueError("Person dict requires 'person_id' (or 'id') and 'name'.")
    return Person(person_id=str(pid), name=str(name), skills=_as_set(skills))

def custom_task_constructor(data: Union[Task, dict]) -> Task:
    if isinstance(data, Task):
        return data
    if not isinstance(data, dict):
        raise TypeError(f"Task payload must be dict or Task; got {type(data)}.")
    tid = data.get("task_id", data.get("id"))
    name = data.get("name")
    start_epoch = data.get("start_epoch", data.get("start"))
    end_epoch = data.get("end_epoch", data.get("end"))
    req = data.get("daily_requirements", data.get("requirements"))
    if tid is None or name is None or start_epoch is None or end_epoch is None or req is None:
        raise ValueError("Task dict requires id/name/start_epoch/end_epoch/daily_requirements.")
    if not isinstance(req, dict):
        raise TypeError("Task.daily_requirements must be a dict[str,int].")
    return Task(task_id=str(tid), name=str(name),
                start_epoch=int(start_epoch), end_epoch=int(end_epoch),
                daily_requirements={str(k): int(v) for k, v in req.items()})

def custom_planstore_constructor(data: Union[PlanStore, dict, str]) -> PlanStore:
    if isinstance(data, PlanStore):
        return data
    if isinstance(data, str):
        return PlanStore.from_json(data)
    if not isinstance(data, dict):
        raise TypeError(f"PlanStore payload must be PlanStore, dict, or json str; got {type(data)}.")
    if "json" in data and isinstance(data["json"], str):
        return PlanStore.from_json(data["json"])
    mapping = data.get("days_by_person", data)
    if not isinstance(mapping, dict):
        raise ValueError("PlanStore dict must contain 'days_by_person' mapping or be a mapping itself.")
    payload = {}
    for pid, days in mapping.items():
        if not isinstance(days, (list, tuple)):
            raise ValueError("PlanStore days must be a list of ISO date strings.")
        payload[str(pid)] = [str(d) for d in days]
    import json as _json
    return PlanStore.from_json(_json.dumps(payload))


# ---------- PTO Map merge (ALWAYS consider baseline PTO) ----------
def _merge_pto_maps(*maps: Optional[Dict[Union[date, str], List[Union[Person, str, dict]]]]) -> Dict[date, List[str]]:
    merged: Dict[date, Set[str]] = {}
    for m in maps:
        if not m:
            continue
        for d, plist in m.items():
            dd = date.fromisoformat(d) if isinstance(d, str) else d
            ids: Set[str] = set()
            for p in plist:
                if isinstance(p, dict):
                    ids.add(custom_person_constructor(p).person_id)
                elif isinstance(p, Person):
                    ids.add(p.person_id)
                else:
                    ids.add(str(p))
            merged.setdefault(dd, set()).update(ids)
    return {d: sorted(list(ids)) for d, ids in merged.items()}


# ---------- Core helpers ----------
def _strip_cache_and_test_week(people: List[Person],
                               tasks: List[Task],
                               week_start: date,
                               now_epoch: int,
                               pto_map: Optional[Dict[date, List[Union[Person, str]]]] = None
                               ) -> Tuple[bool, List[Assignment], List[Tuple[date, Dict[str, Dict[str, int]]]]]:
    """
    One-week solve with NO prior PlanStore usage (fresh),
    but honoring the provided PTO map (which includes baseline PTO + candidate PTO).
    """
    tmp_store = PlanStore()
    sched = WeeklyScheduler(people, tasks, tmp_store, tz_offset_hours=0)
    assigns, unsat = sched.schedule_week(week_start, now_epoch, pto_map=pto_map)
    feasible = len(unsat) == 0
    return feasible, assigns, unsat


# ---------- PTO checks ----------
def can_approve_pto(person_id: str,
                    pto_days: List[Union[date, str]],
                    people: List[Union[Person, dict]],
                    tasks: List[Union[Task, dict]],
                    now_epoch: int,
                    week_start: Optional[Union[date, str]] = None,
                    baseline_pto_map: Optional[Dict[Union[date, str], List[Union[Person, str, dict]]]] = None
                    ) -> Tuple[bool, Dict]:
    """
    Baseline feasibility that ALWAYS considers already-agreed PTO (baseline_pto_map).
    This is a "fresh" check — rolling 7-day history is not applied (no PlanStore preload).
    """
    parsed_pto_days: List[date] = []
    for d in pto_days:
        parsed_pto_days.append(date.fromisoformat(d) if isinstance(d, str) else d)
    parsed_people = [custom_person_constructor(p) for p in people]
    parsed_tasks = [custom_task_constructor(t) for t in tasks]
    if week_start and isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)
    if not parsed_pto_days:
        return True, {"message": "No PTO days provided."}

    # Merge baseline PTO (already approved) + the candidate PTO
    candidate_map = {d: [person_id] for d in parsed_pto_days}
    combined_pto = _merge_pto_maps(baseline_pto_map, candidate_map)

    # Solve weeks that touch the combined PTO window
    first = min(combined_pto.keys())
    last = max(combined_pto.keys())
    start_wk = start_of_week(first, week_start=0)
    end_wk = start_of_week(last, week_start=0)

    all_assignments: List[Assignment] = []
    any_unsat: List[Tuple[date, Dict[str, Dict[str, int]]]] = []
    cur = start_wk
    while cur <= end_wk:
        ok, assigns, unsat = _strip_cache_and_test_week(parsed_people, parsed_tasks, cur, now_epoch, pto_map=combined_pto)
        all_assignments.extend(assigns)
        any_unsat.extend(unsat)
        cur += timedelta(days=7)

    result = {
        "pto_person_id": person_id,
        "pto_days": [d.isoformat() for d in sorted(set(parsed_pto_days))],
        "feasible": len(any_unsat) == 0,
        "unsatisfied": [(d.isoformat(), deficits) for (d, deficits) in any_unsat],
        "assignments": [
            {
                "date": a.day.isoformat(),
                "person_id": a.person_id,
                "task_id": a.task_id,
                "skills_contributed": list(a.skills_contributed)
            } for a in all_assignments
        ]
    }
    return (len(any_unsat) == 0), result


def can_approve_pto_strict(
    person_id: str,
    pto_days: List[Union[date, str]],
    people: List[Union[Person, dict]],
    tasks: List[Union[Task, dict]],
    now_epoch: int,
    base_store: Union[PlanStore, dict, str],
    baseline_pto_map: Optional[Dict[Union[date, str], List[Union[Person, str, dict]]]] = None,
    cohort_pto_requests: Optional[Dict[str, List[Union[date, str]]]] = None,
) -> Tuple[bool, Dict]:
    """
    Strict feasibility:
      - Clones the provided PlanStore (so rolling 7-day limits from history apply)
      - Merges baseline PTO + candidate PTO + cohort PTO
      - Schedules all affected weeks with the deterministic solver
      - Returns (ok, result_json) + UNSAT details
    """
    parsed_people = [custom_person_constructor(p) for p in people]
    parsed_tasks = [custom_task_constructor(t) for t in tasks]
    parsed_store = custom_planstore_constructor(base_store)
    parsed_pto_days: List[date] = []
    for d in pto_days:
        parsed_pto_days.append(date.fromisoformat(d) if isinstance(d, str) else d)
    if not parsed_pto_days:
        return True, {"message": "No PTO days provided."}

    candidate_map = {d: [person_id] for d in parsed_pto_days}
    cohort_map: Dict[Union[date, str], List[Union[Person, str, dict]]] = {}
    if cohort_pto_requests:
        for pid, days in cohort_pto_requests.items():
            for d in days:
                cohort_map.setdefault(d, []).append(pid)

    combined_pto = _merge_pto_maps(baseline_pto_map, candidate_map, cohort_map)

    # Clone store to avoid mutating live cache
    temp_store = custom_planstore_constructor(parsed_store.to_json())

    # Determine affected span
    first = min(combined_pto.keys())
    last = max(combined_pto.keys())
    start_wk = start_of_week(first, week_start=0)
    end_wk = start_of_week(last, week_start=0)

    ws = WeeklyScheduler(parsed_people, parsed_tasks, temp_store, tz_offset_hours=0)
    all_assignments: List[Assignment] = []
    any_unsat: List[Tuple[date, Dict[str, Dict[str, int]]]] = []
    cur = start_wk
    while cur <= end_wk:
        a, u = ws.schedule_week(cur, now_epoch, pto_map=combined_pto)
        all_assignments.extend(a)
        any_unsat.extend(u)
        cur += timedelta(days=7)

    result = {
        "pto_person_id": person_id,
        "pto_days": [d.isoformat() for d in sorted(set(parsed_pto_days))],
        "feasible": len(any_unsat) == 0,
        "unsatisfied": [(d.isoformat(), deficits) for (d, deficits) in any_unsat],
        "assignments": [
            {"date": x.day.isoformat(), "person_id": x.person_id, "task_id": x.task_id}
            for x in all_assignments
        ],
        "combined_pto_map": {d.isoformat(): ids for d, ids in combined_pto.items()},
    }
    return (len(any_unsat) == 0), result


# ---------- Department stratification (siloed; no cross-dept staff) ----------
def schedule_all_departments_week(
    week_start_day: date,
    now_epoch: int,
    get_all_departments: Callable[[], List[str]],
    get_employees_from_dept: Callable[[str], List[Union[Person, dict]]],
    get_tasks_from_dept: Callable[[str], List[Union[Task, dict]]],
    get_planstore_for_dept: Callable[[str], Union[PlanStore, dict, str]],
    get_pto_map_for_dept: Optional[Callable[[str], Optional[Dict[Union[date, str], List[Union[Person, str, dict]]]]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Schedules each department independently with its own PlanStore and PTO map.
    Staff do NOT cross departments; each run only sees that dept's people/tasks.
    """
    results: Dict[str, Dict[str, Any]] = {}
    for dept in sorted(get_all_departments()):
        people = [custom_person_constructor(p) for p in get_employees_from_dept(dept)]
        tasks  = [custom_task_constructor(t) for t in get_tasks_from_dept(dept)]
        store  = custom_planstore_constructor(get_planstore_for_dept(dept))
        pto    = get_pto_map_for_dept(dept) if get_pto_map_for_dept else None
        ws = WeeklyScheduler(people, tasks, store, tz_offset_hours=0)
        assigns, unsat = ws.schedule_week(week_start_day, now_epoch, pto_map=_merge_pto_maps(pto) if pto else None)
        results[dept] = {"assignments": assigns, "unsatisfied": unsat, "plan_store": store}
    return results


# ----------------
# Optional MCP API
# ----------------
if MCP_AVAILABLE and mcp:

    # @mcp.tool()
    # def approve_pto_request(
    #     person_id: str,
    #     pto_days: List[str],  # ISO dates
    #     people: List[dict],
    #     tasks: List[dict],
    #     now_epoch: int,
    #     week_start: Optional[str] = None,
    #     baseline_pto_map: Optional[Dict[str, List[Union[str, dict]]]] = None,
    # ) -> Dict[str, Any]:
    #     try:
    #         feasible, result = can_approve_pto(
    #             person_id=person_id,
    #             pto_days=pto_days,   # type: ignore
    #             people=people,       # type: ignore
    #             tasks=tasks,         # type: ignore
    #             now_epoch=now_epoch,
    #             week_start=week_start,
    #             baseline_pto_map=baseline_pto_map  # ALWAYS considered
    #         )
    #         return {"success": True, "feasible": feasible, "result": result}
    #     except Exception as e:
    #         logger.error(f"Error in approve_pto_request: {e}")
    #         return {"success": False, "error": str(e)}

    @mcp.tool()
    def approve_pto_request_strict(
        person_id: str,
        pto_days: List[str],   # ISO dates
        people: List[dict],
        tasks: List[dict],
        now_epoch: int,
        base_store: Union[dict, str],  # PlanStore as dict or json
        baseline_pto_map: Optional[Dict[str, List[Union[str, dict]]]] = None,
        cohort_pto_requests: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        try:
            feasible, result = can_approve_pto_strict(
                person_id=person_id,
                pto_days=pto_days,         # type: ignore
                people=people,             # type: ignore
                tasks=tasks,               # type: ignore
                now_epoch=now_epoch,
                base_store=base_store,     # type: ignore
                baseline_pto_map=baseline_pto_map,
                cohort_pto_requests=cohort_pto_requests,
            )
            return {"success": True, "feasible": feasible, "result": result}
        except Exception as e:
            logger.error(f"Error in approve_pto_request_strict: {e}")
            return {"success": False, "error": str(e)}
else:
    logger.warning("FastMCP not available - MCP handlers not registered")
