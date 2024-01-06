import asyncio
import os
import queue
import threading


class Message:
    def __init__(self,
                 message_id,
                 chat_user_id,
                 chat_id,
                 user,
                 reply_to_message=None,
                 reply_to_message_id=None,
                 text=None,
                 image=None,
                 audio=None,
                 voice=None,
                 video=None,
                 bot_id=None,
                 metadata=None,  # metadata is transient and survives the current request only
                 is_forward=False,
                 ):
        if metadata is None:
            metadata = {}

        self.user = user
        self.bot_id = bot_id
        self.message_id = message_id
        self.chat_user_id = chat_user_id
        self.chat_id = chat_id
        self.reply_to_message_id = reply_to_message_id
        self.text = text
        self.reply_to_message = reply_to_message
        self.image = image
        self.video = video
        self.audio = audio
        self.metadata = metadata
        self.is_forward = is_forward
        self.voice = voice

        if self.reply_to_message and not self.reply_to_message_id:
            self.reply_to_message_id = self.reply_to_message.message_id

    def translate(self, translator):
        if self.text is not None and translator:
            self.text = translator.translate(self.text) or self.text

    def full_text(self):
        return self.text

    def __str__(self):
        return f"Message({self.message_id}, {self.chat_id}, {self.chat_user_id}, {self.text})"

    def __repr__(self):
        return self.__str__()


class User:
    def __init__(self, username, phone, full_name, language):
        self.username = username
        self.phone = phone
        self.full_name = full_name
        self.language = language


# context = the "short term memory" of the bot. It survives across requests until cleared
# preferences = the "long term memory" of the bot. It survives until a user logs off
class Context:
    def __init__(self, user_id, chat_id, app_name, context=None, preferences=None):
        self.context = {}
        self.user_id = user_id
        self.chat_id = chat_id
        self.app_name = app_name
        self.preferences = {}
        if context:
            self.context = context
            if 'preferences' in context:
                self.preferences = context['preferences']
                del self.context['preferences']

        if preferences:
            self.preferences = preferences

        if self.preferences is None:
            self.preferences = {}

    def pop(self, key):
        if key in self.context:
            return self.context.pop(key)
        return None

    def __str__(self):
        return f"Context({self.context})"

    def __repr__(self):
        return self.__str__()

    def set(self, key, value):
        print('setting', key, value)
        self.context[key] = value

    def get(self, key, default=None, include_preferences=True):
        res = self.context.get(key, None)

        if not res and include_preferences:
            res = self.preferences.get(key, default)

        return res or default

    def clear(self, clear_user=False):
        newc = {}
        # for x in self.context.keys():
        #     if x in ['temp_image', 'temp_audio',
        #              'temp_video'] and not clear_user:  # keep unless we're clearing the user
        #         newc[x] = self.context[x]
        self.context = newc

    def to_dict(self, include_preferences=True):
        res = {}

        if include_preferences:
            for k, v in self.preferences.items():
                res[k] = v

        for k, v in self.context.items():
            if k != 'buffer':
                res[k] = v

        return res

    def images(self) -> dict[str, str]:
        return {
            k: v for k, v in self.context.items()
            if k.endswith('_image') and v is not None
        }

    def audios(self) -> dict[str, str]:
        return {
            k: v for k, v in self.context.items()
            if k.endswith('_audio') and v is not None
        }


class CachedContext(Context):
    def __init__(self, cached_context, app_name, chat_id):
        super().__init__(user_id=cached_context.get('user_id', None),
                         chat_id=chat_id,
                         app_name=app_name,
                         context=cached_context.get('context', {}),
                         preferences=cached_context.get('preferences', {}))
        self.dirty = False

    def pop(self, key):
        if key in self.context:
            self.dirty = True
        return super().pop(key)

    def persist(self, db):
        if self.dirty:  # commit changes
            db.set_chat_context(self.app_name, self.chat_id, self.to_dict())
            self.dirty = False

    def set(self, key, value):
        if self.context.get(key) != value:
            self.dirty = True
        super().set(key, value)

    def clear(self, clear_user=False):
        self.dirty = True
        super().clear(clear_user)

    @classmethod
    def from_cache(cls, cache, app_name, chat_id):
        data = cache.get_chat_context(app_name, chat_id)
        return cls(
            cached_context=data,
            app_name=app_name,
            chat_id=chat_id,
        )


class MessagingService:

    async def initialize(self):
        raise NotImplementedError()

    async def get_file(self, file_id) -> (str, bytes):
        raise NotImplementedError()

    async def get_message(self, message_id):
        raise NotImplementedError()

    def supports_editing_media(self):
        return True  # true by default

    async def edit_message_media(self, message_id, chat_id, media, reply_buttons=None):
        raise NotImplementedError()

    async def edit_message(self, message_id, chat_id, text, context=None, reply_buttons=None):
        raise NotImplementedError()

    async def send_message(self, text, chat_id, context=None, reply_to_message_id=None, reply_buttons=None,
                           buttons=None):
        raise NotImplementedError()

    async def delete_message(self, message_id, chat_id):
        raise NotImplementedError()

    async def send_media(self, chat_id, media, text, reply_to_message_id=None, context=None, reply_buttons=None,
                         buttons=None):
        raise NotImplementedError()


class BaseBot:
    def __init__(self,
                 db,
                 storage,
                 internal_queue,
                 bot_id,
                 handler_fn,
                 apikey,
                 app_name,
                 bot_language,
                 cache,
                 commands,
                 translator,
                 metrics,
                 ):
        self.internal_queue = internal_queue
        self.translator = translator
        self.db = db
        self.storage = storage
        self.bot_id = bot_id
        self.apikey = apikey
        self.commands = commands
        self.bot = None
        self.app_name = app_name
        self.bot_language = bot_language
        self.cache = cache
        self.metrics = metrics

        self.senders = [handler_fn() for _ in range(int(os.cpu_count()))]

        self.threads = [
            threading.Thread(target=handler.listen, args=(self,), daemon=True) for handler in self.senders
        ]

    async def initialize(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def listen(self):
        # initialize the bot commands list and stuff
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.initialize())
        loop.stop()

        # start everything
        [t.start() for t in self.threads]
        print("Bot ready")
        self.start()
        print("blowing things up, stay calm...")
        [s.stop() for s in self.senders]

    async def enqueue(self, update, context):
        self.internal_queue.put((update, context))
