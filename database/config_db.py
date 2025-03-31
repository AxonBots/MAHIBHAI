from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI_MAIN, DATABASE_NAME_MAIN
from datetime import datetime

class MainDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(DATABASE_URI_MAIN)
        self.db = self.client[DATABASE_NAME_MAIN]
        self.user_col = self.db["users"]
        self.config_col = self.db["config"]

    async def update_top_messages(self, user_id, message_text):
        user = await self.user_col.find_one({"user_id": user_id, "messages.text": message_text})
        if not user:
            await self.user_col.update_one(
                {"user_id": user_id},
                {"$push": {"messages": {"text": message_text, "count": 1}}},
                upsert=True
            )
        else:
            await self.user_col.update_one(
                {"user_id": user_id, "messages.text": message_text},
                {"$inc": {"messages.$.count": 1}}
            )

    async def get_top_messages(self, limit=30):
        pipeline = [
            {"$unwind": "$messages"},
            {"$group": {"_id": "$messages.text", "count": {"$sum": "$messages.count"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = await self.user_col.aggregate(pipeline).to_list(limit)
        return [result['_id'] for result in results]

    async def delete_all_messages(self):
        await self.user_col.delete_many({})

    async def update_config(self, key, value):
        await self.config_col.update_one({}, {"$set": {key: value}}, upsert=True)

    async def get_config(self, key):
        config = await self.config_col.find_one({})
        return config.get(key) if config else None

main_db = MainDB()
