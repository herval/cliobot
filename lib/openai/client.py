from pathlib import Path

import openai

VALID_DALLE3_SIZES = ['1024x1792', '1024x1024', '1792x1024']
DALLE3_RATIOS = [float(x[0]) / float(x[1]) for x in
                 [x.split('x') for x in VALID_DALLE3_SIZES]
                 ]


def dalle_size(size):
    if not size in VALID_DALLE3_SIZES:
        # convert to the nearest ratio
        ratio = float(size.split('x')[0]) / float(size.split('x')[1])
        for idx, s in enumerate(DALLE3_RATIOS):
            if ratio <= s:
                return VALID_DALLE3_SIZES[idx]

    return size


class OpenAIClient:
    # OpenAI wrapper that supports multiple regions and a mix of azure + openai apis

    def __init__(self, endpoints, metrics):
        self.metrics = metrics

        self.v1_configs = [v for v in endpoints if v['api_type'] == 'open_ai']
        self.v1_clients = [
            openai.OpenAI(
                api_key=v['api_key'],
                base_url=v['base_url'],
            ) for v in self.v1_configs]

        self.azure_configs = [v for v in endpoints if v['api_type'] == 'azure']
        self.azure_clients = [
            openai.AzureOpenAI(
                api_key=v['api_key'],
                azure_endpoint=v['base_url'],
                api_version=v['api_version'],
            ) for v in self.azure_configs]

    def transcribe(self, audio_file):
        if isinstance(audio_file, str):
            audio_file = Path(audio_file)

        client, model = self._get_client('whisper-1')
        res = client.audio.transcriptions.create(
            file=audio_file,
            model=model,
        )

        return res.text

    def dalle3_txt2img(self, prompt, num, size):
        client, model = self._get_client('dall-e-3')
        res = client.images.generate(
            model=model,
            n=1,
            quality='hd',
            size=dalle_size(size),
            prompt=prompt,
        )
        return res.data

    def ask(self, prompt, model_version='gpt-4'):
        client, model = self._get_client(model_version)
        res = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ]
        )
        return res.choices[0].message.content

    def _get_client(self, model_version):
        if len(self.azure_clients) > 0:
            for i, v in enumerate(self.azure_configs):
                if v['kind'] == model_version:
                    return self.azure_clients[i], v['model']

        return self.v1_clients[0], model_version
