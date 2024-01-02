from dataclasses import Field

from lib.commands import BaseCommand, BasePromptModel


# A set of commands using OpenAI's APIs

class Ask(BaseCommand):
    def __init__(self, messaging_service, openai_client):
        super().__init__(
            command='ask',
            name="ask",
            description="Ask a question using GPT-4",
            examples=[
                "/ask",
            ],
        )
        self.openai_client = openai_client

    async def run(self, parsed, message, context, messaging_service):
        pass



class Dalle3Prompt(BasePromptModel):
    prompt: str = None
    size: str = Field(default='1024x1024',
                      alias='size',
                      error_msg='Supported sizes: 1024x1792, 1024x1024, 1792x1024')

class Dalle3(BaseCommand):
    def __init__(self, openai_client):
        super().__init__(
            command='dalle3',
            name="dalle3",
            description="Generates an image using DALL-E 3",
            examples=[
                "/dalle3",
            ],
            prompt_class=Dalle3Prompt
        )
        self.openai_client = openai_client

    async def run(self, parsed, message, context, messaging_service):
        res = self.openai_client.dalle3_txt2img(
            prompt=parsed.prompt,
            num=1,
            size=parsed.size,
        )

        return await messaging_service.send_media(
            text=res[0].revised_prompt,
            media=res[0].url,
            chat_id=message.chat_id,
        )