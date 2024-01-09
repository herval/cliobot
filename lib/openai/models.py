from typing import Optional

from pydantic import Field

from lib.commands import BasePrompt, Model, GenerationResults, ImageUrl
from lib.openai.client import VALID_DALLE3_SIZES


# A set of commands using OpenAI's APIs
class TranscribePrompt(BasePrompt):
    audio: str
    model: str = 'whisper1'

class Whisper1(Model):
    def __init__(self, openai_client):
        self.openai_client = openai_client
        super().__init__(
            TranscribePrompt
        )

    async def generate(self, parsed) -> GenerationResults:
        txt = self.openai_client.transcribe(parsed.audio)
        return GenerationResults(texts=[txt])


class GPTPrompt(Model):
    def __init__(self, openai_client):
        super().__init__(
            prompt_class=BasePrompt,
        )
        self.openai_client = openai_client

    async def generate(self, parsed):
        res = self.openai_client.ask(
            parsed.prompt
        )
        return GenerationResults(texts=[res])


class Dalle3Prompt(BasePrompt):
    size: str = Field(default='1024x1024',
                      examples=VALID_DALLE3_SIZES) # TODO adjust size?


class Dalle3(Model):
    def __init__(self, openai_client):
        super().__init__(
            prompt_class=Dalle3Prompt,
        )
        self.openai_client = openai_client

    async def generate(self, parsed) -> GenerationResults:
        res = self.openai_client.dalle3_txt2img(
            prompt=parsed.prompt,
            num=1,
            size=parsed.size,
        )

        return GenerationResults(
            images=[
                ImageUrl(
                    url=img.url,
                    prompt=img.revised_prompt,
                )
                for img in res
            ]
        )
