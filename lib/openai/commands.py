from pathlib import Path
from typing import Union, Optional

import openai
from pydantic import Field

from lib.commands import BaseCommand, BasePromptModel
from lib.db.utils import upload_asset, cached_get_file
from lib.openai.client import VALID_DALLE3_SIZES
from lib.utils import abs_path


# A set of commands using OpenAI's APIs

class TranscribePrompt(BasePromptModel):
    audio: str
    prompt: Optional[str] = Field(default=None)


class Transcribe(BaseCommand):
    def __init__(self, openai_client):
        super().__init__(
            command='transcribe',
            name="transcribe",
            description="Transcribe audio with an optional prompt",
            examples=[
                "/transcribe <optional prompt> --audio <audio file url>",
            ],
            prompt_class=TranscribePrompt
        )
        self.openai_client = openai_client

    async def run(self, parsed, message, context, bot) -> bool:
        audio = await cached_get_file(
            file_id=parsed.audio,
            context=context,
            bot=bot,
        )

        msg = await bot.messaging_service.send_message(
            text='Transcribing...',
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )

        txt = self.openai_client.transcribe(audio)

        await bot.messaging_service.edit_message(
            chat_id=msg.chat_id,
            message_id=msg.id,
            text=txt,
        )

        return True


class Ask(BaseCommand):
    def __init__(self, openai_client):
        super().__init__(
            command='ask',
            name="ask",
            description="Ask a question using GPT-4",
            examples=[
                "/ask what's the meaning of life?",
            ],
        )
        self.openai_client = openai_client

    async def run(self, parsed, message, context, bot):
        res = self.openai_client.ask(
            parsed.prompt
        )
        await bot.messaging_service.send_message(
            text=res,
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )


class Dalle3Prompt(BasePromptModel):
    size: str = Field(default='1024x1024',
                      examples=VALID_DALLE3_SIZES)


class Dalle3(BaseCommand):
    def __init__(self, openai_client):
        super().__init__(
            command='dalle3',
            name="dalle3",
            description="Generates an image using DALL-E 3",
            examples=[
                "/dalle3 a hamster in space --size 1024x1024",
            ],
            prompt_class=Dalle3Prompt
        )
        self.openai_client = openai_client

    async def run(self, parsed, message, context, bot):
        msg = await bot.messaging_service.send_media(
            text="Generating image, please wait...",
            chat_id=message.chat_id,
            media={
                'image': abs_path('working.png'),
            },
            reply_to_message_id=message.message_id,
        )

        try:
            res = self.openai_client.dalle3_txt2img(
                prompt=parsed.prompt,
                num=1,
                size=parsed.size,
            )
            upload_asset(
                context=context,
                local_path=res[0].url,
                db=bot.db,
                storage=bot.storage,
                folder='outputs',
            )

            await bot.messaging_service.edit_message_media(
                chat_id=msg.chat_id,
                message_id=msg.id,
                media={
                    'image': res[0].url
                },
                text=res[0].revised_prompt,
            )
        except openai.BadRequestError as e:
            await bot.messaging_service.edit_message_media(
                chat_id=msg.chat_id,
                message_id=msg.id,
                text=f"🚨 {e.message}",
                media={
                    'image': abs_path('working.png'),
                },
            )

        return True
