# users_chats_db.py
import datetime
import pytz
from motor.motor_asyncio import AsyncIOMotorClient
from info import SETTINGS, IS_PM_SEARCH, IS_SEND_MOVIE_UPDATE, PREMIUM_POINT, REF_PREMIUM, DATABASE_NAME, DATABASE_URI

client = AsyncIOMotorClient(DATABASE_URI)
mydb = client[DATABASE_NAME]
fsubs = client['fsubs']

class Database:
    default = SETTINGS.copy()
    def __init__(self):
        self.col = mydb.users
        self.grp = mydb.groups
        self.misc = mydb.misc
        self.verify_id = mydb.verify_id
        self.users = mydb.users  # Fixed typo: uersz -> users
        self.req = mydb.requests
        self.pmMode = mydb.pmMode
        self.jisshu_ads_link = mydb.jisshu_ads_link
        self.movies_update_channel = mydb.movies_update_channel
        self.botcol = mydb.botcol
        self.grp_and_ids = fsubs.grp_and_ids

    async def add_user(self, id, name):
        user = {"id": id, "name": name, "point": 0, "ban_status": {"is_banned": False, "ban_reason": ""}}
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        return bool(await self.col.find_one({'id': int(id)}))

    async def get_settings(self, id):
        chat = await self.grp.find_one({'id': int(id)})
        if not chat:
            await self.grp.update_one({'id': int(id)}, {'$set': {'settings': self.default}}, upsert=True)
            return self.default
        return chat.get('settings', self.default)

    async def update_point(self, id):
        await self.col.update_one({'id': id}, {'$inc': {'point': 100}})
        user = await self.col.find_one({'id': id})
        if user['point'] >= PREMIUM_POINT:
            seconds = REF_PREMIUM * 24 * 60 * 60
            expiry_time = (await self.users.find_one({'id': id}) or {}).get('expiry_time', datetime.datetime.now())
            expiry_time += datetime.timedelta(seconds=seconds)
            await self.users.update_one({'id': id}, {'$set': {'expiry_time': expiry_time}}, upsert=True)
            await self.col.update_one({'id': id}, {'$set': {'point': 0}})

    async def has_premium_access(self, user_id):
        user = await self.users.find_one({"id": user_id})
        if user and (expiry := user.get("expiry_time")) and datetime.datetime.now() <= expiry:
            return True
        return False

    # Simplified Verification
    async def is_user_verified(self, user_id):
        user = await self.misc.find_one({"user_id": int(user_id)}) or {
            "user_id": user_id,
            "last_verified": datetime.datetime(2020, 1, 1, tzinfo=pytz.timezone('Asia/Kolkata'))
        }
        last_verified = user["last_verified"]
        current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        return (current_time - last_verified).total_seconds() < 24 * 60 * 60  # 24 hours validity

    async def update_notcopy_user(self, user_id, value: dict):
        await self.misc.update_one({"user_id": int(user_id)}, {"$set": value}, upsert=True)

    async def create_verify_id(self, user_id: int, hash):
        return await self.verify_id.insert_one({"user_id": user_id, "hash": hash, "verified": False})

    async def get_verify_id_info(self, user_id: int, hash):
        return await self.verify_id.find_one({"user_id": user_id, "hash": hash})

    async def update_verify_id_info(self, user_id, hash, value: dict):
        return await self.verify_id.update_one({"user_id": user_id, "hash": hash}, {"$set": value})

db = Database()
