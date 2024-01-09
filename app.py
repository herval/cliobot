import os
import queue

import yaml

import i18n
from lib.bots.command_handler import CommandHandler
from lib.cache import InMemoryCache
from lib.commands.audio import Transcribe
from lib.commands.context import ClearContext, PrintContext
from lib.commands.help import Help
from lib.commands.images import TextToImage, DescribeImage
from lib.commands.text import Ask
from lib.config import load_config
from lib.errors import BaseErrorHandler
from lib.metrics import BaseMetrics

from lib.ollama.client import OllamaText
from lib.translator import NullTranslator
from lib.utils import abs_path


class App:

    def __init__(self):
        config = load_config('config.yml')

        storage_driver = config['storage']['driver']
        if storage_driver == 'local':
            from lib.storage import LocalStorage
            storage = LocalStorage(config['storage']['folder'])
        elif storage_driver == 's3':
            from lib.storage.s3 import S3Storage
            storage = S3Storage(
                access_key=config['storage']['s3']['access_key'],
                secret=config['storage']['s3']['secret_key'],
                bucket=config['storage']['s3']['bucket'],
                region=config['storage']['s3']['region'],
            )
        else:
            raise Exception('unsupported storage driver:', storage_driver)

        db_driver = config['db']['driver']
        if db_driver == 'sqlite3':
            from lib.db.sqlite import SqliteDb
            db = SqliteDb()
        elif db_driver == 'inmemory':
            from lib.db import InMemoryDb
            db = InMemoryDb()
        else:
            raise Exception('unsupported db driver:', db_driver)

        error_handler = BaseErrorHandler()
        metrics = BaseMetrics(error_handler)

        commands = [
            ClearContext(),
            PrintContext(),
            # TextToImage,
            # DescribeImage,
            # Ask,
            # Transcribe,
        ]

        txt2img_models = {}
        transcribe_models = {}
        describe_models = {}
        ask_models = {}

        if config.get('replicate', None):
            print("**** Using Replicate API ****")
            from lib.replicate.client import ReplicateEndpoint

            models = config['replicate']['endpoints']
            for v in models:
                cli = ReplicateEndpoint(
                    v['kind'],
                    config['replicate']['api_token'],
                    v['version'],
                    v['params'],
                )
                if v['kind'] == 'describe':
                    describe_models[v['model']] = cli
                elif v['kind'] == 'transcribe':
                    transcribe_models[v['model']] = cli
                elif v['kind'] == 'describe':
                    describe_models[v['model']] = cli
                elif v['kind'] == 'ask':
                    ask_models[v['model']] = cli

        if config.get('ollama', None):
            print("**** Using Ollama API ****")
            endpoint = config['ollama']['endpoint']
            for m in config['ollama']['models']:
                ask_models[m] = OllamaText(
                    endpoint=endpoint,
                )

        if config.get('openai', None):
            print("**** Using OpenAI API ****")
            from lib.openai.client import OpenAIClient, GPTPrompt, Whisper1, Dalle3, Gpt4Vision

            openai_client = OpenAIClient(
                endpoints=config['openai']['endpoints'],
                metrics=metrics,
            )

            models = config['openai']['models']
            if 'dall-e-3' in models:
                txt2img_models['dall-e-3'] = Dalle3(openai_client)

            if 'whisper-1' in models:
                transcribe_models['whisper-1'] = Whisper1(openai_client)

            if 'gpt-4' in models:
                ask_models['gpt-4'] = GPTPrompt(openai_client)

            if 'gpt-4-vision-preview' in models:
                describe_models['gpt-4-vision-preview'] = Gpt4Vision(openai_client)

        defaults = config.get('default_models', {})

        if len(txt2img_models) > 0:
            commands.append(TextToImage(txt2img_models, defaults.get('image', None)))

        if len(transcribe_models) > 0:
            commands.append(Transcribe(transcribe_models, defaults.get('transcribe', None)))

        if len(describe_models) > 0:
            commands.append(DescribeImage(describe_models, defaults.get('describe', None)))

        if len(ask_models) > 0:
            commands.append(Ask(ask_models, defaults.get('ask', None)))

        commands.append(Help(commands))

        self.internal_queue = queue.Queue()

        i18n.load_path.append(abs_path('i18n'))
        i18n.set('filename_format', '{locale}.{format}')

        cache = InMemoryCache()
        db = db

        temp_dir = abs_path("tmp")
        os.makedirs(temp_dir, exist_ok=True)

        translator = NullTranslator()

        if config['mode'] == 'command':
            handler = lambda: CommandHandler(
                fallback_commands=config['fallback_commands'],
                commands=commands,
            )
        else:
            raise Exception('unsupported mode:', config['mode'])

        plat = config['bot']['platform']
        if plat == 'telegram':
            from lib.bots.telegram_bot import TelegramBot
            from lib.bots.telegram_bot import telegram_bot_id

            apikey = config['bot']['token']
            app_name = 'telegram_bot'

            self.bot = TelegramBot(
                internal_queue=self.internal_queue,
                db=db,
                storage=storage,
                translator=translator,
                apikey=apikey,
                bot_id=telegram_bot_id(apikey),
                app_name=app_name,
                bot_language='en',
                cache=cache,
                commands=commands,
                metrics=metrics,
                handler_fn=handler,
            )
        else:
            raise Exception('unsupported platform:', plat)

        self.bot.listen()


if __name__ == '__main__':
    App()
