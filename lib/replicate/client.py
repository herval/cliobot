from replicate.client import Client

from lib.commands import Model, BasePrompt, GenerationResults, ImageUrl
from lib.utils import decode_image


class ReplicatePrompt(BasePrompt):
    image: str
    prompt: str


class ReplicateEndpoint(Model):
    def __init__(self, kind, api_key, version, params):
        super().__init__(
            prompt_class=None,
        )
        self.kind = kind
        self.version = version
        self.api_key = api_key
        self.params = params
        self.client = Client(api_key)

    async def generate(self, params) -> GenerationResults:
        input_args = {}
        for k, v in self.params.items():
            default = v.get('default', None)
            param_name = v.get('alias', k)
            value_map = v.get('value_map', None)

            if v['kind'] == 'image':
                input_args[k] = decode_image(params.get(param_name, default))
            elif v['kind'] == 'bool':
                input_args[k] = params.get(param_name, default) == 'true'
            else:
                input_args[k] = params.get(param_name, default)
                if value_map:
                    input_args[k] = value_map.get(input_args[k], input_args[k])

            if input_args[k] is None:
                del input_args[k]

        res = await self.client.async_run(
            self.version,
            input_args
        )

        txt = ''
        imgs = []

        for r in res:
            if self.kind == 'image':
                imgs.append(
                    ImageUrl(
                        url=r,
                        prompt=params['prompt'],
                    )
                )
            else:
                txt += r

        if len(txt) > 0:
            txts = [txt]
        else:
            txts = []

        return GenerationResults(
            texts=txts,
            images=imgs,
        )



    # def swap_face(self, source, target):
    #     output = self.client.run(
    #         "yan-ops/face_swap:a7d6a0118f021279b8966473f302b1d982fd3920426ebd334e8f64d5caf84418",
    #         input={
    #             "det_thresh": 0.1,
    #             "request_id": "",
    #             "source_image": open(source, 'rb'),
    #             "target_image": open(target, 'rb')
    #         }
    #     )
    #
    #     if output['status'] == 'failed':
    #         raise Exception(output['msg'])
    #
    #     return output['image']
    #
    # def colorize(self, image_path):
    #     output = self.client.run(
    #         "arielreplicate/deoldify_image:0da600fab0c45a66211339f1c16b71345d22f26ef5fea3dca1bb90bb5711e950",
    #         input={
    #             "input_image": open(image_path, "rb"),
    #             'model_name': 'Stable',
    #             "render_factor": 35,
    #         }
    #     )
    #
    #     result = ""
    #     for item in output:
    #         result += item
    #
    #     return result
    #
    # def gfpgan(self, image_path):
    #     output = self.client.run(
    #         "tencentarc/gfpgan:9283608cc6b7be6b65a8e44983db012355fde4132009bf99d976b2f0896856a3",
    #         input={
    #             "img": open(image_path, "rb"),
    #             'scale': 4,
    #             "version": "v1.4"
    #         }
    #     )
    #
    #     result = ""
    #     for item in output:
    #         result += item
    #
    #     return result
