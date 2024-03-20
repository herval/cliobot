import json
from typing import Optional

import requests

from cliobot.commands import Model, GenerationResults, BasePrompt
from cliobot.utils import decode_image


class OllamaPrompt(BasePrompt):
    prompt: Optional[str] = "what's in this image?"
    image: Optional[str]

class OllamaText(Model):
    def __init__(self, endpoint):
        super().__init__(
            prompt_class=OllamaPrompt,
        )
        self.endpoint = endpoint

    async def generate(self, parsed) -> GenerationResults:
        params = {
            'model': parsed.model,
            'prompt': parsed.prompt,
        }

        if parsed.image:
            params['images'] = [decode_image(parsed.image)]
            if params['images'][0].startswith('data:image'):
                params['images'][0] = params['images'][0].split(',')[1]

        r = requests.post(f'{self.endpoint}/api/generate',
                          json=params,
                          stream=True)
        r.raise_for_status()

        response = ''
        for line in r.iter_lines():
            body = json.loads(line)
            response_part = body.get('response', '')
            print(response_part, end='', flush=True)
            response += response_part

            if 'error' in body:
                raise Exception(body['error'])

        return GenerationResults(
            texts=[response.strip()]
        )
