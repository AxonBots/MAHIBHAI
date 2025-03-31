from pymongo import MongoClient
from info import DATABASE_URI_MAIN, DATABASE_NAME_MAIN

class ReferDB:
    def __init__(self):
        self.client = MongoClient(DATABASE_URI_MAIN)
        self.db = self.client[DATABASE_NAME_MAIN]
        self.user_col = self.db["referusers"]
        self.ref_col = self.db["refers"]

    def add_user(self, user_id):
        if not self.user_col.find_one({"user_id": user_id}):
            self.user_col.insert_one({"user_id": user_id})

    def remove_user(self, user_id):
        self.user_col.delete_one({"user_id": user_id})

    def is_user_in_list(self, user_id):
        return bool(self.user_col.find_one({"user_id": user_id}))

    def add_refer_points(self, user_id, points):
        self.ref_col.update_one(
            {"user_id": user_id},
            {"$set": {"points": points}},
            upsert=True
        )

    def get_refer_points(self, user_id):
        user = self.ref_col.find_one({"user_id": user_id})
        return user.get("points", 0) if user else 0

refer_db = ReferDB()
