import unittest

from cliobot.config import load_config
from cliobot.ollama.client import OllamaText, OllamaPrompt
from cliobot.utils import abs_path


class TestOllamaClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        config = load_config('config.yml')
        self.text_client = OllamaText(
            config['ollama']['endpoint'],
        )

    async def test_text(self):
        res = await self.text_client.generate(
            OllamaPrompt(
                command='',
                prompt='Hello there',
                model='llama2',
            )
        )
        print(res)
        self.assertIsNot(res.texts, [])


    async def test_describe(self):
        res = await self.text_client.generate(
            OllamaPrompt(
                command='',
                prompt='whats this?',
                model='llava',
                image=abs_path('test/res/sandwich.jpg'),
            )
        )
        print(res)
        self.assertIsNot(res.texts, [])
