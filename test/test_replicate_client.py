import unittest

import yaml

from lib.config import load_config
from lib.replicate.client import ReplicateEndpoint
from lib.utils import abs_path


class TestReplicateClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        config = load_config('config.yml')
        self.describe_client = ReplicateEndpoint(
            config['replicate']['endpoints'][0]['kind'],
            config['replicate']['api_token'],
            config['replicate']['endpoints'][0]['version'],
            config['replicate']['endpoints'][0]['params'],
        )
        self.txt2img_client = ReplicateEndpoint(
            config['replicate']['endpoints'][1]['kind'],
            config['replicate']['api_token'],
            config['replicate']['endpoints'][1]['version'],
            config['replicate']['endpoints'][1]['params'],
        )

    async def test_describe(self):
        res = await self.describe_client.generate(
            {
                'prompt': 'whats this?',
                'image': abs_path('test/res/sandwich.jpg'),
            }
        )
        print(res)
        self.assertIsNot(res.texts, [])
        self.assertIs(res.images, [])

    async def test_txt2img(self):
        res = await self.txt2img_client.generate(
            {
                'prompt': 'a blue coffee cup on top of a red table, besides a white plate',
                'width': 1280,
                'no': 'photography, realistic'
            }
        )
        print(res)
        self.assertIs(res.texts, [])
        self.assertIsNot(res.images, [])
