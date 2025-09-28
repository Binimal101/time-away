import datetime, calendar
from src.search._search import Person, Task, HorizonScheduler, HorizonSchedule
from typing import Union, List, Dict, Any, Tuple

#TODO database abstractions 
get_all_organization_departments = lambda: [None,] * 6
get_people_from_organization = lambda org: [None] * 6
get_all_tasks_from_organization = lambda org, start_date, end_date: [None] * 6

cache_schedule = lambda org, month, year, schedule: None
load_cached_schedule = lambda org, month, year: None

#start to generate a bunch of schedule data for a organization

def generate_month_schedule_against_PTO_request(PTO_requests: Dict[Tuple[datetime.date], List[object]], cur_date: datetime.date = datetime.date.today()):
    """Generates a monthly schedule while considering PTO requests. DOES NOT CACHE. TODO lookback
    
    Args:
        PTO_requests (Dict[Tuple[datetime.date], List[object]]): A list of PTO dates that match to employees.
        cur_date (datetime.date, optional): The current date. Defaults to datetime.date.today().
    """
    monthly_departmental_schedules: Dict[object, List[HorizonSchedule]] = dict()
    for dept in get_all_organization_departments():
        month_schedule: List[HorizonSchedule] = list()
        
        #DO SEQUENCTIAL DAYS AND DISINCLUDE PTO DAY'S IN THE MONTH
        #WE DO NOT TAKE INTO ACCOUNT THE POSSIBILITY OF PTO REQUESTS SPANNING MONTHS
        
        disinclude_employeeid_from_working_today = set()

        #TODO lookback here and preset employees preworked_in_last_7
        for i_day in range(1, calendar.monthrange(cur_date.year, cur_date.month)[1] + 1):
            #get day_schedules for each day in the month, disinclude PTO days for employees
            
            #grab people who may have pto on this day
            pto_people = [emp for emp, pto_dates in PTO_requests.items() if cur_date in pto_dates]
            for emp in pto_people:
                #disinclude this employee from the schedule for this day
                disinclude_employeeid_from_working_today.add(emp)

            employees = [x for x in get_people_from_organization(dept) if x.person_id not in disinclude_employeeid_from_working_today]  # type: ignore
            tasks = get_all_tasks_from_organization(dept, cur_date.replace(day=i_day), cur_date.replace(day=i_day))
            
            sched = abstract_output(HorizonScheduler(
                people=employees,  # type: ignore
                tasks=tasks,  # type: ignore
                start_day=cur_date.replace(day=i_day),
                span_days=1,
                current_ts=cur_date,
                allow_future=True
            ))

def fill_month_schedule(today: datetime.date = datetime.date.today()):
    """TODO check cached dates against last 7 days to pre-populate preworked_in_last_7 for employees.

    Generates a schedule for all departments in an organization for the month specified at a generic date (in the month).
    Defaults to filling current month
    """
    first_of_month = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    last_of_month = today.replace(day=last_day)

    month_span_days = (last_of_month - first_of_month).days + 1

    #goes dept for dept, gets all people and tasks, generates a schedule for the MONTH (monthview generator)
    for dept in get_all_organization_departments():  
        if not load_cached_schedule(dept, today.month, today.year):
            schedule = abstract_output(HorizonScheduler(
                people=get_people_from_organization(dept), # type: ignore
                tasks=get_all_tasks_from_organization(dept, first_of_month, last_of_month), # type: ignore
                start_day=first_of_month,
                span_days=month_span_days,
                current_ts=today, # type: ignore
                allow_future=True
            ))

            cache_schedule(dept, today.month, today.year, schedule)