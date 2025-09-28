import pydantic as pydantic

class UserProfile(pydantic.BaseModel):
    name: str
    image: str
    department: str
    skills: tuple[str, ...]
    age: int

class Department(pydantic.BaseModel):
    name: str
    statistics: dict[str, int]

class Task(pydantic.BaseModel):
    name: str
    description: str
    skills: tuple[str, ...]
    start_date: str
    end_date: str
    requirements: dict[str, int]
