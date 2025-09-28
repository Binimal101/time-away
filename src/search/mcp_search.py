import datetime, calendar
from src.search._search import Person, Task, HorizonScheduler

#TODO database abstractions 
get_all_organization_departments = lambda: [None,] * 6
get_people_from_organization = lambda org: [None] * 6
get_all_tasks_from_organization = lambda org, start_date, end_date: [None] * 6

#start generate a bunch of schedule data for a organization
from src.search._search import HorizonScheduler

today = datetime.date.today()
first_of_month = today.replace(day=1)
last_day = calendar.monthrange(today.year, today.month)[1]
last_of_month = today.replace(day=last_day)

    

def fill_month_schedule():
    """
    Generates a schedule for all departments in an organization for the current month.
    """
    month_span_days = (last_of_month - first_of_month).days + 1

    #goes dept for dept, gets all people and tasks, generates a schedule for the MONTH (monthview generator)
    for org in get_all_organization_departments():  
        for i in range(1, 6):
            schedule = abstract_output(HorizonScheduler(
                people=get_people_from_organization(org), # type: ignore
                tasks=get_all_tasks_from_organization(org, first_of_month, last_of_month), # type: ignore
                start_day=first_of_month,
                span_days=month_span_days,
                current_ts=today, # type: ignore
                allow_future=True
            ))