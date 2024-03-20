from cliobot.commands import ModelBackedCommand
from cliobot.db.utils import cached_get_file


class Transcribe(ModelBackedCommand):
    def __init__(self, models, default_model):
        super().__init__(
            command='transcribe',
            name="transcribe",
            description="Transcribes an audio file",
            examples=[
                "/transcribe --audio <file url>",
                "upload or forward an audio file with /transcribe"
            ],
            models=models,
            default_model=default_model,
        )

    async def run_model(self, parsed, model, message, session, bot):
        msg = await bot.messaging_service.send_message(
            text='Transcribing...',
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )

        parsed.audio = await cached_get_file(
            session=session,
            file_id=parsed.audio,
            bot=bot,
        )

        res = await model.generate(parsed)
        await bot.messaging_service.delete_message(
            message_id=msg.message_id,
            chat_id=message.chat_id,
        )
        for r in res.texts:
            await bot.messaging_service.send_message(
                text=r,
                chat_id=message.chat_id,
                reply_to_message_id=message.message_id,
            )
