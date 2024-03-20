import os
import queue
import re

import i18n
import yaml
from dotenv import load_dotenv

from cliobot.bots import BaseBot
from cliobot.bots.command_handler import CommandHandler
from cliobot.cache import InMemoryCache
from cliobot.commands.audio import Transcribe
from cliobot.commands.help import Help
from cliobot.commands.images import TextToImage, DescribeImage
from cliobot.commands.session import SetPreference, ListPreferences, ClearContext, PrintContext, ListModels
from cliobot.commands.text import Ask
from cliobot.errors import BaseErrorHandler
from cliobot.metrics import BaseMetrics
from cliobot.translator import NullTranslator
from cliobot.utils import abs_path


def substitute_env_vars(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = substitute_env_vars(value)

    if isinstance(data, list):
        for i, value in enumerate(data):
            data[i] = substitute_env_vars(value)

    elif isinstance(data, str):
        # Find all occurrences of $ENV_VAR
        matches = re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)', data)

        # Replace each occurrence with the corresponding environment variable value
        for match in matches:
            env_var_value = os.environ.get(match, f"${match}")
            data = data.replace(f"${match}", env_var_value)

    return data


def load_config(filename):
    load_dotenv(
        dotenv_path=abs_path('.env'),
        verbose=True,
    )

    with open(abs_path(filename)) as f:
        config = yaml.safe_load(f)

    return substitute_env_vars(config)



class ConfigLoader:
    # prepares a Cliobot based on a config.yml file

    def __init__(self, configPath, tmpFolder=None):
        config = load_config(configPath)
        self.config = config
        self.tmp_folder = tmpFolder or abs_path("tmp")

    def build(self) -> BaseBot:
        os.makedirs(self.tmp_folder, exist_ok=True)

        storage_driver = self.config['storage']['driver']
        if storage_driver == 'local':
            from cliobot.storage import LocalStorage
            storage = LocalStorage(self.config['storage']['folder'])
        elif storage_driver == 's3':
            from cliobot.storage.s3 import S3Storage
            storage = S3Storage(
                access_key=self.config['storage']['s3']['access_key'],
                secret=self.config['storage']['s3']['secret_key'],
                bucket=self.config['storage']['s3']['bucket'],
                region=self.config['storage']['s3']['region'],
            )
        else:
            raise Exception('unsupported storage driver:', storage_driver)

        db_driver = self.config['db']['driver']
        if db_driver == 'sqlite3':
            from cliobot.db.sqlite import SqliteDb
            db = SqliteDb(
                file=self.config['db'].get('file', abs_path('clibot.db'))
            )
        elif db_driver == 'inmemory':
            from cliobot.db import InMemoryDb
            db = InMemoryDb()
        else:
            raise Exception('unsupported db driver:', db_driver)

        error_handler = BaseErrorHandler()
        metrics = BaseMetrics(error_handler)

        commands = [
            ClearContext(),
            PrintContext(),
            SetPreference(),
            ListPreferences(),
        ]

        txt2img_models: dict = {}
        transcribe_models: dict = {}
        describe_models: dict = {}
        ask_models: dict = {}

        if self.config.get('replicate', None):
            print("**** Using Replicate API ****")
            from cliobot.replicate.client import ReplicateEndpoint

            models = self.config['replicate']['endpoints']
            for v in models:
                cli = ReplicateEndpoint(
                    v['kind'],
                    self.config['replicate']['api_token'],
                    v['version'],
                    v['params'],
                )
                if v['kind'] == 'describe':
                    describe_models[v['model']] = cli
                elif v['kind'] == 'transcribe':
                    transcribe_models[v['model']] = cli
                elif v['kind'] == 'image':
                    txt2img_models[v['model']] = cli
                elif v['kind'] == 'ask':
                    ask_models[v['model']] = cli

        if self.config.get('ollama', None):
            from cliobot.ollama.client import OllamaText

            print("**** Using Ollama API ****")
            endpoint = self.config['ollama']['endpoint']
            for v in self.config['ollama']['models']:
                m = OllamaText(
                    endpoint=endpoint,
                )
                h = None

                if v['kind'] == 'ask':
                    h = ask_models
                elif v['kind'] == 'describe':
                    h = describe_models
                elif v['kind'] == 'transcribe':
                    h = transcribe_models
                elif v['kind'] == 'image':
                    h = txt2img_models

                if h:
                    h[v['model']] = m

        if self.config.get('openai', None):
            print("**** Using OpenAI API ****")
            from cliobot.openai.client import OpenAIClient, GPTPrompt, Whisper1, Dalle3, Gpt4Vision

            openai_client = OpenAIClient(
                endpoints=self.config['openai']['endpoints'],
                metrics=metrics,
            )

            models = self.config['openai']['models']
            if 'dall-e-3' in models:
                txt2img_models['dall-e-3'] = Dalle3(openai_client)

            if 'whisper-1' in models:
                transcribe_models['whisper-1'] = Whisper1(openai_client)

            if 'gpt-4' in models:
                ask_models['gpt-4'] = GPTPrompt(openai_client)

            if 'gpt-4-vision-preview' in models:
                describe_models['gpt-4-vision-preview'] = Gpt4Vision(openai_client)

        if self.config.get('webui', None):
            from cliobot.webui.client import WebuiClient, Txt2img

            print("**** Using Auto1111 WebUI API ****")
            client = WebuiClient(
                self.config['webui']['endpoint'],
                self.config['webui'].get('auth', None),
                temp_dir=self.tmp_folder,
            )

            # get all models on boot
            ms = client.get_models()
            for m in ms:
                print("MODEL:", m['model_name'], 'loaded from webui')
                txt2img_models[m['model_name']] = Txt2img(m['model_name'], client)


        defaults = self.config.get('default_models', {})

        if len(txt2img_models) > 0:
            commands.append(TextToImage(txt2img_models, defaults.get('image', None)))

        if len(transcribe_models) > 0:
            commands.append(Transcribe(transcribe_models, defaults.get('transcribe', None)))

        if len(describe_models) > 0:
            commands.append(DescribeImage(describe_models, defaults.get('describe', None)))

        if len(ask_models) > 0:
            commands.append(Ask(ask_models, defaults.get('ask', None)))

        commands.append(
            ListModels(
                txt2img_models,
                transcribe_models,
                describe_models,
                ask_models,
            ))
        commands.append(Help(commands))

        self.internal_queue = queue.Queue()

        i18n.load_path.append(abs_path('i18n'))
        i18n.set('filename_format', '{locale}.{format}')

        cache = InMemoryCache()
        db = db

        translator = NullTranslator()

        if self.config['mode'] == 'command':
            handler = lambda: CommandHandler(
                fallback_commands=self.config['fallback_commands'],
                commands=commands,
            )
        else:
            raise Exception('unsupported mode:', self.config['mode'])

        plat = self.config['bot']['platform']
        if plat == 'telegram':
            from cliobot.bots.telegram_bot import TelegramBot

            apikey = self.config['bot']['token']

            return TelegramBot(
                internal_queue=self.internal_queue,
                db=db,
                storage=storage,
                translator=translator,
                apikey=apikey,
                bot_language='en',
                cache=cache,
                metrics=metrics,
                handler_fn=handler,
            )
        else:
            raise Exception('unsupported platform:', plat)
