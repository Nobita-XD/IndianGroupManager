import importlib
import time
import re
import random
from sys import argv
from typing import Optional

from telethon.sessions import string

from TeamIndia import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,   
    BOT_USERNAME, 
    BOT_NAME,    
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from TeamIndia.modules import ALL_MODULES
from TeamIndia.modules.helper_funcs.chat_status import is_user_admin
from TeamIndia.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

SETUP_VIDEO = ""

PM_START_TEXT = """
Hᴇʏ Tʜᴇʀᴇ[🤗](https://telegra.ph/file/26f94066bbbc590188cba.jpg), Iᴍ A Hɪɢʜʏ Aᴅᴠᴀɴᴄᴇᴅ Bᴏᴛ Wɪᴛʜ Lᴏᴛꜱ Oꜰ Aᴍᴀᴢɪɴɢ Tᴏᴏʟꜱ.
I'ᴍ Hᴇʀᴇ Tᴏ Hᴇʟᴘ Yᴏᴜ Mᴀɴᴀɢᴇ Yᴏᴜʀ Gʀᴏᴜᴘꜱ! Hɪᴛ /help Tᴏ Kɴᴏᴡ Aʙᴏᴜᴛ Mʏ Cᴏᴏʟ Fᴇᴀᴛᴜʀᴇꜱ😉
"""

