from lib.commands import ModelBackedCommand
from lib.db.utils import cached_get_file


class Transcribe(ModelBackedCommand):
    def __init__(self, models):
        super().__init__(
            command='transcribe',
            name="transcribe",
            description="Transcribes an audio file",
            examples=[
                "/transcribe --audio <file url>",
                "upload or forward an audio file with /transcribe"
            ],
            models=models,
        )

    async def run(self, parsed, model, message, context, bot):
        msg = await bot.messaging_service.send_message(
            text='Transcribing...',
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )

        parsed.audio = await cached_get_file(
            context=context,
            file_id=parsed.audio,
            bot=bot,
        )

        res = await model.generate(parsed)
        for r in res.texts:
            await bot.messaging_service.send_message(
                text=r.text,
                chat_id=message.chat_id,
                reply_to_message_id=message.message_id,
            )
