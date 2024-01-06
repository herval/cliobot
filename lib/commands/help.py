from lib.commands import BaseCommand
from lib.utils import get_or_default, locale
from i18n import t

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

    async def run(self, parsed, message, context, bot):
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
# get a value from update metadata, reply to message metadata and context, in that order
def get_value(update, context, key, default=None):
    res = get_or_default(update.metadata, key, None)
    if res is not None:
        return res

    res = update.reply_to_message and update.reply_to_message.metadata.get(key) or None
    if res is not None:
        return res

    return context.get(key, default)
