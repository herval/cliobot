import base64
import io
import os.path
import random

import requests
from PIL import Image

from cliobot.commands import Model, BasePrompt, GenerationResults
from cliobot.utils import base64_to_bytes, abs_path


def save_image(base64data, folder):
    image = Image.open(
        io.BytesIO(
            base64_to_bytes(base64data)
        ))
    filepath = abs_path(os.path.join(
        folder,
        f'{str(int(random.random() * 100000000))}.png'))
    image.save(filepath)
    return filepath


class Txt2imgPrompt(BasePrompt):
    steps: int = 20
    sampler: str = 'DPM++ 2M SDE'
    width: int = 512
    height: int = 512
    batchcount: int = 1
    batchsize: int = 1
    cfg: int = 7
    seed: int = -1
    negative: str = ''


class Txt2img(Model):
    def __init__(self, model, client):
        super().__init__(
            prompt_class=Txt2imgPrompt,
        )
        self.client = client
        self.model = model

    async def generate(self, prompt):
        print("here!", prompt)
        return await self.client.txt2img(prompt)


class WebuiClient:

    def __init__(self, endpoint, auth, temp_dir = 'tmp'):
        self.endpoint = endpoint
        self.auth = auth  # TODO use
        self.temp_dir = temp_dir

    def get_models(self):
        return self._get(f'/sdapi/v1/sd-models')

    async def txt2img(self, parsed) -> GenerationResults:
        params = {
            'cfg_scale': parsed.cfg,
            'width': parsed.width,
            'height': parsed.height,
            'batch_size': parsed.batchsize,
            'n_iter': parsed.batchcount,
            'seed': parsed.seed,
            'prompt': parsed.prompt,
            'negative_prompt': parsed.negative,
            'steps': parsed.steps,
            'sampler_name': parsed.sampler,
        }  # TODO previews

        r = self._post(f'/sdapi/v1/txt2img', params)

        imgs = []

        for i in r['images']:
            path = save_image(i, self.temp_dir)
            imgs.append({
                'url': path,
                'prompt': parsed.prompt,
            })

        return GenerationResults(
            texts=[],
            images=imgs,
        )

        # TODO
        #     "styles": [
        #         "string"
        #     ],
        #     "subseed": -1,
        #     "subseed_strength": 0,
        #     "seed_resize_from_h": -1,
        #     "seed_resize_from_w": -1,
        #     "restore_faces": true,
        #     "tiling": true,
        #     "do_not_save_samples": false,
        #     "do_not_save_grid": false,
        #     "eta": 0,
        #     "denoising_strength": 0,
        #     "s_min_uncond": 0,
        #     "s_churn": 0,
        #     "s_tmax": 0,
        #     "s_tmin": 0,
        #     "s_noise": 0,
        #     "override_settings": {},
        #     "override_settings_restore_afterwards": true,
        #     "refiner_checkpoint": "string",
        #     "refiner_switch_at": 0,
        #     "disable_extra_networks": false,
        #     "comments": {},
        #     "enable_hr": false,
        #     "firstphase_width": 0,
        #     "firstphase_height": 0,
        #     "hr_scale": 2,
        #     "hr_upscaler": "string",
        #     "hr_second_pass_steps": 0,
        #     "hr_resize_x": 0,
        #     "hr_resize_y": 0,
        #     "hr_checkpoint_name": "string",
        #     "hr_sampler_name": "string",
        #     "hr_prompt": "",
        #     "hr_negative_prompt": "",
        #     "script_name": "string",
        #     "script_args": [],
        #     "send_images": true,
        #     "save_images": false,
        #     "alwayson_scripts": {}
        # }

    def _get(self, path):
        args = {}
        if self.auth:
            encoded_credentials = base64.b64encode(self.auth.encode()).decode()
            args['headers'] = {
                'Authorization': f'Basic {encoded_credentials}',
            }

        return requests.get(self.endpoint + path, **args).json()

    def _post(self, path, params):
        args = {}
        if self.auth:
            encoded_credentials = base64.b64encode(self.auth.encode()).decode()
            args['headers'] = {
                'Authorization': f'Basic {encoded_credentials}',
            }

        return requests.post(self.endpoint + path, json=params, **args).json()
