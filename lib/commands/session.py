from i18n import t

from lib.commands import BaseCommand
from lib.utils import locale


# context manipulation commands

class ListModels(BaseCommand):
    def __init__(self, txt2img, transcribe, describe, ask):
        super().__init__(
            command='models',
            name="list_models",
            description="Lists all available models",
            examples=[
                "/models",
            ],
            prompt_class=None,
        )
        self.models = {
            'Text to Image': txt2img,
            'Transcribe': transcribe,
            'Describe': describe,
            'Ask': ask,
        }

    async def run(self, parsed, message, session, bot):
        models = []

        for k, v in self.models.items():
            if len(v) > 0:
                models.append(k + ':')
                models.extend([f'- {k}' for k, v in v.items()])
                models.append('\n')

        return await bot.messaging_service.send_message(
            text='Available models:\n' + '\n'.join(models),
            chat_id=message.chat_id,
        )

class ClearContext(BaseCommand):
    def __init__(self):
        super().__init__(
            command='clear',
            name="clear_context",
            description="Clears the context of the current chat",
            examples=[
                "/clear",
            ],
            prompt_class=None,
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
            command='context',
            name="print_context",
            description="Prints the context of the current chat",
            examples=[
                "/print",
            ],
            prompt_class=None,
        )

    async def run(self, parsed, message, session, bot):
        ctx = '\n'.join([f'- {k}: {v}' for k, v in session.context.items() if v is not None])
        if len(ctx) == 0:
            msg = 'Nothing in context'
        else:
            msg = t('results.current_context', context=ctx, locale=locale(session))

        return await bot.messaging_service.send_message(
            text=msg,
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
        attr, val = parsed.prompt.split(' ', 1)

        session.set_preference(attr, val)

        return await bot.messaging_service.send_message(
            text=t('results.preference_set', attr=attr, value=val, locale=locale(session)),
            chat_id=message.chat_id,
        )


class ListPreferences(BaseCommand):
    def __init__(self):
        super().__init__(
            command='preferences',
            name="list_preferences",
            description="Lists all preferences for the current chat",
            examples=[
                "/list",
            ],
            prompt_class=None,
        )

    async def run(self, parsed, message, session, bot) -> bool:
        prefs = '\n'.join([f'- {k}: {v}' for k, v in session.preferences.items()])
        if len(prefs) == 0:
            msg = 'No preferences set'
        else:
            msg = t('results.current_preferences', preferences=prefs, locale=locale(session))

        return await bot.messaging_service.send_message(
            text=msg,
            chat_id=message.chat_id,
        )