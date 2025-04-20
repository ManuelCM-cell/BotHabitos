from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["habits_db"]
collection = db["habits"]

def get_user_habits(user_id):
    user = collection.find_one({"user_id": user_id})
    return user["habits"] if user else []

def save_user_habits(user_id, habits):
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"habits": habits}},
        upsert=True
    )
