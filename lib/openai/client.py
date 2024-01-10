from pathlib import Path
from typing import Optional

import openai
from pydantic import Field

from lib.commands import BasePrompt, Model, GenerationResults, ImageUrl
from lib.utils import image_to_base64, open_image, decode_image

VALID_DALLE3_SIZES = ['1024x1792', '1024x1024', '1792x1024']
DALLE3_RATIOS = [float(x[0]) / float(x[1]) for x in
                 [x.split('x') for x in VALID_DALLE3_SIZES]
                 ]


# A set of commands using OpenAI's APIs
class TranscribePrompt(BasePrompt):
    audio: str
    model: str = 'whisper-1'
    prompt: Optional[str] = ""


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
                      examples=VALID_DALLE3_SIZES)  # TODO adjust size?


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


class DescribePrompt(BasePrompt):
    image: str
    prompt: str = "what's this?"


class Gpt4Vision(Model):
    def __init__(self, openai_client):
        super().__init__(
            prompt_class=DescribePrompt,
        )
        self.openai_client = openai_client

    async def generate(self, parsed) -> GenerationResults:
        res = self.openai_client.img2text(
            prompt=parsed.prompt,
            image_url=parsed.image,
        )

        return GenerationResults(texts=[res])


def dalle_size(size):
    if not size in VALID_DALLE3_SIZES:
        # convert to the nearest ratio
        ratio = float(size.split('x')[0]) / float(size.split('x')[1])
        for idx, s in enumerate(DALLE3_RATIOS):
            if ratio <= s:
                return VALID_DALLE3_SIZES[idx]

    return size


class OpenAIClient:
    # OpenAI wrapper that supports multiple regions and a mix of azure + openai apis

    def __init__(self, endpoints, metrics):
        self.metrics = metrics

        self.v1_configs = [v for v in endpoints if v['api_type'] == 'open_ai']
        self.v1_clients = [
            openai.OpenAI(
                api_key=v['api_key'],
                base_url=v['base_url'],
            ) for v in self.v1_configs]

        self.azure_configs = [v for v in endpoints if v['api_type'] == 'azure']
        self.azure_clients = [
            openai.AzureOpenAI(
                api_key=v['api_key'],
                azure_endpoint=v['base_url'],
                api_version=v['api_version'],
            ) for v in self.azure_configs]

    def transcribe(self, audio_file):
        if isinstance(audio_file, str):
            audio_file = Path(audio_file)

        client, model = self._get_client('whisper-1')
        res = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
        )

        return res.text

    def img2text(self, prompt, image_url, max_tokens=300) -> str:
        image_url = decode_image(image_url)

        client, model = self._get_client('gpt-4-vision-preview')

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def dalle3_txt2img(self, prompt, num, size):
        client, model = self._get_client('dall-e-3')
        res = client.images.generate(
            model=model,
            n=1,
            quality='hd',
            size=dalle_size(size),
            prompt=prompt,
        )
        return res.data

    def ask(self, prompt, model_version='gpt-4'):
        client, model = self._get_client(model_version)
        res = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
        )
        return res.choices[0].message.content

    def _get_client(self, model_kind):
        if len(self.azure_clients) > 0:
            for i, v in enumerate(self.azure_configs):
                if v['kind'] == model_kind:
                    return self.azure_clients[i], v['model']

        if len(self.v1_clients) > 0:
            return self.v1_clients[0], model_kind

        raise Exception("No OpenAI client available!")
