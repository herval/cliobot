from i18n import t

from cliobot.commands import BaseCommand
from cliobot.utils import locale


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

    async def process(self, message, context, bot):
        return await bot.messaging_service.send_message(
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
