# topdb.py
from info import DATABASE_URI
import motor.motor_asyncio
import uuid

class JsTopDB:
    def __init__(self, db_uri):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(db_uri)
        self.db = self.client["movie_series_db"]
        self.collection = self.db["movie_series"]

    async def set_movie_series_names(self, names, group_id):
        if not names or not isinstance(names, str):
            return
        movie_series_list = [name.strip() for name in names.split(",") if name.strip()]
        for name in movie_series_list:
            await self.collection.update_one(
                {"name": name, "group_id": group_id},
                {"$inc": {"search_count": 1}},
                upsert=True
            )

    async def get_movie_series_names(self, group_id):
        cursor = self.collection.find({"group_id": group_id}).sort("search_count", -1)
        return [document["name"] async for document in cursor]

    async def clear_movie_series_names(self, group_id):
        await self.collection.delete_many({"group_id": group_id})

movie_series_db = JsTopDB(DATABASE_URI)
