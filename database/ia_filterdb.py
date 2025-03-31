import re
import base64
from struct import pack
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI_FILES, DATABASE_NAME_FILES, COLLECTION_NAME

class FilesDB:
    def __init__(self):
        self.client = AsyncIOMotorClient(DATABASE_URI_FILES)
        self.db = self.client[DATABASE_NAME_FILES]
        self.media_col = self.db[COLLECTION_NAME]

    @staticmethod
    def encode_file_id(s: bytes) -> str:
        r = b""
        n = 0
        for i in s + bytes([22]) + bytes([4]):
            if i == 0:
                n += 1
            else:
                if n:
                    r += b"\x00" + bytes([n])
                    n = 0
                r += bytes([i])
        return base64.urlsafe_b64encode(r).decode().rstrip("=")

    @staticmethod
    def encode_file_ref(file_ref: bytes) -> str:
        return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

    def unpack_new_file_id(self, new_file_id):
        decoded = FileId.decode(new_file_id)
        file_id = self.encode_file_id(
            pack("<iiqq", int(decoded.file_type), decoded.dc_id, decoded.media_id, decoded.access_hash)
        )
        file_ref = self.encode_file_ref(decoded.file_reference)
        return file_id, file_ref

    async def save_file(self, media):
        file_id, file_ref = self.unpack_new_file_id(media.file_id)
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        try:
            doc = {
                "_id": file_id,
                "file_ref": file_ref,
                "file_name": file_name,
                "file_size": media.file_size,
                "mime_type": media.mime_type,
                "caption": media.caption.html if media.caption else None
            }
            await self.media_col.insert_one(doc)
            return "suc"
        except DuplicateKeyError:
            return "dup"

    async def get_search_results(self, query, max_results=10, offset=0):
        regex = re.compile(query.strip(), flags=re.IGNORECASE)
        cursor = self.media_col.find({"file_name": regex}).skip(offset).limit(max_results)
        return await cursor.to_list(length=max_results)

files_db = FilesDB()
