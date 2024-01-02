import asyncio
import traceback
from sys import exc_info
from typing import Optional

from i18n import t

from lib.bots.models import Message, CachedContext
from lib.commands import BaseCommand
from lib.utils import get_or_default, locale


def help_commands_str(context, commands):
    return '\n'.join([f'/{k.command} - {k.description}' for k in commands])


class Help(BaseCommand):

    def __init__(self, commands):
        super().__init__(
            command='help',
            name="help",
            description="Shows this help message",
            examples=[
                "/help",
            ],
        )
        self.commands = commands

    async def run(self, parsed, message, context, messaging_service):
        return await messaging_service.send_message(
            reply_to_message_id=message.message_id,
            chat_id=message.chat_id,
            text=t('instructions.help',
                   locale=locale(context),
                   commands=help_commands_str(context, self.commands)),
            reply_buttons=[
                [
                    {
                        'text': t('buttons.read_docs', locale=locale(context)),
                        'url': f"https://github.com/herval/cliobot",
                        'inline_mode': False,
                    }
                ]
            ]
        )
# get a value from update metadata, reply to message metadata and context, in that order
def get_value(update, context, key, default=None):
    res = get_or_default(update.metadata, key, None)
    if res is not None:
        return res

    res = update.reply_to_message and update.reply_to_message.metadata.get(key) or None
    if res is not None:
        return res

    return context.get(key, default)


def app_name(bot_name):
    if bot_name == 'whatsapp_bot':
        return "WhatsApp"
    elif bot_name == 'telegram_bot':
        return "Telegram"
    return bot_name


class CommandHandler:
    """
    Simple handler that just executes commands using a slash command syntax
    """

    def __init__(self,
                 app_name,
                 bot_id,
                 messaging_service,
                 internal_queue,
                 db,
                 storage,
                 error_handler,
                 metrics,
                 commands,
                 translator):
        self.messaging_service = messaging_service
        self.translator = translator
        self.internal_queue = internal_queue
        self.db = db
        self.app_name = app_name
        self.bot_id = bot_id
        self.storage = storage
        self.running = True
        self.sender_loop = None
        self.metrics = metrics
        self.error_handler = error_handler
        self.commands = commands
        self.command_handlers = {c.command: c for c in commands}
        self.reply_handlers = [c.command for c in commands if c.reply_only]

    def infer_command(self, update, context) -> Optional[BaseCommand]:
        if 'command' in update.metadata:  # callback data takes precedence
            return self.command_handlers[update.metadata.get('command')]

        if update.text is None:
            return None

        text = update.text
        txt = text.split(" ")[0].lower()
        if txt.startswith('/'):
            txt = txt[1:]

        if txt in self.command_handlers:
            return self.command_handlers[txt]

        if update.reply_to_message_id and txt in self.reply_handlers:
            return self.command_handlers[txt]

        if context.get('command'):
            return self.command_handlers[context.get('command')]

        return None

    async def exec(self, command: BaseCommand, update: Message, context: CachedContext):
        self.error_handler.set_context({
            "id": context.user_id,
        })

        try:
            parsed = await command.parse(update, context, self.messaging_service)
            if parsed and await command.run(parsed, update, context, self.messaging_service):
                context.clear()
        except Exception as e:
            traceback.print_exc()
            self.metrics.capture_exception(exc_info(), self.app_name, context.user_id)
        finally:
            context.persist(self.db)

    async def message_handler(self, update: Message, context: CachedContext):
        print('on_message', update.__str__(), context.__str__())
        self.error_handler.set_context({
            "id": context.user_id,
        })

        try:
            self.db.save_message(
                chat_user_id=update.chat_user_id,
                chat_id=update.chat_id,
                text=update.text or '',
                app=self.app_name,
                external_id=update.message_id,
                image=update.image,
                video=update.video,
                audio=update.audio,
                voice=update.voice,
                is_forward=update.is_forward,
            )
        except Exception as e:
            self.metrics.capture_exception(e, self.app_name, context.user_id)

        if context.user_id is None:
            session = self.db.create_or_get_chat_session(update.chat_user_id, app=self.app_name)
            context.chat_id = update.chat_id
            context.user_id = session.get('user_id', None)

        if update.reply_to_message_id and not update.reply_to_message:
            print("Loading reply...")
            update.reply_to_message = await self.messaging_service.get_message(update.reply_to_message_id)

        update.translate(self.translator)

        inf = self.infer_command(update, context)
        if inf is not None:  # handle as a command input
            self.metrics.send_event(
                event="user_command",
                app_name=self.app_name,
                user_id=context.user_id,
                params={
                    'command': inf.command,
                    'chat_id': update.chat_id,
                }
            )
            await self.exec(inf, update, context)  # command handled, all good
        else:
            self.metrics.send_event(
                event="user_message",
                app_name=self.app_name,
                user_id=context.user_id,
                params={
                    'chat_id': update.chat_id,
                }
            )
            await self.exec(
                Help(
                    self.commands,
                ), update, context)  # TODO

    async def poll(self):
        while self.running:
            try:
                message = self.internal_queue.get()
                update, context = message
                await self.message_handler(update, context)
            except (KeyboardInterrupt, SystemExit):
                print("Shutting down...")
                self.running = False
                return
            except Exception:
                traceback.print_exc()
                self.metrics.capture_exception(exc_info(), self.app_name, 'anonymous')
            finally:
                self.internal_queue.task_done()

    def listen(self):
        self.sender_loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self.sender_loop)
        self.sender_loop.run_until_complete(self.poll())

    def stop(self):
        self.running = False
        self.sender_loop.stop()
