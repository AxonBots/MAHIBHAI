from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI_FILES, DATABASE_NAME_FILES
import uuid

class MediaDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(DATABASE_URI_FILES)
        self.db = self.client[DATABASE_NAME_FILES]
        self.media_col = self.db["movie_series"]

    async def set_movie_names(self, names, group_id):
        for name in names.split(","):
            await self.media_col.update_one(
                {"name": name.strip(), "group_id": group_id},
                {"$inc": {"search_count": 1}},
                upsert=True
            )

    async def get_movie_names(self, group_id):
        cursor = self.media_col.find({"group_id": group_id}).sort("search_count", -1)
        return [doc["name"] async for doc in cursor]

    async def clear_movies(self, group_id):
        await self.media_col.delete_many({"group_id": group_id})

media_db = MediaDB()
