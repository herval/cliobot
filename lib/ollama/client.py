import json

from lib.commands import Model, GenerationResults, BasePrompt
import requests


class OllamaText(Model):
    def __init__(self, endpoint):
        super().__init__(
            prompt_class=BasePrompt,
        )
        self.endpoint = endpoint

    async def generate(self, parsed) -> GenerationResults:
        r = requests.post(f'{self.endpoint}/api/generate',
                          json={
                              'model': parsed.model,
                              'prompt': parsed.prompt,
                              'stream': True,
                          },
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

            if body.get('done', True):
                return GenerationResults(
                    texts=[response.strip()]
                )
