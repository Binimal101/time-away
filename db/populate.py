import sys
#sys.path.insert(1,"..")
import pydantic_types
from db.connect import get_user_profile_collection, get_dept_collection, get_tasks_collection
from pydantic_types.state_types import UserProfile, Department, Task
from faker import Faker
import random
from datetime import timedelta

# Initialize Faker
fake = Faker()

# Get collections
tasks_collection = get_tasks_collection()
user_profile_collection = get_user_profile_collection()
dept_collection = get_dept_collection()

# Clear existing data
tasks_collection.delete_many({})
user_profile_collection.delete_many({})
dept_collection.delete_many({})

# --- Generate Departments ---
departments = ["Engineering", "Marketing", "Sales", "Human Resources", "Product Management"]
for dept_name in departments:
    department = Department(
        name=dept_name,
        statistics={
            "numemployees": 0,  # Will be updated later
            "numtasks": 0  # Will be updated later
        }
    )
    dept_collection.insert_one(department.model_dump())

print("Generated 5 Departments")

# --- Generate User Profiles ---
skills_list = [
    "Python", "JavaScript", "React", "Node.js", "SQL", "MongoDB", "AWS", "Docker", "Kubernetes",
    "Terraform", "Ansible", "CI/CD", "Git", "Linux", "Windows", "Agile", "Scrum", "Jira",
    "Confluence", "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "Salesforce",
    "HubSpot", "Marketo", "Google Analytics", "SEO", "SEM", "Content Marketing", "Social Media"
]

for _ in range(20):
    department_name = random.choice(departments)
    user_profile = UserProfile(
        name=fake.name(),
        image=f"{fake.first_name().lower()}_{fake.last_name().lower()}.jpg",
        department=department_name,
        skills=tuple(random.sample(skills_list, k=random.randint(3, 7))),
        age=random.randint(22, 60)
    )
    user_profile_collection.insert_one(user_profile.model_dump())
    
    # Update department statistics
    dept_collection.update_one(
        {"name": department_name},
        {"$inc": {"statistics.numemployees": 1}}
    )

print("Generated 20 User Profiles")

# --- Generate Tasks ---
for _ in range(100):
    start_date = fake.date_between(start_date='-30d', end_date='+30d')
    end_date = start_date + timedelta(days=random.randint(5, 30))
    task_skills = tuple(random.sample(skills_list, k=random.randint(2, 5)))
    
    requirements = {skill: random.randint(1, 3) for skill in task_skills}

    task = Task(
        name=fake.bs().title(),
        description=fake.text(max_nb_chars=200),
        skills=task_skills,
        start_date=start_date.strftime("%B %d, %Y"),
        end_date=end_date.strftime("%B %d, %Y"),
        requirements=requirements
    )
    tasks_collection.insert_one(task.model_dump())

print("Generated 100 Tasks")

# Update task counts in departments (randomly for simplicity)
for _ in range(100):
    department_name = random.choice(departments)
    dept_collection.update_one(
        {"name": department_name},
        {"$inc": {"statistics.numtasks": 1}}
    )

print("Database populated successfully!")
