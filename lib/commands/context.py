from i18n import t

from lib.bots.models import Message, Context
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

    async def run(self, parsed, message: Message, context: Context, messaging_service):
        context.clear()
        return await messaging_service.send_message(
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

    async def run(self, parsed, message: Message, context: Context, messaging_service):
        ctx = '\n'.join([f'{k}: {v}' for k, v in context.context.items() if v is not None])

        return await messaging_service.send_message(
            text=t('result.current_context', context=ctx, locale=locale(context)),
            chat_id=message.chat_id,
        )
