from cliobot.commands import send_error_message_image, ModelBackedCommand
from cliobot.db.utils import upload_asset, cached_get_file
from cliobot.utils import abs_path


class TextToImage(ModelBackedCommand):
    def __init__(self, models, default_model):
        super().__init__(
            command='image',
            name="image",
            description="Create an image from a text prompt",
            examples=[
                "/image a hamster astronaut floating in space",
            ],
            models=models,
            default_model=default_model,
        )

    async def run_model(self, parsed, model, message, session, bot):
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
                    session=session,
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
    def __init__(self, models, default_model):
        super().__init__(
            command='describe',
            name="describe_image",
            description="Describes an image",
            examples=[
                "/describe",
            ],
            models=models,
            default_model=default_model,
        )

    async def run_model(self, parsed, model, message, session, bot):
        if isinstance(parsed, dict): # unparsed prompt...
            image_id = parsed.get('image', None)
        else:
            image_id = parsed.image

        image = await cached_get_file(
            session=session,
            file_id=image_id,
            bot=bot,
        )
        if isinstance(parsed, dict):
            parsed['image'] = image
        else:
            parsed.image = image

        res = await model.generate(parsed)
        for r in res.texts:
            await bot.messaging_service.send_message(
                text=r,
                chat_id=message.chat_id,
                reply_to_message_id=message.message_id,
            )
