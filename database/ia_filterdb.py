# ia_filterdb.py
import logging
import re
import base64
from struct import pack
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import FILE_DATABASE_URI, FILE_DATABASE_NAME, COLLECTION_NAME, MAX_BTN

client = AsyncIOMotorClient(FILE_DATABASE_URI)
mydb = client[FILE_DATABASE_NAME]
instance = Instance.from_db(mydb)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    file_type = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME

async def get_files_db_size():
    return (await mydb.command("dbstats"))['dataSize']

async def save_file(media):
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
            file_type=media.mime_type.split('/')[0] if media.mime_type else None
        )
        await file.commit()
        print(f"{file_name} saved to database")
        return 'suc'
    except ValidationError as e:
        print(f"Validation error saving {file_name}: {e}")
        return 'err'
    except DuplicateKeyError:
        print(f"{file_name} already exists in database")
        return 'dup'

async def get_search_results(query, max_results=MAX_BTN, offset=0, lang=None):
    query = query.strip()
    raw_pattern = '.' if not query else (r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])' if ' ' not in query else query.replace(' ', r'.*[\s\.\+\-_]'))
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(query), flags=re.IGNORECASE)
    
    filter = {'file_name': regex}
    cursor = Media.find(filter).sort('$natural', -1)
    
    if lang:
        lang_files = [file async for file in cursor if lang.lower() in file.file_name.lower()]
        files = lang_files[offset:offset + max_results]
        total_results = len(lang_files)
    else:
        files = await cursor.skip(offset).limit(max_results).to_list(length=max_results)
        total_results = await Media.count_documents(filter)
    
    next_offset = offset + max_results if offset + max_results < total_results else ''
    return files, next_offset, total_results

async def get_bad_files(query, file_type=None, offset=0):
    query = query.strip()
    raw_pattern = '.' if not query else (r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])' if ' ' not in query else query.replace(' ', r'.*[\s\.\+\-_]'))
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        return [], 0
    
    filter = {'file_name': regex}
    if file_type:
        filter['file_type'] = file_type
    
    cursor = Media.find(filter).sort('$natural', -1)
    total_results = await Media.count_documents(filter)
    files = await cursor.to_list(length=total_results)
    return files, total_results

async def get_file_details(query):
    return await Media.find({'file_id': query}).to_list(length=1)

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

def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(pack("<iiqq", decoded.file_type, decoded.dc_id, decoded.media_id, decoded.access_hash))
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
