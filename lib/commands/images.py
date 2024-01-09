from lib.commands import send_error_message_image, ModelBackedCommand
from lib.db.utils import upload_asset
from lib.utils import abs_path


class TextToImage(ModelBackedCommand):
    def __init__(self, models):
        super().__init__(
            command='image',
            name="image",
            description="Create an image from a text prompt",
            examples=[
                "/image a hamster astronaut floating in space",
            ],
            models=models,
        )

    async def run(self, parsed, model, message, context, bot):
        msg = await bot.messaging_service.send_media(
            text="Generating image, please wait...",
            chat_id=message.chat_id,
            media={
                'image': abs_path('working.jpg'),
            },
            reply_to_message_id=message.message_id,
        )

        try:
            res = await model.generate(parsed)
            images = res.images
            for r in images:
                upload_asset(
                    context=context,
                    local_path=r.url,
                    db=bot.db,
                    storage=bot.storage,
                    folder='outputs',
                )

            if len(images) == 1:
                await bot.messaging_service.edit_message_media(
                    chat_id=msg.chat_id,
                    message_id=msg.id,
                    media={
                        'image': images[0].url
                    },
                    text=images[0].prompt,
                )
            elif len(images) > 1:
                for r in images:
                    await bot.messaging_service.send_media(
                        chat_id=msg.chat_id,
                        media={
                            'image': r.url
                        },
                        text=r.prompt,
                    )
                await bot.messaging_service.delete_message(
                    message_id=msg.id,
                    chat_id=msg.chat_id,
                )
        except Exception as e:
            await send_error_message_image(bot.messaging_service, e.__str__(), message)


class DescribeImage(ModelBackedCommand):
    def __init__(self, models):
        super().__init__(
            command='describe',
            name="describe_image",
            description="Describes an image",
            examples=[
                "/describe",
            ],
            models=models,
        )

    async def run(self, parsed, model, message, context, bot):
        return await bot.messaging_service.send_message(
            reply_to_message_id=message.message_id,
            chat_id=message.chat_id,
            text="Please send me an image to describe",
        )
