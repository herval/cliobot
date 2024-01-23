from lib.commands import ModelBackedCommand


class Ask(ModelBackedCommand):
    def __init__(self, models, default_model):
        super().__init__(
            command='ask',
            name="ask",
            description="Ask a question using a language model",
            examples=[
                "/ask what's the meaning of life?",
            ],
            models=models,
            default_model=default_model,
        )

    async def run_model(self, parsed, model, message, session, bot) -> bool:
        res = await model.generate(parsed)

        for r in res.texts:
            await bot.messaging_service.send_message(
                text=r,
                chat_id=message.chat_id,
                reply_to_message_id=message.message_id,
            )

        return True
