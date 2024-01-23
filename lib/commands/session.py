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

    async def run(self, parsed, message, session, bot):
        session.clear()
        return await bot.messaging_service.send_message(
            text=t('result.clear_context', locale=locale(session)),
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

    async def run(self, parsed, message, session, bot):
        ctx = '\n'.join([f'{k}: {v}' for k, v in session.context.items() if v is not None])

        return await bot.messaging_service.send_message(
            text=t('result.current_context', context=ctx, locale=locale(session)),
            chat_id=message.chat_id,
        )


class SetPreference(BaseCommand):
    def __init__(self):
        super().__init__(
            command='set',
            name="set_preference",
            description="Sets a preference for the current chat. Preferences have the same name as the parameters you want to hardcode (eg /set model dalle3 will always pick the dalle3 model by default, unless you override it on your prompt).",
            examples=[
                "/set preference_name preference_value",
            ],
        )

    async def run(self, parsed, message, session, bot) -> bool:
        key, val = parsed.prompt.split(' ', 1)

        session.set_preference(key, val)

        return await bot.messaging_service.send_message(
            text=t('results.preference_set', key=key, value=val, locale=locale(session)),
            chat_id=message.chat_id,
        )


class ListPreferences(BaseCommand):
    def __init__(self):
        super().__init__(
            command='list',
            name="list_preferences",
            description="Lists all preferences for the current chat",
            examples=[
                "/list",
            ],
        )

    async def run(self, parsed, message, session, bot) -> bool:
        prefs = '\n'.join([f'{k}: {v}' for k, v in session.preferences.items()])

        return await bot.messaging_service.send_message(
            text=t('results.current_preferences', preferences=prefs, locale=locale(session)),
            chat_id=message.chat_id,
        )