buttons = [
    [
        InlineKeyboardButton(
            text="💞 Sᴜᴍᴍᴏɴ Mᴇ 💞", url="https://t.me/{BOT_USERNAME}?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="Sᴇᴛᴜᴘ", callback_data="india_"),
        InlineKeyboardButton(
            text="Sᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_CHAT}"
        ),
    ],
    [
        InlineKeyboardButton(text="❔ Hᴇʟᴘ & Cᴏᴍᴍᴀɴᴅꜱ ❔", callback_data="india_helpk"),
    ],
]


HELP_STRINGS = """
Hɪ.. I'ᴍ Bᴇsᴛ Gʀᴏᴜᴘ Manager [❤️](https://telegra.ph/file/26f94066bbbc590188cba.jpg) 
Cʟɪᴄᴋ Oɴ Tʜᴇ Bᴜᴛᴛᴏɴꜱ Bᴇʟᴏᴡ Tᴏ Gᴇᴛ Dᴏᴄᴜᴍᴇɴᴛᴀᴛɪᴏɴ Aʙᴏᴜᴛ Sᴘᴇᴄɪꜰɪᴄ Mᴏᴅᴜʟᴇꜱ."""


india_IMG = "https://telegra.ph/file/26f94066bbbc590188cba.jpg"

DONATE_STRING = """Heya, glad to hear you want to donate!
 You can support the project via [Paypal](#) or by contacting @piroXpower \
 Supporting isnt always financial! \
 Those who cannot provide monetary support are welcome to help us develop the bot at ."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}
MOD_BUTTON = {}
MOD_BUTTONS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("TeamIndia.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__button__"):
        MOD_BUTTON[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__buttons__"):
        MOD_BUTTONS[imported_module.__mod_name__.lower()] = imported_module



# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="⬅️ BACK", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_text(
            "I'm awake already!\n<b>Haven't slept since:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text( 
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [   MOD_BUTTON[module].__button__,
                        MOD_BUTTONS[module].__buttons__,
                        [InlineKeyboardButton(text="Back", callback_data="help_back")]
                        
                    ]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass



def india_about_callback(update, context):
    query = update.callback_query
    if query.data == "india_":
        query.message.edit_text(
            text=""" ℹ️ ɪ'ᴍ **ɪɴᴅɪᴀɴ**, ᴀ ᴘᴏᴡᴇʀꜰᴜʟ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ʙᴜɪʟᴛ ᴛᴏ ʜᴇʟᴘ ʏᴏᴜ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴇᴀꜱɪʟʏ.
                 \n❍ ɪ ᴄᴀɴ ʀᴇꜱᴛʀɪᴄᴛ ᴜꜱᴇʀꜱ.
                 \n❍ ɪ ᴄᴀɴ ɢʀᴇᴇᴛ ᴜꜱᴇʀꜱ ᴡɪᴛʜ ᴄᴜꜱᴛᴏᴍɪᴢᴀʙʟᴇ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ᴀɴᴅ ᴇᴠᴇɴ ꜱᴇᴛ ᴀ ɢʀᴏᴜᴘ'ꜱ ʀᴜʟᴇꜱ.
                 \n❍ ɪ ʜᴀᴠᴇ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɴᴛɪ-ꜰʟᴏᴏᴅ ꜱʏꜱᴛᴇᴍ.
                 \n❍ ɪ ᴄᴀɴ ᴡᴀʀɴ ᴜꜱᴇʀꜱ ᴜɴᴛɪʟ ᴛʜᴇʏ ʀᴇᴀᴄʜ ᴍᴀx ᴡᴀʀɴꜱ, ᴡɪᴛʜ ᴇᴀᴄʜ ᴘʀᴇᴅᴇꜰɪɴᴇᴅ ᴀᴄᴛɪᴏɴꜱ ꜱᴜᴄʜ ᴀꜱ ʙᴀɴ, ᴍᴜᴛᴇ, ᴋɪᴄᴋ, ᴇᴛᴄ.
                 \n❍ ɪ ʜᴀᴠᴇ ᴀ ɴᴏᴛᴇ ᴋᴇᴇᴘɪɴɢ ꜱʏꜱᴛᴇᴍ, ʙʟᴀᴄᴋʟɪꜱᴛꜱ, ᴀɴᴅ ᴇᴠᴇɴ ᴘʀᴇᴅᴇᴛᴇʀᴍɪɴᴇᴅ ʀᴇᴘʟɪᴇꜱ ᴏɴ ᴄᴇʀᴛᴀɪɴ ᴋᴇʏᴡᴏʀᴅꜱ.
                 \n❍ ɪ ᴄʜᴇᴄᴋ ꜰᴏʀ ᴀᴅᴍɪɴ'ꜱ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ʙᴇꜰᴏʀᴇ ᴇxᴇᴄᴜᴛɪɴɢ ᴀɴʏ ᴄᴏᴍᴍᴀɴᴅ ᴀɴᴅ ᴍᴏʀᴇ ꜱᴛᴜꜰꜰꜱ 
                 \n\n_ᴍᴇ'ꜱ ʟɪᴄᴇɴꜱᴇᴅ ᴜɴᴅᴇʀ ᴛʜᴇ ɢɴᴜ ɢᴇɴᴇʀᴀʟ ᴘᴜʙʟɪᴄ ʟɪᴄᴇɴꜱᴇ ᴠ3.0_
                 \nʜᴇʀᴇ ɪꜱ ᴛʜᴇ [💾ʀᴇᴘᴏꜱɪᴛᴏʀʏ](https://github.com/TG-TeamIndia/IndianSecurityBot).                  
                 \n\nɪꜰ ʏᴏᴜ ʜᴀᴠᴇ ᴀɴʏ Qᴜᴇꜱᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴀʟɪᴄɪᴀ, ʟᴇᴛ ᴜꜱ ᴋɴᴏᴡ ᴀᴛ @IndianSupportGroup""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Hᴇʟᴘ⚡", callback_data="india_tut"),
                    InlineKeyboardButton(text="sᴜᴘᴘᴏʀᴛ", callback_data="india_support")
                 ], 
                 [
                    InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="india_back")
                 ]
                ]
            ),
        )

    elif query.data == "india_tut":
        query.message.reply_video(
            PATRICIA_SETUP,
            parse_mode=ParseMode.MARKDOWN,                         
        )
        query.message.delete()

    elif query.data == "india_support":
        query.message.edit_text(
            text=f"**ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʜᴇʟᴘ sᴇᴄᴛɪᴏɴ ʀᴇɢᴀʀᴅs  sᴜᴘᴘᴏʀᴛ ᴀɴᴅ ᴍᴀɴᴀɢᴇᴍᴇɴᴛs**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [               
                [
                 InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url="https://t.me/{SUPPORT_CHAT}"),
                 InlineKeyboardButton(text="Dᴇᴠs", url="https://t.me/StarkBotInDustries")
                ], 
                [
                 InlineKeyboardButton(text="Lᴏɢs", url="https://t.me/{GBAN_USERNAME}"),
                 InlineKeyboardButton(text="Uᴘᴅᴀᴛᴇs", url="https://t.me/{UPDATE_CHANNEL}")
                ]
                [InlineKeyboardButton(text="Bᴀᴄᴋ", callback_data="india_back")],
              ]
            ),
        )
    elif query.data == "india_helpk":
        query.message.edit_text(
            text=f"""*Nᴇᴡ  Tᴏ  {BOT_NAME}!  Hᴇʀᴇ  Is  Tʜᴇ  Qᴜɪᴄᴋ  Sᴛᴀʀᴛ  Gᴜɪᴅᴇ  Wʜɪᴄʜ  Wɪʟʟ  Hᴇʟᴘ  Yᴏᴜ  Tᴏ  Uɴᴅᴇʀsᴛᴀɴᴅ  Wʜᴀᴛ  Is  {BOT_NAME}  Aɴᴅ  Hᴏᴡ  Tᴏ  Usᴇ  Iᴛ.
                       Cʟɪᴄᴋ  Bᴇʟᴏᴡ  Bᴜᴛᴛᴏɴ  Tᴏ  Aᴅᴅ  Bᴏᴛ  Iɴ  Yᴏᴜʀ  Gʀᴏᴜᴘ. Bᴀsɪᴄ  Tᴏᴜʀ  Sᴛᴀʀᴛᴇᴅ  Tᴏ  Kɴᴏᴡ  Aʙᴏᴜᴛ  Hᴏᴡ  Tᴏ  Usᴇ  Mᴇ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="Aʟʟ Cᴏᴍᴍᴀɴᴅs 📚", callback_data="help_back")],               
                [InlineKeyboardButton(text="Qᴜɪᴄᴋ Sᴇᴛᴜᴘ⚙", callback_data="india_help"),
                 InlineKeyboardButton(text="Donate ", callback_data="india_donate")],        
                [InlineKeyboardButton(text="🔙 Back", callback_data="india_back")], 
              ]
            ),
        )
    elif query.data == "india_help":
        query.message.edit_text(
            text=f"""*Nᴇᴡ  Tᴏ  {BOT_NAME}!  Hᴇʀᴇ  Is  Tʜᴇ  Qᴜɪᴄᴋ  Sᴛᴀʀᴛ  Gᴜɪᴅᴇ  Wʜɪᴄʜ  Wɪʟʟ  Hᴇʟᴘ  Yᴏᴜ  Tᴏ  Uɴᴅᴇʀsᴛᴀɴᴅ  Wʜᴀᴛ  Is  {BOT_NAME}  Aɴᴅ  Hᴏᴡ  Tᴏ  Usᴇ  Iᴛ.
                       Cʟɪᴄᴋ  Bᴇʟᴏᴡ  Bᴜᴛᴛᴏɴ  Tᴏ  Aᴅᴅ  Bᴏᴛ  Iɴ  Yᴏᴜʀ  Gʀᴏᴜᴘ. Bᴀsɪᴄ  Tᴏᴜʀ  Sᴛᴀʀᴛᴇᴅ  Tᴏ  Kɴᴏᴡ  Aʙᴏᴜᴛ  Hᴏᴡ  Tᴏ  Usᴇ  Mᴇ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="Sᴇᴛᴜᴘ Tᴜᴛᴏʀɪᴀʟ 🎥", callback_data="india_vida")],
               [InlineKeyboardButton(text="➕️  Iɴᴠɪᴛᴇ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ➕️", url="https://t.me/{BOT_USERNAME}?startgroup=true")],       
                [InlineKeyboardButton(text="🔙 Bᴀᴄᴋ", callback_data="india_"),
                 InlineKeyboardButton(text="➡️", callback_data="india_helpa")]
              ]
            ),
        )

    elif query.data == "india_helpa":
        query.message.edit_text(
            text=f"""<b>Hᴇʏ,  Wᴇʟᴄᴏᴍᴇ  Tᴏ  Cᴏɴғɪɢᴜʀᴀᴛɪᴏɴ  Tᴜᴛᴏʀɪᴀʟ
                       Bᴇғᴏʀᴇ  Wᴇ  Gᴏ,  I  Nᴇᴇᴅ  Aᴅᴍɪɴ  Pᴇʀᴍɪssɪᴏɴs  Iɴ  Tʜɪs  Cʜᴀᴛ  Tᴏ  Wᴏʀᴋ  Pʀᴏᴘᴇʀʟʏ.
                       1). Cʟɪᴄᴋ  Mᴀɴᴀɢᴇ  Gʀᴏᴜᴘ.
                       2). Gᴏ  Tᴏ  Aᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs  Aɴᴅ  Aᴅᴅ</b> @{BOT_USERNAME} <b>As  Aᴅᴍɪɴ.
                       3). Gɪᴠɪɴɢ  Fᴜʟʟ  Pᴇʀᴍɪssɪᴏɴs  Mᴀᴋᴇ    Fᴜʟʟʏ  Usᴇғᴜʟ</b>""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="⬅️", callback_data="india_help"),
                InlineKeyboardButton(text="➡️", callback_data="india_helpb")],               
              ]
            ),
        )
    elif query.data == "india_helpb":
        query.message.edit_text(
            text="""*Cᴏɴɢʀᴀɢᴜʟᴀᴛɪᴏɴs,  Tʜɪꜱ  Bᴏᴛ  Nᴏᴡ  Rᴇᴀᴅʏ  Tᴏ  Mᴀɴᴀɢᴇ  Yᴏᴜʀ  Gʀᴏᴜᴘ
                       Hᴇʀᴇ  Aʀᴇ  Sᴏᴍᴇ  Essᴇɴᴛɪᴀʟᴛ  Tᴏ  Tʀʏ  Oɴ Tʜɪs Bᴏᴛ .
                       ×  Aᴅᴍɪɴ  Tᴏᴏʟs
                       ʙᴀsɪᴄ  ᴀᴅᴍɪɴ  ᴛᴏᴏʟs  ʜᴇʟᴘ  ʏᴏᴜ  ᴛᴏ  ᴘʀᴏᴛᴇᴄᴛ  ᴀɴᴅ  ᴘᴏᴡᴇʀᴜᴘ  ʏᴏᴜʀ  ɢʀᴏᴜᴘ
                       ʏᴏᴜ  ᴄᴀɴ  ʙᴀɴ  ᴍᴇᴍʙᴇʀs,  ᴋɪᴄᴋ  ᴍᴇᴍʙᴇʀs,  ᴘʀᴏᴍᴏᴛᴇ  sᴏᴍᴇᴏɴᴇ  ᴀs  ᴀᴅᴍɪɴ  ᴛʜʀᴏᴜɢʜ  ᴄᴏᴍᴍᴀɴᴅs  ᴏғ  ʙᴏᴛ
                       ×  Wᴇʟᴄᴏᴍᴇs
                       ʟᴇᴛs  sᴇᴛ  ᴀ  ᴡᴇʟᴄᴏᴍᴇ  ᴍᴇssᴀɢᴇ  ᴛᴏ  ᴡᴇʟᴄᴏᴍᴇ  ɴᴇᴡ  ᴜsᴇʀs  ᴄᴏᴍɪɴɢ  ᴛᴏ  ʏᴏᴜʀ  ɢʀᴏᴜᴘ
                       sᴇɴᴅ  /setwelcome  [ᴍᴇssᴀɢᴇ]  ᴛᴏ  sᴇᴛ  ᴀ  ᴡᴇʟᴄᴏᴍᴇ  ᴍᴇssᴀɢᴇ
                       ᴀʟsᴏ  ʏᴏᴜ  ᴄᴀɴ  sᴛᴏᴘ  ᴇɴᴛᴇʀɪɴɢ  ʀᴏʙᴏᴛs  ᴏʀ  sᴘᴀᴍᴍᴇʀs  ᴛᴏ  ʏᴏᴜʀ  ᴄʜᴀᴛ  ʙʏ  sᴇᴛᴛɪɴɢ  ᴡᴇʟᴄᴏᴍᴇ  ᴄᴀᴘᴛᴄʜᴀ  
                       Rᴇғᴇʀ  Hᴇʟᴘ  Mᴇɴᴜ  Tᴏ  Sᴇᴇ  Eᴠᴇʀʏᴛʜɪɴɢ  Iɴ  Dᴇᴛᴀɪʟ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="india_helpa"),
                 InlineKeyboardButton(text="➡️", callback_data="india_helpc")]
                ]
            ),
        )
    elif query.data == "india_helpc":
        query.message.edit_text(
            text="""*× Fɪʟᴛᴇʀs
                       ғɪʟᴛᴇʀs  ᴄᴀɴ  ʙᴇ  ᴜsᴇᴅ  ᴀs  ᴀᴜᴛᴏᴍᴀᴛᴇᴅ  ʀᴇᴘʟɪᴇs/ʙᴀɴ/ᴅᴇʟᴇᴛᴇ  ᴡʜᴇɴ  sᴏᴍᴇᴏɴᴇ  ᴜsᴇ  ᴀ  ᴡᴏʀᴅ  ᴏʀ  sᴇɴᴛᴇɴᴄᴇ
                       ғᴏʀ  ᴇxᴀᴍᴘʟᴇ  ɪғ  ɪ  ғɪʟᴛᴇʀ  ᴡᴏʀᴅ  'ʜᴇʟʟᴏ'  ᴀɴᴅ  sᴇᴛ  ʀᴇᴘʟʏ  ᴀs  'ʜɪ'
                       ʙᴏᴛ  ᴡɪʟʟ  ʀᴇᴘʟʏ  ᴀs  'ʜɪ'  ᴡʜᴇɴ  sᴏᴍᴇᴏɴᴇ  sᴀʏ  'ʜᴇʟʟᴏ'
                       ʏᴏᴜ  ᴄᴀɴ  ᴀᴅᴅ  ғɪʟᴛᴇʀs  ʙʏ  sᴇɴᴅɪɴɢ  /filter  ғɪʟᴛᴇʀ  ɴᴀᴍᴇ
                       × Aɪ  CʜᴀᴛBᴏᴛ
                       ᴡᴀɴᴛ  sᴏᴍᴇᴏɴᴇ  ᴛᴏ  ᴄʜᴀᴛ  ɪɴ  ɢʀᴏᴜᴘ?
                       Bᴏᴛ  ʜᴀs  ᴀɴ  ɪɴᴛᴇʟʟɪɢᴇɴᴛ  ᴄʜᴀᴛʙᴏᴛ  ᴡɪᴛʜ  ᴍᴜʟᴛɪʟᴀɴɢ  sᴜᴘᴘᴏʀᴛ
                       ʟᴇᴛ's  ᴛʀʏ  ɪᴛ,
                       Sᴇɴᴅ  /chatbot  Oɴ  Aɴᴅ  Rᴇᴘʟʏ  Tᴏ  Aɴʏ  Oғ  Mʏ  Mᴇssᴀɢᴇs  Tᴏ  Sᴇᴇ  Tʜᴇ  Mᴀɢɪᴄ*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="india_helpb"),
                 InlineKeyboardButton(text="➡️", callback_data="india_helpd")]
                ]
            ),
        )
    elif query.data == "india_helpd":
        query.message.edit_text(
            text="""*× Sᴇᴛᴛɪɴɢ  Uᴘ  Nᴏᴛᴇs
                       ʏᴏᴜ  ᴄᴀɴ  sᴀᴠᴇ  ᴍᴇssᴀɢᴇ/ᴍᴇᴅɪᴀ/ᴀᴜᴅɪᴏ  ᴏʀ  ᴀɴʏᴛʜɪɴɢ  ᴀs  ɴᴏᴛᴇs ᴜsɪɴɢ /notes
                       ᴛᴏ  ɢᴇᴛ  ᴀ  ɴᴏᴛᴇ  sɪᴍᴘʟʏ  ᴜsᴇ  #  ᴀᴛ  ᴛʜᴇ  ʙᴇɢɪɴɴɪɴɢ  ᴏғ  ᴀ  ᴡᴏʀᴅ
                       sᴇᴇ  ᴛʜᴇ  ɪᴍᴀɢᴇ..
                       × Sᴇᴛᴛɪɴɢ  Uᴘ  Nɪɢʜᴛᴍᴏᴅᴇ
                       ʏᴏᴜ  ᴄᴀɴ  sᴇᴛ  ᴜᴘ  ɴɪɢʜᴛᴍᴏᴅᴇ  ᴜsɪɴɢ  /nightmode  ᴏɴ/ᴏғғ  ᴄᴏᴍᴍᴀɴᴅ.
                       Nᴏᴛᴇ-  ɴɪɢʜᴛ  ᴍᴏᴅᴇ  ᴄʜᴀᴛs  ɢᴇᴛ  ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ  ᴄʟᴏsᴇᴅ  ᴀᴛ  12ᴘᴍ(ɪsᴛ)
                       ᴀɴᴅ  ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ  ᴏᴘᴇɴɴᴇᴅ  ᴀᴛ  6ᴀᴍ(ɪsᴛ)  ᴛᴏ  ᴘʀᴇᴠᴇɴᴛ  ɴɪɢʜᴛ  sᴘᴀᴍs.*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="⬅️", callback_data="india_helpc"),
                 InlineKeyboardButton(text="➡️", callback_data="india_helpe")]
                ]
            ),
        )
    elif query.data == "india_term":
        query.message.edit_text(
            text=f"""✗ *Terms and Conditions:*
                       - Only your first name, last name (if any) and username (if any) is stored for a convenient communication!
                       - No group ID or it's messages are stored, we respect everyone's privacy.
                       - Messages between Bot and you is only infront of your eyes and there is no backuse of it.
                       - Watch your group, if someone is spamming your group, you can use the report feature of your Telegram Client.
                       - Do not spam commands, buttons, or anything in bot PM.
                       *NOTE:* Terms and Conditions might change anytime
                       *Updates Channel:* @{UPDATE_CHANNEL}
                       *Support Chat:* @{SUPPORT_GROUP}""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                InlineKeyboardButton(text="🔙 𝘽𝙖𝙘𝙠", callback_data="about_")]]
            ),
        )
    elif query.data == "india_helpe":
        query.message.edit_text(
            text="""*× Sᴏ  Nᴏᴡ  Yᴏᴜ  Aʀᴇ  Aᴛ  Tʜᴇ  Eɴᴅ  Oғ  Bᴀsɪᴄ  Tᴏᴜʀ.  Bᴜᴛ  Tʜɪs  Is  Nᴏᴛ  Aʟʟ  I  Cᴀɴ  Dᴏ.
                       Sᴇɴᴅ  /help  Iɴ  Bᴏᴛ  Pᴍ  Tᴏ  Aᴄᴄᴇss  Hᴇʟᴘ  Mᴇɴᴜ
                       Tʜᴇʀᴇ  Aʀᴇ  Mᴀɴʏ  Hᴀɴᴅʏ  Tᴏᴏʟs  Tᴏ  Tʀʏ  Oᴜᴛ.  
                       Aɴᴅ  Aʟsᴏ  Iғ  Yᴏᴜ  Hᴀᴠᴇ  Aɴʏ  Sᴜɢɢᴇssɪᴏɴs  Aʙᴏᴜᴛ  Mᴇ,  Dᴏɴ'ᴛ  Fᴏʀɢᴇᴛ  Tᴏ  tᴇʟʟ  Tʜᴇᴍ  Tᴏ  Dᴇᴠs
                       Aɢᴀɪɴ  Tʜᴀɴᴋs  Fᴏʀ  Usɪɴɢ  Mᴇ
                       × Bʏ  Usɪɴɢ  Tʜɪꜱ  Bᴏᴛ  Yᴏᴜ  Aʀᴇ  Aɢʀᴇᴇᴅ  Tᴏ  Oᴜʀ  Tᴇʀᴍs  &  Cᴏɴᴅɪᴛɪᴏɴs*""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="➕ Aʟʟ Cᴏᴍᴍᴀɴᴅs ➕", callback_data="help_back")],
                [InlineKeyboardButton(text="⬅️", callback_data="india_helpd"),
                InlineKeyboardButton(text="Mᴀɪɴ Mᴇɴᴜ ", callback_data="india_helpk")]]
            ),
        )
    elif query.data == "india_donate":
        query.message.edit_text(
            text=f"**Soon**",
            parse_mode=ParseMode.MARKDOWN,
            show_alert=True
        )
      
    


    elif query.data == "india_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

     

def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text=""" Hi..🤗 I'm *india*
                 \nHere is the [Source Code](https://github.com/TG-TeamIndia/IndianSecurityBot) .""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Go Back", callback_data="source_back")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )


def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )



def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))



def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)



def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 254318997 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            stringz = ["Yes I'm Alive😊", "india is in your service again🤗", "I'm Working Back🤓", "I'm Still Alive Dude 😉"]
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}", random.choice(stringz))
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, pass_args=True, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*", run_async=True)

    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_", run_async=True)

    about_callback_handler = CallbackQueryHandler(india_about_callback, pattern=r"india_", run_async=True)
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_", run_async=True)

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats, run_async=True)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=15, read_latency=4, drop_pending_updates=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
