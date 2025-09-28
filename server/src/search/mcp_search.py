import datetime, calendar
from src.search._search import HorizonSchedulerPTO, HorizonSchedule
from typing import Union, List, Dict, Any, Tuple, Set, Optional
from src import _TZ, logger

#TODO database abstractions 
get_all_organization_departments = lambda: [None,] * 6
get_people_from_department = lambda dept: [None] * 6
get_all_tasks_from_department = lambda dept, start_date, end_date: [None] * 6

cache_schedule = lambda dept, month, year, schedule: None
load_cached_schedule = lambda dept, month, year: None


#HELPERS
def validate(builded_schedule: HorizonSchedule): #returns validation on the schedule
    return builded_schedule, builded_schedule.feasible

#start to generate a bunch of schedule data for a organization

#RUNS ON-LOAD FOR HTTP ON MNGR SCREEN
def build_full_month_schedule_with_pto(month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a full month (all departments) schedule with PTO (Paid Time Off) considerations.

    Args:
        month_date (datetime.date): The date for the month to build the schedule for.
        pto_map (Optional[Dict[datetime.date, Set[str]]]): A mapping of PTO dates to employee IDs.
    """
    depts = get_all_organization_departments()
    all_dept_month_schedule = []
    for dept in depts:
        people = get_people_from_department(dept)
        first = month_date.replace(day=1)
        last = (first + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1) #next month first - 1 day = last of this month
        tasks = get_all_tasks_from_department(dept, first, last)
        all_dept_month_schedule.append(build_month_schedule_with_pto_from_items(people, tasks, month_date, pto_map))

#DEPLOY TO MCP
def test_employee_pto(department: object, employee: object, date: datetime.date):
    """Tests the PTO (Paid Time Off) functionality for employees in a specific department.


    Args:
        department (object): The department to test the PTO of a specific employee.
        employee (object): The employee to test the PTO for.
        date (datetime.date): The date to test the PTO for.
    """

    schedule, validation = validate(build_month_schedule_with_pto_from_items(
        get_people_from_department(department), 
        get_all_tasks_from_department(department, date, date),
        date,
        {date: {employee.id,}} #TODO dict.update from cached pto data in THIS dept, in THIS timeframe
    ))

    if not validation:
        #TODO mcp bad-ack 
        pass
    
    else:
        cache_schedule(department, date.month, date.year, schedule)

def build_month_schedule_with_pto_from_items(people: List[object], tasks: List[object], month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a monthly schedule (specific department) with PTO (Paid Time Off) considerations FROM people and task lists.

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