import os
import queue

import yaml

import i18n
from lib.bots.command_handler import CommandHandler
from lib.cache import InMemoryCache
from lib.commands.context import ClearContext, PrintContext
from lib.commands.help import Help
from lib.errors import BaseErrorHandler
from lib.metrics import BaseMetrics
from lib.translator import NullTranslator
from lib.utils import abs_path

BASE_COMMANDS = [
    ClearContext,
    PrintContext,
]


class App:

    def __init__(self):
        with open('config.yml', 'r') as file:
            config = yaml.safe_load(file)

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

        commands = [k() for k in BASE_COMMANDS]

        if config.get('openai', None):
            from lib.openai.client import OpenAIClient
            from lib.openai.commands import Dalle3, Ask

            openai_client = OpenAIClient(
                endpoints=config['openai']['endpoints'],
                metrics=metrics,
            )

            commands.extend([
                Ask(openai_client),
                Dalle3(openai_client),
            ])

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
                fallback_command=Help(
                    commands,
                ),
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
