from pymongo import MongoClient
from env import MONGO_URL
uri = MONGO_URL

client = MongoClient(uri)

def get_db():
    return client['pto_db']

def get_user_profile_collection():
    db = get_db()
    return db['user_profile']

def get_dept_collection():
    db = get_db()
    return db['departments']

def get_tasks_collection():
    db = get_db()
    return db['tasks']

def get_all_collections():
    db = get_db()
    return db.list_collection_names()

# make skills a frozen set



