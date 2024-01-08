from i18n import t

from lib.commands import BaseCommand
from lib.utils import locale


# context manipulation commands

class ClearContext(BaseCommand):
    def __init__(self):
        super().__init__(
            command='clear',
            name="clear_context",
            description="Clears the context of the current chat",
            examples=[
                "/clear",
            ],
        )

    async def process(self, message, context, bot):
        context.clear()
        return await bot.messaging_service.send_message(
            text=t('result.clear_context', locale=locale(context)),
            chat_id=message.chat_id,
        )


class PrintContext(BaseCommand):
    def __init__(self):
        super().__init__(
            command='print',
            name="print_context",
            description="Prints the context of the current chat",
            examples=[
                "/print",
            ],
        )

    async def process(self, message, context, bot):
        ctx = '\n'.join([f'{k}: {v}' for k, v in context.context.items() if v is not None])

        return await bot.messaging_service.send_message(
            text=t('result.current_context', context=ctx, locale=locale(context)),
            chat_id=message.chat_id,
        )
