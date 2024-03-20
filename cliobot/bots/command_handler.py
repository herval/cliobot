import asyncio
import traceback
from sys import exc_info
from typing import Optional

from cliobot.bots import Message, CachedSession, MessageHandler
from cliobot.commands import BaseCommand

class CommandHandler(MessageHandler):
    """
    Simple handler that just executes commands using a slash command syntax
    """

    def __init__(self, fallback_commands: dict, commands):
        super().__init__()
        self.fallback_commands = fallback_commands
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
            bot.metrics.capture_exception(exc_info(), session.user_id)
        finally:
            session.persist(bot.db)

    async def process(self, message: Message, session: CachedSession, bot):
        inf = self.infer_command(message, session)
        if inf is not None:  # handle as a command input
            bot.metrics.send_event(
                event="user_command",
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
