import asyncio
import re
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions, WebAppInfo, InputMediaAnimation
from pyrogram import Client, filters, enums
from pyrogram.errors import *
from utils import temp, get_settings, is_check_admin, get_status, get_size, save_group_settings, is_req_subscribed, get_poster, get_readable_time, imdb, formate_file_name
from database.users_chats_db import db
from database.ia_filterdb import Media, get_search_results, get_bad_files, get_file_details
import random
lock = asyncio.Lock()
import traceback
from fuzzywuzzy import process
BUTTONS = {}
FILES_ID = {}
CAP = {}

from database.jsreferdb import referdb
from database.config_db import mdb
import logging
from urllib.parse import quote_plus
from Jisshu.util.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_search(client, message):
    await mdb.update_top_messages(message.from_user.id, message.text)
    bot_id = client.me.id
    user_id = message.from_user.id    
    if str(message.text).startswith('/'):
        return
    if await db.get_pm_search_status(bot_id):
        if 'hindi' in message.text.lower() or 'tamil' in message.text.lower() or 'telugu' in message.text.lower() or 'malayalam' in message.text.lower() or 'kannada' in message.text.lower() or 'english' in message.text.lower() or 'gujarati' in message.text.lower(): 
            return await auto_filter(client, message)
        await auto_filter(client, message)
    else:
        await message.reply_text("<b><i>ɪ ᴀᴍ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ. ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇꜱ ɪɴ ᴏᴜʀ ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜ ɢʀᴏᴜᴘ.</i></b>",
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜ ɢʀᴏᴜᴘ ", url=MGL)]]))

@Client.on_message(filters.group & filters.text & filters.incoming)
async def group_search(client, message):
    await mdb.update_top_messages(message.from_user.id, message.text)
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    if message.chat.id == SUPPORT_GROUP:
        if message.text.startswith("/"):
            return
        files, n_offset, total = await get_search_results(message.text, offset=0)
        if total != 0:
            link = await db.get_set_grp_links(index=1)
            msg = await message.reply_text(script.SUPPORT_GRP_MOVIE_TEXT.format(message.from_user.mention(), total),
                                           reply_markup=InlineKeyboardMarkup([
                                               [InlineKeyboardButton('ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ 😉', url=link)]
                                           ]))
            await asyncio.sleep(300)
            return await msg.delete()
        else:
            return
    if settings["auto_filter"]:
        if not user_id:
            return
        if 'hindi' in message.text.lower() or 'tamil' in message.text.lower() or 'telugu' in message.text.lower() or 'malayalam' in message.text.lower() or 'kannada' in message.text.lower() or 'english' in message.text.lower() or 'gujarati' in message.text.lower(): 
            return await auto_filter(client, message)
        elif message.text.startswith("/"):
            return
        elif re.findall(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            await message.delete()
            return await message.reply("<b>sᴇɴᴅɪɴɢ ʟɪɴᴋ ɪsɴ'ᴛ ᴀʟʟᴏᴡᴇᴅ ʜᴇʀᴇ ❌🤞🏻</b>")
        elif '@admin' in message.text.lower() or '@admins' in message.text.lower():
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            admins = []
            async for member in client.get_chat_members(chat_id=message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if not member.user.is_bot:
                    admins.append(member.user.id)
                    if member.status == enums.ChatMemberStatus.OWNER:
                        if message.reply_to_message:
                            try:
                                sent_msg = await message.reply_to_message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.reply_to_message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
                        else:
                            try:
                                sent_msg = await message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
            hidden_mentions = (f'[\u2064](tg://user?id={user_id})' for user_id in admins)
            await message.reply_text('<code>Report sent</code>' + ''.join(hidden_mentions))
            return
        else:
            try:
                await auto_filter(client, message)
            except Exception as e:
                traceback.print_exc()
                print('found err in grp search :', e)
                await message.reply_text("Kuch gadbad ho gayi bhai, thodi der baad try kar!")
    else:
        k = await message.reply_text('<b>⚠️ ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ ᴍᴏᴅᴇ ɪꜱ ᴏғғ...</b>')
        await asyncio.sleep(10)
        await k.delete()
        try:
            await message.delete()
        except:
            pass

@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('ɪɴᴠɪᴛᴇ ʟɪɴᴋ', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point')
    ],[
        InlineKeyboardButton('❌ ᴄʟᴏꜱᴇ ❌', callback_data='close_data')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    REFERRAL_IMAGES = ["https://envs.sh/7f-.jpg", "https://example.com/backup.jpg"]
    await bot.send_photo(
        chat_id=query.message.chat.id,
        photo=random.choice(REFERRAL_IMAGES),
        caption=f'<b>ʜᴀʏ ʏᴏᴜʀ ʀᴇꜰᴇʀ ʟɪɴᴋ:\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nꜱʜᴀʀᴇ ᴛʜɪꜱ ʟɪɴᴋ ᴡɪᴛʜ ʏᴏᴜʀ ꜰʀɪᴇɴᴅꜱ, ᴇᴀᴄʜ ᴛɪᴍᴇ ᴛʜᴇʏ ᴊᴏɪɴ, ʏᴏᴜ ᴡɪʟʟ ɢᴇᴛ 𝟣𝟢 ʀᴇꜰᴇʀʀᴀʟ ᴘᴏɪɴᴛꜱ ᴀɴᴅ ᴀꜰᴛᴇʀ 𝟣𝟢𝟢 ᴘᴏɪɴᴛꜱ ʏᴏᴜ ᴡɪʟʟ ɢᴇᴛ 𝟣 ᴍᴏɴᴛʜ ᴘʀᴇᴍɪᴜᴍ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.\n\n𝟣 ʀᴇꜰᴇʀ = 𝟣𝟢 ᴘᴏɪɴᴛꜱ.</b>',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    files, n_offset, total = await get_search_results(search, offset=offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    if not files:
        return
    temp.FILES_ID[key] = files
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    settings = await get_settings(query.message.chat.id)
    reqnxt = query.from_user.id if query.from_user else 0
    temp.CHAT[query.from_user.id] = query.message.chat.id
    links = ""
    for file_num, file in enumerate(files, start=offset+1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if offset != "":
        if total >= MAX_BTN:
            btn.append([
                InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
                InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
            ])
            btn.append([
                InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
            ])
        else:
            btn.append([
                InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
                InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
            ])
            btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    else:
        btn.append([InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link)])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if 0 < offset <= int(MAX_BTN):
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - int(MAX_BTN)
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"𝐏𝐀𝐆𝐄 {math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{n_offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"{math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{n_offset}")]
        )
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    await query.answer()

@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_cb_handler(client: Client, query:.CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    btn = []
    for i in range(0, len(SEASONS)-1, 3):
        btn.append([
            InlineKeyboardButton(text=SEASONS[i].title(), callback_data=f"season_search#{SEASONS[i].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=SEASONS[i+1].title(), callback_data=f"season_search#{SEASONS[i+1].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=SEASONS[i+2].title(), callback_data=f"season_search#{SEASONS[i+2].lower()}#{key}#0#{offset}#{req}"),
        ])
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ sᴇᴀsᴏɴ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^season_search#"))
async def season_search(client: Client, query: CallbackQuery):
    _, season, key, offset, orginal_offset, req = query.data.split("#")
    try:
        seas = int(season.split(' ', 1)[1])
    except (IndexError, ValueError):
        await query.answer("Season ka format galat hai bhai!", show_alert=True)
        return
    seas = f'S0{seas}' if seas < 10 else f'S{seas}'
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    files, n_offset, total = await get_search_results(f"{search} {seas}", max_results=int(MAX_BTN), offset=offset)
    files2, n_offset2, total2 = await get_search_results(f"{search} {season}", max_results=int(MAX_BTN), offset=offset)
    total += total2
    try:
        n_offset = int(n_offset)
    except:
        try:
            n_offset = int(n_offset2)
        except:
            n_offset = 0
    files = [file for file in files if re.search(seas, file.file_name, re.IGNORECASE)]
    if not files:
        files = [file for file in files2 if re.search(season, file.file_name, re.IGNORECASE)]
        if not files:
            await query.answer(f"sᴏʀʀʏ {season.title()} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
            return
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    links = ""
    for file_num, file in enumerate(files, start=offset+1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if total >= MAX_BTN:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
        ])
        btn.append([
            InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if n_offset == '':
        btn.append([InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    elif n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"season_search#{season}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"season_search#{season}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"season_search#{season}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"season_search#{season}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^years#"))
async def years_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    btn = []
    for i in range(0, len(YEARS)-1, 3):
        btn.append([
            InlineKeyboardButton(text=YEARS[i].title(), callback_data=f"years_search#{YEARS[i].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=YEARS[i+1].title(), callback_data=f"years_search#{YEARS[i+1].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=YEARS[i+2].title(), callback_data=f"years_search#{YEARS[i+2].lower()}#{key}#0#{offset}#{req}"),
        ])
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ ʏᴇᴀʀ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^years_search#"))
async def year_search(client: Client, query: CallbackQuery):
    _, year, key, offset, orginal_offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    files, n_offset, total = await get_search_results(f"{search} {year}", max_results=int(MAX_BTN), offset=offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    files = [file for file in files if re.search(year, file.file_name, re.IGNORECASE)]
    if not files:
        await query.answer(f"sᴏʀʀʏ ʏᴇᴀʀ {year.title()} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
        return
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    links = ""
    for file_num, file in enumerate(files, start=offset+1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if total >= MAX_BTN:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
        ])
        btn.append([
            InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if n_offset == '':
        btn.append([InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    elif n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"years_search#{year}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"years_search#{year}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"years_search#{year}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"years_search#{year}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^qualities#"))
async def quality_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    btn = []
    for i in range(0, len(QUALITIES)-1, 3):
        btn.append([
            InlineKeyboardButton(text=QUALITIES[i].title(), callback_data=f"quality_search#{QUALITIES[i].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=QUALITIES[i+1].title(), callback_data=f"quality_search#{QUALITIES[i+1].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=QUALITIES[i+2].title(), callback_data=f"quality_search#{QUALITIES[i+2].lower()}#{key}#0#{offset}#{req}"),
        ])
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ ǫᴜᴀʟɪᴛʏ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^quality_search#"))
async def quality_search(client: Client, query: CallbackQuery):
    _, qul, key, offset, orginal_offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    files, n_offset, total = await get_search_results(f"{search} {qul}", max_results=int(MAX_BTN), offset=offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    files = [file for file in files if re.search(qul, file.file_name, re.IGNORECASE)]
    if not files:
        await query.answer(f"sᴏʀʀʏ ǫᴜᴀʟɪᴛʏ {qul.title()} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
        return
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    links = ""
    for file_num, file in enumerate(files, start=offset+1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if total >= MAX_BTN:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
        ])
        btn.append([
            InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if n_offset == '':
        btn.append([InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    elif n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"quality_search#{qul}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"quality_search#{qul}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"quality_search#{qul}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"quality_search#{qul}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    btn = []
    for i in range(0, len(LANGUAGES)-1, 2):
        btn.append([
            InlineKeyboardButton(text=LANGUAGES[i].title(), callback_data=f"lang_search#{LANGUAGES[i].lower()}#{key}#0#{offset}#{req}"),
            InlineKeyboardButton(text=LANGUAGES[i+1].title(), callback_data=f"lang_search#{LANGUAGES[i+1].lower()}#{key}#0#{offset}#{req}"),
        ])
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{offset}")])
    await query.message.edit_text("<b>ɪɴ ᴡʜɪᴄʜ ʟᴀɴɢᴜᴀɢᴇ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ғʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^lang_search#"))
async def lang_search(client: Client, query: CallbackQuery):
    _, lang, key, offset, orginal_offset, req = query.data.split("#")
    lang2 = lang[:3]
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    files, n_offset, total = await get_search_results(f"{search} {lang}", max_results=int(MAX_BTN), offset=offset)
    files2, n_offset2, total2 = await get_search_results(f"{search} {lang2}", max_results=int(MAX_BTN), offset=offset)
    total += total2
    try:
        n_offset = int(n_offset)
    except:
        try:
            n_offset = int(n_offset2)
        except:
            n_offset = 0
    files = [file for file in files if re.search(lang, file.file_name, re.IGNORECASE)]
    if not files:
        files = [file for file in files2 if re.search(lang2, file.file_name, re.IGNORECASE)]
        if not files:
            return await query.answer(f"sᴏʀʀʏ ʟᴀɴɢᴜᴀɢᴇ {lang.title()} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    links = ""
    for file_num, file in enumerate(files, start=offset+1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if total >= MAX_BTN:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
        ])
        btn.append([
            InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
            InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
        ])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if n_offset == '':
        btn.append([InlineKeyboardButton(text="🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    elif n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"lang_search#{lang}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"lang_search#{lang}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"lang_search#{lang}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"lang_search#{lang}#{key}#{n_offset}#{orginal_offset}#{req}")]
        )
    btn.append([InlineKeyboardButton(text="⌫ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ ⌦", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT, show_alert=True)
    movie = await get_poster(id, id=True)
    search = movie.get('title')
    await query.answer('bhai sahab hamare pass nahin Hai')
    files, offset, total_results = await get_search_results(search)
    if files:
        k = (search, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        k = await query.message.edit(script.NO_RESULT_TXT)
        await asyncio.sleep(60)
        await k.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

async def ai_spell_check(wrong_name):
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        movie_list = [movie['title'] for movie in search_results]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return
        movie = closest_match[0]
        files, offset, total_results = await get_search_results(movie)
        if files:
            return movie
        movie_list.remove(movie)
    return

async def auto_filter(client, msg, spoll=False, pm_mode=False):
    if not spoll:
        message = msg
        search = message.text
        chat_id = message.chat.id
        settings = await get_settings(chat_id, pm_mode=pm_mode)
        searching_msg = await msg.reply_text(f'**🔎 sᴇᴀʀᴄʜɪɴɢ {search}**')
        files, offset, total_results = await get_search_results(search)
        await searching_msg.delete()
        if not files:
            if settings["spell_check"]:
                ai_sts = await msg.reply_text(f'**ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...**')
                is_misspelled = await ai_spell_check(search)
                if is_misspelled:
                    await asyncio.sleep(2)
                    msg.text = is_misspelled
                    await ai_sts.delete()
                    return await auto_filter(client, msg)
                await ai_sts.delete()
                return await advantage_spell_chok(msg)
            return
    else:
        settings = await get_settings(msg.message.chat.id, pm_mode=pm_mode)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
    req = message.from_user.id if message.from_user else 0
    key = f"{message.chat.id}-{message.id}"
    batch_ids = files
    temp.FILES_ID[f"{message.chat.id}-{message.id}"] = batch_ids
    batch_link = f"batchfiles#{message.chat.id}#{message.id}#{message.from_user.id}"
    temp.CHAT[message.from_user.id] = message.chat.id
    settings = await get_settings(message.chat.id, pm_mode=pm_mode)
    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings["auto_delete"] else ''
    links = ""
    for file_num, file in enumerate(files, start=1):
        links += f"""<b>\n\n{file_num}. <a href=https://t.me/{temp.U_NAME}?start={"pm_mode_" if pm_mode else ''}file_{ADMINS[0] if pm_mode else message.chat.id}_{file.file_id}>[{get_size(file.file_size)}] {formate_file_name(file.file_name)}</a></b>"""
    btn = []
    if offset != "":
        if total_results >= MAX_BTN:
            btn.append([
                InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
                InlineKeyboardButton("🚩 ʏᴇᴀʀ ⌛", callback_data=f"years#{key}#{offset}#{req}")
            ])
            btn.append([
                InlineKeyboardButton("✨ ǫᴜᴀʟɪᴛʏ ", callback_data=f"qualities#{key}#{offset}#{req}"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
            ])
        else:
            btn.append([
                InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link),
                InlineKeyboardButton("✨ ʟᴀɴɢᴜᴀɢᴇ ✨", callback_data=f"languages#{key}#{offset}#{req}")
            ])
            btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    else:
        btn.append([InlineKeyboardButton("♻️ sᴇɴᴅ ᴀʟʟ ♻️", callback_data=batch_link)])
        btn.append([InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="pages")])
    if spoll:
        m = await msg.message.edit(f"<b><code>{search}</code> ɪs ꜰᴏᴜɴᴅ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ꜰɪʟᴇs 📫</b>")
        await asyncio.sleep(1.2)
        await m.delete()
    if offset != "":
        BUTTONS[key] = search
        btn.append(
            [InlineKeyboardButton(text=f"1/{math.ceil(int(total_results) / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton(text="𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{offset}")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b><blockquote>🗄️ ꜰɪʟᴇꜱ ꜰᴏʀ {search}</blockquote></b>"
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = f"<a href=https://t.me/{temp.U_NAME}?start=ads>{ads_name}</a>" if ads and ads_name else ""
    js_ads = f"\n\n<b><blockquote>⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️</blockquote>\n{ads_text}</b>" if ads_text else ""
    CAP[key] = cap
    if imdb and imdb.get('poster'):
        try:
            if settings['auto_delete']:
                k = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024] + links + del_msg, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
                await asyncio.sleep(DELETE_TIME)
                await k.delete()
                try:
                    await message.delete()
                except:
                    pass
            else:
                await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024] + links + js_ads, reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            poster = imdb.get('poster', 'https://example.com/default-poster.jpg')
            if settings["auto_delete"]:
                k = await message.reply_photo(photo=poster, caption=cap[:1024] + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
                await asyncio.sleep(DELETE_TIME)
                await k.delete()
                try:
                    await message.delete()
                except:
                    pass
            else:
                await message.reply_photo(photo=poster, caption=cap[:1024] + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            print(e)
            k = await message.reply_text(cap + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
            if settings["auto_delete"]:
                await asyncio.sleep(DELETE_TIME)
                await k.delete()
                try:
                    await message.delete()
                except:
                    pass
    else:
        k = await message.reply_text(text=cap + links + js_ads, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)
        if settings['auto_delete']:
            await asyncio.sleep(DELETE_TIME)
            await k.delete()
            try:
                await message.delete()
            except:
                pass
    return

async def advantage_spell_chok(message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(120)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[InlineKeyboardButton(text=movie.get('title'), callback_data=f"spol#{movie.movieID}#{user}")] for movie in movies]
    buttons.append([InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')])
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(120)
    await d.delete()
    try:
        await message.delete()
    except:
        pass
