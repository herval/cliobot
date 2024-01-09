import unittest

import yaml

from lib.commands import BasePrompt
from lib.ollama.client import OllamaText
from lib.utils import abs_path


class TestOpenAIClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        with open(abs_path('config.test.yml'), 'r') as file:
            config = yaml.safe_load(file)
            self.text_client = OllamaText(
                config['ollama']['endpoint'],
            )

    async def test_text(self):
        res = await self.text_client.generate(
            BasePrompt(
                command='',
                prompt='Hello there',
                model='llama2',
            )
        )
        print(res)
        self.assertIsNot(res.texts, [])

