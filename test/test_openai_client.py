import os
import unittest

import yaml

from lib.metrics import BaseMetrics
from lib.openai.client import OpenAIClient
from lib.utils import abs_path


class TestOpenAIClient(unittest.TestCase):

    def setUp(self):
        with open(abs_path('config.test_openai.yml'), 'r') as file:
            config = yaml.safe_load(file)
            self.openai_client = OpenAIClient(
                config['openai']['endpoints'],
                BaseMetrics(None),
            )

        with open(abs_path('config.test_azure.yml'), 'r') as file:
            config = yaml.safe_load(file)
            self.azure_client = OpenAIClient(
                config['openai']['endpoints'],
                BaseMetrics(None),
            )

    def test_transcribe(self):
        res = self.openai_client.transcribe(abs_path('test/res/hello.mp3'))
        print(res)
        assert res == 'Hello there'

        res = self.azure_client.transcribe(abs_path('test/res/hello.mp3'))
        print(res)
        assert res == 'Hello there'

    def test_dalle_txt2img(self):
        res = self.azure_client.dalle3_txt2img(
            'a blue coffee cup on top of a red table, besides a white plate',
            2,
            '512x512') # size gets fixed automatically
        print(res)
        assert len(res) == 1  # always 1

        res = self.openai_client.dalle3_txt2img(
            'a blue coffee cup on top of a red table, besides a white plate',
            2,
            '512x512') # size gets fixed automatically
        print(res)
        assert len(res) == 1  # always 1

