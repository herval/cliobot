from lib.commands import ModelBackedCommand


class Ask(ModelBackedCommand):
    def __init__(self, models):
        super().__init__(
            command='ask',
            name="ask",
            description="Ask a question using a language model",
            examples=[
                "/ask what's the meaning of life?",
            ],
            models=models,
        )

    async def run(self, parsed, model, message, context, bot) -> bool:
        res = await model.generate(parsed)

        for r in res.texts:
            await bot.messaging_service.send_message(
                text=r,
                chat_id=message.chat_id,
                reply_to_message_id=message.message_id,
            )

        return True
