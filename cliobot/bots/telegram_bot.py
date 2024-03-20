import contextvars
from pathlib import Path

import httpcore
from retry import retry
from telegram import BotCommand, InputMediaPhoto, InputMediaDocument, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, KeyboardButton
from telegram._bot import Bot
from telegram.error import BadRequest, TimedOut, Forbidden
from telegram.ext import ApplicationBuilder, ConversationHandler, MessageHandler, CallbackQueryHandler, \
    filters

from cliobot.bots import Message, User, MessagingService, BaseBot
from cliobot.errors import TransientFailure, UserBlocked, UnknownError, MessageNoLongerExists, MessageNotModifiable
from cliobot.utils import flatten


def telegram_bot_id(apikey):
    return apikey.split(':')[0]


def convert_exceptions(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpcore.ConnectTimeout as to:
            # capture_exception(to)
            raise TransientFailure(to)
        except TimedOut as to:
            raise TransientFailure(to)
        except Forbidden as f:
            if 'bot was blocked by the user' in f.message:
                raise UserBlocked(f)
            else:
                raise UnknownError(f)
        except BadRequest as _e:
            if _e.message == 'Chat not found':
                print("Chat not found, ignoring (could be using a different bot instance?)")
            elif _e.message in [
                'Message to delete not found',
                'Message to edit not found']:
                raise MessageNoLongerExists(_e)
            elif _e.message in [
                'There is no media in the message to edit',
                'Replied message not found',
                'Message can\'t be edited']:
                raise MessageNotModifiable(_e)
            elif (_e.__str__() in
                  [
                      'Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message',
                      'Canceled by new editmessagemedia request',
                  ]):
                print(_e.__str__())  # happens, just ignore it
                raise TransientFailure(_e)
            else:
                raise _e

    return wrapper


def convert_media(media):
    if 'image' in media:
        path = media['image']
        if path.startswith('/'):
            path = Path(path)

        return InputMediaPhoto(
            media=media['image'],
            filename=media.get('filename', None),
            caption=media.get('text', None))
    elif 'attachment' in media:
        return InputMediaDocument(
            media=media['attachment'],
            filename=media.get('filename', None),
            caption=media.get('text', None),
            thumbnail=media.get('thumbnail', media['attachment']),
        )
    else:
        return None


def parse_callback_string(callback_data):
    op, *rest = callback_data.split(':')
    if op in ['upvote', 'downvote']:
        return {
            'command': op,
            'job_id': rest[0],
        }

    if op == 'select':
        return {
            'command': op,
            'job_id': rest[0],
            'index': rest[1],
        }

    if op == 'shuffle':
        return {
            'command': op,
            'job_id': rest[0],
            'index': rest[1],
        }

    if op == 'reroll_job':
        return {
            'command': op,
            'job_id': rest[0],
        }

    if op == 'retry':
        return {
            'command': op,
            'job_id': rest[0],
        }

    return {}


threadlocal_bot = contextvars.ContextVar("bot_instance", default=None)


class TelegramMessagingService(MessagingService):
    def __init__(self, apikey, commands, db):
        self.apikey = apikey
        self.bot_id = telegram_bot_id(apikey)
        self.db = db
        self.commands = commands

    async def initialize(self) -> Bot:
        if not threadlocal_bot.get():
            threadlocal_bot.set(Bot(self.apikey))

        if not threadlocal_bot.get()._initialized:
            await threadlocal_bot.get().initialize()

        return threadlocal_bot.get()

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def get_file(self, file_id):
        bot = await self.initialize()
        file = await bot.get_file(file_id)
        bytesdata = await file.download_as_bytearray()

        return file.file_path, bytesdata

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def get_file_info(self, file_id):
        bot = await self.initialize()
        info = await bot.get_file(file_id)
        return {
            'file_path': info.file_path,
        }

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def edit_message_media(self, message_id, chat_id, media, text=None, reply_buttons=None):
        bot = await self.initialize()
        await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=convert_media(media),
            reply_markup=reply_markup(reply_buttons)
        )

        if text:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=text,
            )

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def edit_message(self, message_id, chat_id, text, session=None, reply_buttons=None):
        bot = await self.initialize()
        return await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text or '',
        )

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def send_media(self, chat_id, media, reply_to_message_id=None, session=None, text=None, reply_buttons=None,
                         buttons=None):
        bot = await self.initialize()

        if buttons:
            for b in buttons:
                if b['kind'] == 'url':
                    text += f"\n\n{b['text']}: {b['url']}"

        res = await bot.send_photo(
            chat_id=chat_id,
            photo=media['image'],
            caption=text,
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup(reply_buttons) or buttons_markup(buttons),
        )

        self.db.save_message(
            user_id=self.bot_id,
            chat_id=chat_id,
            text=text or '',
            external_id=res.id,
            image=res.photo[-1].file_id,
            is_forward=False,
        )

        return res

    @convert_exceptions
    @retry(TimedOut, tries=2, delay=0.5)
    async def delete_message(self, message_id, chat_id):
        bot = await self.initialize()
        return await bot.delete_message(
            chat_id=int(chat_id),
            message_id=int(message_id),
        )

    @convert_exceptions
    @retry((TimedOut, TransientFailure), tries=2, delay=0.5)
    async def send_message(self, text, chat_id, session=None, reply_to_message_id=None, reply_buttons=None,
                           buttons=None):
        bot = await self.initialize()

        if buttons:
            for b in flatten(buttons):
                if b['kind'] == 'url':
                    text += f"\n\n{b['text']}: {b['url']}"

        res = await bot.send_message(
            chat_id=chat_id,
            text=text or '',
            reply_to_message_id=reply_to_message_id,
            reply_markup=reply_markup(reply_buttons) or buttons_markup(buttons),
        )

        self.db.save_message(
            user_id=self.bot_id,
            chat_id=chat_id,
            text=text or '',
            external_id=res.id,
            is_forward=False,
        )

        return res


