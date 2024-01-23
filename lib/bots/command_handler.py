import asyncio
import traceback
from sys import exc_info
from typing import Optional

from lib.bots import Message, CachedSession
from lib.commands import BaseCommand
from lib.utils import is_empty


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
                 fallback_commands: dict,
                 commands,
                 ):
        self.fallback_commands = fallback_commands
        self.running = True
        self.sender_loop = None
        self.commands = commands
        self.command_handlers = {c.command: c for c in commands}
        self.reply_handlers = [c.command for c in commands if c.reply_only]

    def infer_command(self, update, session) -> Optional[BaseCommand]:
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

        if session.get('command'):
            return self.command_handlers[session.get('command')]

        return None

    async def exec(self, command: BaseCommand, update: Message, session: CachedSession, bot):
        try:
            if await command.process(update, session, bot):
                session.clear()
        except Exception as e:
            traceback.print_exc()
            bot.metrics.capture_exception(exc_info(), bot.app_name, session.user_id)
        finally:
            session.persist(bot.db)

    async def message_handler(self, message: Message, bot):
        print('on_message', message.__str__())
        session = CachedSession.from_cache(
            db=bot.db,
            user_id=message.user_id,
            chat_id=message.chat_id,
            app_name=bot.app_name)

        bot.metrics.error_handler.set_context({
            "id": session.user_id,
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
            bot.metrics.capture_exception(e, bot.app_name, session.user_id)

        if session.user_id is None:
            session = bot.db.create_or_get_chat_session(message.user_id, app=bot.app_name)
            session.chat_id = message.chat_id
            session.user_id = session.get('external_user_id', None)

        if message.reply_to_message_id and not message.reply_to_message:
            print("Loading reply...")
            message.reply_to_message = await bot.messaging_service.get_message(message.reply_to_message_id)

        message.translate(bot.translator)

        inf = self.infer_command(message, session)
        if inf is not None:  # handle as a command input
            bot.metrics.send_event(
                event="user_command",
                app_name=bot.app_name,
                user_id=session.user_id,
                params={
                    'command': inf.command,
                    'chat_id': message.chat_id,
                }
            )
            await self.exec(inf, message, session, bot)  # command handled, all good
        else:
            bot.metrics.send_event(
                event="user_message",
                app_name=bot.app_name,
                user_id=session.user_id,
                params={
                    'chat_id': message.chat_id,
                }
            )

            if message.audio and 'audio' in self.fallback_commands:
                fallback = self.fallback_commands['audio']
            elif message.video and 'video' in self.fallback_commands:
                fallback = self.fallback_commands['video']
            elif message.voice and 'voice' in self.fallback_commands:
                fallback = self.fallback_commands['voice']
            elif message.image and 'image' in self.fallback_commands:
                fallback = self.fallback_commands['image']
            elif message.text and 'text' in self.fallback_commands:
                fallback = self.fallback_commands['text']
            else:
                fallback = None


            if fallback in self.command_handlers:
                message.text = f'/{fallback} {message.text}'.strip()
                await self.exec(self.command_handlers[fallback], message, session, bot)

    async def poll(self, bot):
        while self.running:
            try:
                message = bot.internal_queue.get()
                await self.message_handler(message, bot)
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
