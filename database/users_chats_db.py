from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI_MAIN, DATABASE_NAME_MAIN, SETTINGS
import datetime

class UserChatDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(DATABASE_URI_MAIN)
        self.db = self.client[DATABASE_NAME_MAIN]
        self.user_col = self.db["users"]
        self.group_col = self.db["groups"]

    async def add_user(self, user_id, name):
        if not await self.user_col.find_one({"id": user_id}):
            await self.user_col.insert_one({
                "id": user_id,
                "name": name,
                "ban_status": {"is_banned": False, "ban_reason": ""}
            })

    async def ban_user(self, user_id, reason):
        await self.user_col.update_one(
            {"id": user_id},
            {"$set": {"ban_status": {"is_banned": True, "ban_reason": reason}}}
        )

    async def get_ban_status(self, user_id):
        user = await self.user_col.find_one({"id": user_id})
        return user.get("ban_status", {"is_banned": False, "ban_reason": ""}) if user else None

    async def add_group(self, chat_id, title):
        if not await self.group_col.find_one({"id": chat_id}):
            await self.group_col.insert_one({
                "id": chat_id,
                "title": title,
                "settings": SETTINGS.copy()
            })

user_chat_db = UserChatDB()