def buttons_markup(buttons):
    if buttons is not None:
        rows = []
        for line in buttons:
            items = []
            for e in line:
                if e.get('kind', None) == 'login':
                    items.append(KeyboardButton(
                        text=e['text'],
                        request_contact=True,
                    ))
                elif e.get('kind', None) == 'url':
                    pass
                    # skip
                    # items.append(KeyboardButton(
                    #     text=e['text'],
                    #     web_app=WebAppInfo(
                    #         url=e['url'],
                    #     )
                    # ))

            rows.append(items)

        return ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            keyboard=rows
        )
    else:
        return None


def reply_markup(reply_buttons):
    if reply_buttons is not None:
        rows = []
        for line in reply_buttons:
            items = []
            for e in line:
                if 'url' in e:
                    items.append(InlineKeyboardButton(
                        text=e['text'],
                        url=e['url'],
                    ))
                if 'callback' in e:
                    items.append(InlineKeyboardButton(
                        text=e['text'],
                        callback_data=e['callback'],
                    ))
            rows.append(items)

        return InlineKeyboardMarkup(
            inline_keyboard=rows
        )
    else:
        return None


class TelegramBot(BaseBot):
    def __init__(self,
                 apikey,
                 commands,
                 db,
                 **kwargs
                 ):
        self.messaging_service = TelegramMessagingService(
            apikey=apikey,
            db=db,
            commands=commands,
        )
        self.app = ApplicationBuilder().token(apikey).build()

        super().__init__(
            commands=commands,
            db=db,
            bot_id=telegram_bot_id(apikey),
            **kwargs,
        )

    def handler_adapter(self, command):
        async def wrapper(message, context):
            print(message, context)
            msg = await self._parse_message(
                message=message.effective_message,
                user=message.effective_user,
                chat=message.effective_chat,
                context=context,
                callback_query=message.callback_query)

            await self.enqueue(msg)

        return wrapper

    async def initialize(self):
        self.app.add_handler(
            ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(self.handler_adapter('message_handler')),
                    MessageHandler(filters.ALL,
                                   self.handler_adapter('message_handler')),
                ],
                states={},
                fallbacks=[],
            ))

        bot = Bot(self.apikey)
        # sharing a bot between threads blows things up
        await bot.initialize()
        await bot.set_my_commands(
            commands=[
                BotCommand(
                    c.command,
                    c.description,
                ) for c in self.commands
            ])

    def start(self):
        self.app.run_polling()

    async def _parse_message(self, message, user, chat, context, callback_query) -> Message:
        meta = {}

        # text
        if message is not None:
            txt = message.text or message.caption
        else:
            txt = None
        if callback_query is not None:
            txt = callback_query.data
            meta = parse_callback_string(txt)
        if context.args is not None and len(context.args) > 0:
            txt = ' '.join(context.args)

        audio = None
        image = None
        reply = None
        voice = None
        video = None
        if message.reply_to_message is not None:
            m = message.reply_to_message
            reply = await self._parse_message(
                message=m,
                user=m.from_user,
                chat=m.chat,
                context=context,
                callback_query=None)

            # if command is in reply to a photo, use that photo
            if message.reply_to_message.photo is not None and len(
                    message.reply_to_message.photo) > 0:  # a photo
                image = message.reply_to_message.photo[-1].file_id
            elif message.reply_to_message.document is not None and message.reply_to_message.document.mime_type.startswith(
                    'image'):
                image = message.reply_to_message.document.file_id  # a document

            if message.reply_to_message.audio is not None:
                audio = message.reply_to_message.audio.file_id

            if message.reply_to_message.video is not None:
                video = message.reply_to_message.video.file_id
        elif message.photo is not None and len(
                message.photo) > 0:  # uploaded a new image
            image = message.photo[-1].file_id
        elif message.document is not None and message.document.mime_type.startswith(
                'image'):
            image = message.document.file_id

        if message.audio is not None:
            audio = message.audio.file_id

        if message.video is not None:
            video = message.video.file_id

        if message.voice is not None:
            voice = message.voice.file_id

        phone = message.contact.phone_number if message.contact and message.contact.user_id == user.id else None
        return Message(
            user=User(
                username=user.username,
                phone=phone,
                full_name=f'{user.first_name} {user.last_name}' if user.first_name and user.last_name else None,
                language=user.language_code,
            ),
            message_id=message.id,
            user_id=user.id,
            chat_id=chat.id,
            reply_to_message_id=message.reply_to_message.id if message.reply_to_message is not None else None,
            reply_to_message=reply,
            text=txt or '',
            image=image,
            audio=audio,
            voice=voice,
            video=video,
            metadata=meta,
            is_forward=message.forward_from is not None,
        )
