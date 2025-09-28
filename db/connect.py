from pymongo import MongoClient

uri = "mongodb+srv://au249_db_user:QdQk1laMIwkj303c@cluster0.qimgmdc.mongodb.net/"

client = MongoClient(uri)

db = client['pto_db']
user_profile_collection = db['user_profile']
dept_collection = db['departments']
tasks_collection = db['tasks']

# make skills a frozen set

user_profile_doc = {
    "name": "Victor Jimenez",
    "image": "victor_jimenez.jpg", 
    "skills": frozenset(["Databases", "SQL", "Python", "Unix", "AWS", "TensorFlow", "Pytorch" ]),
    "dept": "Engineering", 
    "age": "7",
}


dept_collection_doc = {
    "name": "Engineering",
    "statistics": {
        "numemployees": 7,
        "numtasks": 10,
    }  
}

tasks_doc = {
    "name": "Set up database on servers", 
    "description": "Engineering team needs to set up cloud database on AWS for engineering team datastore", 
    "skills": frozenset(["Databases", "SQL", "Python", "Unix", "AWS" ]),
    "start_date": "September 25, 2025", 
    "end_date": "October 15, 2025", 
    "requirements": {
        "Databases": 1,
        "SQL": 1
    }
}



#user_profile_collection.insert_one(user_profile_doc)
dept_collection.insert_one(dept_collection_doc)
#tasks_collection.insert_one(tasks_doc)

