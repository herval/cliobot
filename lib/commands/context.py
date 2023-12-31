from lib.bots.models import Message, Context
from lib.commands import BaseCommand

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

    async def run(self, message: Message, context: Context):
        context.clear()
