import unittest

from lib.commands import BasePrompt
from lib.config import load_config
from lib.ollama.client import OllamaText


class TestOpenAIClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        config = load_config('config.yml')
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

