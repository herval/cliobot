import unittest

from cliobot.config import load_config
from cliobot.metrics import BaseMetrics
from cliobot.openai.client import OpenAIClient
from cliobot.utils import abs_path


class TestOpenAIClient(unittest.TestCase):

    def setUp(self):
        config = load_config('config.yml')
        self.openai_client = OpenAIClient(
            [config['openai']['endpoints'][0]],
            BaseMetrics(None),
        )

        self.azure_client = OpenAIClient(
            config['openai']['endpoints'][1:],
            BaseMetrics(None),
        )

    def test_transcribe(self):
        res = self.openai_client.transcribe(abs_path('test/res/hello.mp3'))
        print(res)
        self.assertEqual(res, 'Hello there')

        res = self.azure_client.transcribe(abs_path('test/res/hello.mp3'))
        print(res)
        self.assertEqual(res, 'Hello there')

    def test_dalle_txt2img(self):
        res = self.azure_client.dalle3_txt2img(
            'a blue coffee cup on top of a red table, besides a white plate',
            2,
            '512x512')  # size gets fixed automatically
        print(res)
        assert len(res) == 1  # always 1

        res = self.openai_client.dalle3_txt2img(
            'a blue coffee cup on top of a red table, besides a white plate',
            2,
            '512x512')  # size gets fixed automatically
        print(res)
        assert len(res) == 1  # always 1

    def test_ask(self):
        # res = self.openai_client.ask('What is the meaning of life?')
        # print(res)
        # assert len(res) > 0

        res = self.azure_client.ask('What is the meaning of life?')
        print(res)
        assert len(res) > 0

    def test_img2txt(self):
        res = self.openai_client.img2text(
            "what's in this image?",
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRQX0YDlVeH53k9oST-dmEt-5w5IQwdxu7BhywRS2Q9cg&s'
        )
        print(res)
        self.assertIsNotNone(res)

        res = self.openai_client.img2text(
            "what's in this image?",
            abs_path('test/res/sandwich.jpg')
        )
        print(res)
        self.assertIsNotNone(res)
