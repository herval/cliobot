from pydantic import Field

from lib.commands import BaseCommand, BasePromptModel
from lib.openai.client import VALID_DALLE3_SIZES


# A set of commands using OpenAI's APIs

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

    async def run(self, parsed, message, context, messaging_service):
        res = self.openai_client.ask(
            message.text,
        )
        await messaging_service.send_message(
            text=res,
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )


class Dalle3Prompt(BasePromptModel):
    prompt: str = None
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

    async def run(self, parsed, message, context, messaging_service):
        await messaging_service.send_message(
            text="Generating image, please wait",
            chat_id=message.chat_id,
        )

        res = self.openai_client.dalle3_txt2img(
            prompt=parsed.prompt,
            num=1,
            size=parsed.size,
        )

        return await messaging_service.send_media(
            text=res[0].revised_prompt,
            media={
                'image': res[0].url
            },
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
        )