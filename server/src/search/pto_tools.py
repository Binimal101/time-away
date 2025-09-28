from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional, Union, Iterable, Set, Any

# Import from centralized src module
from src import (
    Person, Task, Assignment, logger, start_of_week, daterange
)
from src.search._search import (
    PlanStore, WeeklyScheduler, DaySolver, is_task_active_on_day, 
    pretty_assignments, normalize_pto_map
)

# FastMCP imports
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

# Logger is imported from src module

# Custom object constructors - YOU will implement these
def custom_person_constructor(data: Union[Person, dict]) -> Person:
    """Parse Person from dict if needed"""
    if isinstance(data, Person):
        return data
    # YOU implement this parsing logic
    raise NotImplementedError("You need to implement Person parsing from dict")

def custom_task_constructor(data: Union[Task, dict]) -> Task:
    """Parse Task from dict if needed"""
    if isinstance(data, Task):
        return data
    # YOU implement this parsing logic
    raise NotImplementedError("You need to implement Task parsing from dict")

def custom_planstore_constructor(data: Union[PlanStore, dict]) -> PlanStore:
    """Parse PlanStore from dict if needed"""
    if isinstance(data, PlanStore):
        return data
    # YOU implement this parsing logic
    raise NotImplementedError("You need to implement PlanStore parsing from dict")

def _strip_cache_and_test_week(people: List[Person],
                               tasks: List[Task],
                               week_start: date,
                               now_epoch: int,
                               pto_map: Optional[Dict[date, List[Union[Person, str]]]] = None
                               ) -> Tuple[bool, List[Assignment], List[Tuple[date, Dict[str, Dict[str, int]]]]]:
    """
    Helper: run one-week schedule with NO prior PlanStore usage (fresh)
    ignoring rolling 7-day constraint pressure from history, as a feasibility test.
    """
    tmp_store = PlanStore()
    sched = WeeklyScheduler(people, tasks, tmp_store, tz_offset_hours=0)
    assigns, unsat = sched.schedule_week(week_start, now_epoch, pto_map=pto_map)
    feasible = len(unsat) == 0
    return feasible, assigns, unsat


def can_approve_pto(person_id: str,
                    pto_days: List[Union[date, str]],
                    people: List[Union[Person, dict]],
                    tasks: List[Union[Task, dict]],
                    now_epoch: int,
                    week_start: Optional[Union[date, str]] = None,
                    strict_rolling: bool = False
                    ) -> Tuple[bool, Dict]:
    """
    Return (ok, result_json).
    OK if all affected days remain satisfiable when the person is marked PTO on those days.

    - By default, this check runs WITHOUT historical cache pressure (strict_rolling=False)
      to answer resource-feasibility: "can others cover?"
    - If strict_rolling=True, we keep the rolling 7-day constraint by using a preserved PlanStore
      (caller must pass a non-empty store via kwargs in future extension). For now we stick to the simple mode.
    """
    # Parse inputs
    parsed_pto_days = []
    for d in pto_days:
        if isinstance(d, str):
            parsed_pto_days.append(date.fromisoformat(d))
        else:
            parsed_pto_days.append(d)
    
    parsed_people = [custom_person_constructor(p) for p in people]
    parsed_tasks = [custom_task_constructor(t) for t in tasks]
    
    if week_start and isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)
    
    if not parsed_pto_days:
        return True, {"message": "No PTO days provided."}

    # Construct a PTO map for the window covering the PTO days (expand to full weeks to be safe)
    pto_map = {}
    for d in parsed_pto_days:
        pto_map.setdefault(d, []).append(person_id)

    # Plan the full weeks that touch the PTO
    first = min(parsed_pto_days)
    last = max(parsed_pto_days)
    start_wk = start_of_week(first, week_start=0)
    end_wk = start_of_week(last, week_start=0)

    all_assignments: List[Assignment] = []
    any_unsat: List[Tuple[date, Dict[str, Dict[str, int]]]] = []

    cur = start_wk
    while cur <= end_wk:
        ok, assigns, unsat = _strip_cache_and_test_week(parsed_people, parsed_tasks, cur, now_epoch, pto_map=pto_map)
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


