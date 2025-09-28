'''
Victor's Updated FILE.
I did not pull beforehand so I did not see you edits, and made adjustemets to the old
file, which means we need to go over this a bit
helper functions and mongodb work :)

import datetime, calendar
from typing import Dict, List
from src.search._search import Person, Task, HorizonScheduler
from src.db.helper_functions import (
    get_all_organization_departments,
    get_people_from_organization, 
    get_all_tasks_from_organization,
    abstract_output
)

today = datetime.date.today()
first_of_month = today.replace(day=1)
last_day = calendar.monthrange(today.year, today.month)[1]
last_of_month = today.replace(day=last_day)
current_ts = int(datetime.datetime.combine(today, datetime.time()).timestamp())


def fill_month_schedule() -> Dict[str, List[Dict]]:
    """
    Generates a schedule for all departments in an organization for the current month.
    
    Returns:
        Dict[str, List[Dict]]: Dictionary mapping department names to lists of schedule results
    """
    month_span_days = (last_of_month - first_of_month).days + 1
    all_schedules = {}

    # Goes dept for dept, gets all people and tasks, generates a schedule for the MONTH
    for org in get_all_organization_departments():
        print(f"Processing department: {org}")
        
        people = get_people_from_organization(org)
        tasks = get_all_tasks_from_organization(org, first_of_month, last_of_month)
        
        if not people:
            print(f"  No people found in {org}, skipping...")
            continue
            
        if not tasks:
            print(f"  No tasks found for {org} in date range, skipping...")
            continue
        
        org_schedules = []
        
        # Generate multiple schedule variations (the loop from 1 to 6 seems to be for different scenarios)
        for i in range(1, 6):
            try:
                scheduler = HorizonScheduler(
                    people=people,
                    tasks=tasks,
                    start_day=first_of_month,
                    span_days=month_span_days,
                    current_ts=current_ts,
                    allow_future=True
                )
                
                schedule_result = abstract_output(scheduler)
                schedule_result['variation'] = i
                schedule_result['department'] = org
                schedule_result['people_count'] = len(people)
                schedule_result['tasks_count'] = len(tasks)
                
                org_schedules.append(schedule_result)
                
                print(f"  Variation {i}: Feasible={schedule_result['feasible']}, "
                      f"Assignments={schedule_result['total_assignments']}")
                
            except Exception as e:
                print(f"  Error in variation {i}: {e}")
                continue
        
        all_schedules[org] = org_schedules
    
    return all_schedules


def get_best_schedule_for_department(department: str) -> Dict:
    """
    Gets the best (most feasible) schedule for a specific department.
    
    Args:
        department (str): Department name
        
    Returns:
        Dict: Best schedule result for the department
    """
    people = get_people_from_organization(department)
    tasks = get_all_tasks_from_organization(department, first_of_month, last_of_month)
    
    if not people or not tasks:
        return {
            "feasible": False,
            "error": "No people or tasks available",
            "department": department
        }
    
    month_span_days = (last_of_month - first_of_month).days + 1
    
    try:
        scheduler = HorizonScheduler(
            people=people,
            tasks=tasks,
            start_day=first_of_month,
            span_days=month_span_days,
            current_ts=current_ts,
            allow_future=True
        )
        
        result = abstract_output(scheduler)
        result['department'] = department
        result['people_count'] = len(people)
        result['tasks_count'] = len(tasks)
        
        return result
        
    except Exception as e:
        return {
            "feasible": False,
            "error": str(e),
            "department": department
        }
'''
import datetime, calendar
from src.search._search import HorizonSchedulerPTO, HorizonSchedule
from typing import Union, List, Dict, Any, Tuple, Set, Optional
from src import _TZ, logger

#TODO database abstractions 
get_all_organization_departments = lambda: [None,] * 6
get_people_from_organization = lambda org: [None] * 6
get_all_tasks_from_organization = lambda org, start_date, end_date: [None] * 6

cache_schedule = lambda org, month, year, schedule: None
load_cached_schedule = lambda org, month, year: None

#start to generate a bunch of schedule data for a organization

def build_full_month_schedule_with_pto(month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a monthly schedule with PTO (Paid Time Off) considerations. FULL month for entire org, all departments."""
    depts = get_all_organization_departments()

    for dept in depts:
        people = get_people_from_organization(dept)
        tasks = get_all_tasks_from_organization(dept, first, last)
        build_month_schedule_with_pto_from_items(people, tasks, month_date, pto_map)

def build_month_schedule_with_pto_from_items(people: List[object], tasks: List[object], month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a monthly schedule with PTO (Paid Time Off) considerations FROM people and task lists.

    Args:
        people (List[object]): _description_
        tasks (List[object]): _description_
        month_date (datetime.date): _description_
        pto_map (Optional[Dict[datetime.date, Set[str]]]): _description_

    Returns:
        _type_: _description_
    """
    first = month_date.replace(day=1)
    last = (first + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    span = (last - first).days + 1
    return HorizonSchedulerPTO(people, tasks, first, span, int(datetime.datetime.now(tz=_TZ).timestamp()), allow_future=True, pto_map=pto_map).build() # type: ignore

# def fill_month_schedule(today: datetime.date = datetime.date.today()):
#     """TODO check cached dates against last 7 days to pre-populate preworked_in_last_7 for employees.

#     Generates a schedule for all departments in an organization for the month specified at a generic date (in the month).
#     Defaults to filling current month
#     """
#     first_of_month = today.replace(day=1)
#     last_day = calendar.monthrange(today.year, today.month)[1]
#     last_of_month = today.replace(day=last_day)

#     month_span_days = (last_of_month - first_of_month).days + 1

#     #goes dept for dept, gets all people and tasks, generates a schedule for the MONTH (monthview generator)
#     for dept in get_all_organization_departments():  
#         if not load_cached_schedule(dept, today.month, today.year):
#             schedule = abstract_output(HorizonScheduler(
#                 people=get_people_from_organization(dept), # type: ignore
#                 tasks=get_all_tasks_from_organization(dept, first_of_month, last_of_month), # type: ignore
#                 start_day=first_of_month,
#                 span_days=month_span_days,
#                 current_ts=today, # type: ignore
#                 allow_future=True
#             ))

#             cache_schedule(dept, today.month, today.year, schedule)