import asyncio
import traceback
from sys import exc_info
from typing import Optional

from i18n import t

from lib.bots.models import Message, CachedContext
from lib.commands import BaseCommand
from lib.utils import get_or_default, locale


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
                 fallback_command,
                 commands,
                 ):
        self.fallback_command = fallback_command
        self.running = True
        self.sender_loop = None
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

    async def exec(self, command: BaseCommand, update: Message, context: CachedContext, bot):
        try:
            parsed = await command.parse(update, context, bot)
            if parsed and await command.run(parsed, update, context, bot):
                context.clear()
        except Exception as e:
            traceback.print_exc()
            bot.metrics.capture_exception(exc_info(), bot.app_name, context.user_id)
        finally:
            context.persist(bot.db)

    async def message_handler(self, message: Message, context: CachedContext, bot):
        print('on_message', message.__str__(), context.__str__())
        bot.metrics.error_handler.set_context({
            "id": context.user_id,
        })

        try:
            bot.db.save_message(
                user_id=message.user_id,
                chat_id=message.chat_id,
                text=message.text or '',
                app=bot.app_name,
                external_id=message.message_id,
                image=message.image,
                video=message.video,
                audio=message.audio,
                voice=message.voice,
                is_forward=message.is_forward,
            )
        except Exception as e:
            bot.metrics.capture_exception(e, bot.app_name, context.user_id)

        if context.user_id is None:
            session = bot.db.create_or_get_chat_session(message.user_id, app=bot.app_name)
            context.chat_id = message.chat_id
            context.user_id = session.get('external_user_id', None)

        if message.reply_to_message_id and not message.reply_to_message:
            print("Loading reply...")
            message.reply_to_message = await bot.messaging_service.get_message(message.reply_to_message_id)

        message.translate(bot.translator)

        inf = self.infer_command(message, context)
        if inf is not None:  # handle as a command input
            bot.metrics.send_event(
                event="user_command",
                app_name=bot.app_name,
                user_id=context.user_id,
                params={
                    'command': inf.command,
                    'chat_id': message.chat_id,
                }
            )
            await self.exec(inf, message, context, bot)  # command handled, all good
        else:
            bot.metrics.send_event(
                event="user_message",
                app_name=bot.app_name,
                user_id=context.user_id,
                params={
                    'chat_id': message.chat_id,
                }
            )
            await self.fallback_command.run(None, message, context, bot)

    async def poll(self, bot):
        while self.running:
            try:
                message = bot.internal_queue.get()
                update, context = message
                await self.message_handler(update, context, bot)
            except (KeyboardInterrupt, SystemExit):
                print("Shutting down...")
                self.running = False
                return
            except Exception:
                traceback.print_exc()
                bot.metrics.capture_exception(exc_info(), bot.app_name, 'anonymous')
            finally:
                bot.internal_queue.task_done()

    def listen(self, bot):
        self.sender_loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self.sender_loop)
        self.sender_loop.run_until_complete(self.poll(bot))

    def stop(self):
        self.running = False
        self.sender_loop.stop()