def generate_month_view(year: int,
                        month: int,
                        people: List[Union[Person, dict]],
                        tasks: List[Union[Task, dict]],
                        store: Union[PlanStore, dict],
                        now_epoch: int,
                        pto_map: Optional[Dict[Union[date, str], List[Union[Person, str, dict]]]] = None
                        ) -> Tuple[List[Assignment], List[Tuple[date, Dict[str, Dict[str, int]]]]]:
    """
    Produce a schedule for the entire calendar month.
    Uses the provided store (so rolling 7-day limits are enforced across weeks).
    Does NOT overwrite incoming variables beyond store.commit() as days succeed.
    """
    # Parse inputs
    parsed_people = [custom_person_constructor(p) for p in people]
    parsed_tasks = [custom_task_constructor(t) for t in tasks]
    parsed_store = custom_planstore_constructor(store)
    
    # Parse PTO map if provided
    parsed_pto_map = None
    if pto_map:
        parsed_pto_map = {}
        for d, plist in pto_map.items():
            parsed_date = date.fromisoformat(d) if isinstance(d, str) else d
            parsed_people_list = []
            for p in plist:
                if isinstance(p, dict):
                    parsed_people_list.append(custom_person_constructor(p))
                elif isinstance(p, str):
                    parsed_people_list.append(p)
                else:
                    parsed_people_list.append(p)
            parsed_pto_map[parsed_date] = parsed_people_list
    
    # First day and last day of month
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)

    # Iterate week-by-week to keep consistency
    ws = WeeklyScheduler(parsed_people, parsed_tasks, parsed_store, tz_offset_hours=0)
    all_assignments: List[Assignment] = []
    unsat_all: List[Tuple[date, Dict[str, Dict[str, int]]]] = []

    # Advance from the Monday on/before the first of the month to the Sunday on/after the last
    cur = start_of_week(first, week_start=0)
    while cur <= last:
        assigns, unsat = ws.schedule_week(cur, now_epoch, pto_map=parsed_pto_map)
        all_assignments.extend(assigns)
        unsat_all.extend(unsat)
        cur += timedelta(days=7)

    return all_assignments, unsat_all


# FastMCP Handlers
if MCP_AVAILABLE and mcp:
    
    @mcp.tool()
    def approve_pto_request(
        person_id: str,
        pto_days: List[str],  # ISO format dates
        people: List[dict],   # Person objects as dicts
        tasks: List[dict],    # Task objects as dicts
        now_epoch: int,
        week_start: Optional[str] = None,  # ISO format date
        strict_rolling: bool = False
    ) -> Dict[str, Any]:
        """
        FastMCP handler for can_approve_pto.
        Check if a person's PTO request can be approved without causing scheduling conflicts.
        
        Args:
            person_id: ID of the person requesting PTO
            pto_days: List of dates in ISO format (YYYY-MM-DD) for PTO
            people: List of Person objects as dictionaries
            tasks: List of Task objects as dictionaries  
            now_epoch: Current timestamp in epoch seconds
            week_start: Optional start of week date in ISO format
            strict_rolling: Whether to enforce strict rolling constraints
            
        Returns:
            Dictionary with feasibility result and details
        """
        try:
            feasible, result = can_approve_pto(
                person_id=person_id,
                pto_days=pto_days,  # type: ignore
                people=people,  # type: ignore
                tasks=tasks,  # type: ignore
                now_epoch=now_epoch,
                week_start=week_start,
                strict_rolling=strict_rolling
            )
            return {"success": True, "feasible": feasible, "result": result}
        except Exception as e:
            logger.error(f"Error in approve_pto_request: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_monthly_schedule(
        year: int,
        month: int,
        people: List[dict],   # Person objects as dicts
        tasks: List[dict],    # Task objects as dicts
        store: dict,          # PlanStore object as dict
        now_epoch: int,
        pto_map: Optional[Dict[str, List[Union[str, dict]]]] = None  # date_iso -> [person_ids or person_dicts]
    ) -> Dict[str, Any]:
        """
        FastMCP handler for generate_month_view.
        Generate a schedule for an entire calendar month.
        
        Args:
            year: Year for the schedule
            month: Month (1-12) for the schedule
            people: List of Person objects as dictionaries
            tasks: List of Task objects as dictionaries
            store: PlanStore object as dictionary
            now_epoch: Current timestamp in epoch seconds
            pto_map: Optional mapping of ISO dates to person IDs/dicts on PTO
            
        Returns:
            Dictionary with assignments and unsatisfied requirements
        """
        try:
            assignments, unsat = generate_month_view(
                year=year,
                month=month,
                people=people,  # type: ignore
                tasks=tasks,  # type: ignore
                store=store,  # type: ignore
                now_epoch=now_epoch,
                pto_map=pto_map  # type: ignore
            )
            
            # Convert assignments to serializable format
            serialized_assignments = [
                {
                    "day": a.day.isoformat(),
                    "person_id": a.person_id,
                    "task_id": a.task_id,
                    "skills_contributed": list(a.skills_contributed)
                } for a in assignments
            ]
            
            # Convert unsatisfied to serializable format
            serialized_unsat = [
                {"date": d.isoformat(), "deficits": deficits}
                for d, deficits in unsat
            ]
            
            return {
                "success": True,
                "assignments": serialized_assignments,
                "unsatisfied": serialized_unsat
            }
        except Exception as e:
            logger.error(f"Error in generate_monthly_schedule: {e}")
            return {"success": False, "error": str(e)}

else:
    logger.warning("FastMCP not available - MCP handlers not registered")