import unittest

from lib.config import load_config
from lib.utils import abs_path
from lib.webui.client import WebuiClient, Txt2imgPrompt, save_image


def save_images(imgs):
    for img in imgs:
        save_image(img.url, abs_path('tmp'))


class TestWebuiClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = load_config('config.yml')
        self.client = WebuiClient(
            config['webui']['endpoint'],
            config['webui'].get('auth', None),
        )

    async def test_txt2img(self):
        res = await self.client.txt2img(
            Txt2imgPrompt(
                command='image',
                prompt='a banana',
                model='sdxl',
                steps=5,
                batchsize=2,
            )
        )
        save_images(res.images)
        self.assertIs(len(res.texts), 0)
        self.assertIs(len(res.images), 2)
