import queue

import yaml

from lib.baseapp import BaseApp
from lib.bots.command_handler import CommandHandler
from lib.commands.context import ClearContext, PrintContext

BASE_COMMANDS = [
    ClearContext,
    PrintContext,
]


class App(BaseApp):

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

        super().__init__(
            internal_queue=queue.Queue(),
            storage=storage,
        )

        commands = [k() for k in BASE_COMMANDS]

        if config.get('openai', None):
            from lib.openai.client import OpenAIClient
            from lib.openai.commands import Dalle3

            openai_client = OpenAIClient(
                endpoints=config['openai']['endpoints'],
                metrics=self.metrics,
            )

            commands.append(*[
                Dalle3(openai_client),
            ])

        plat = config['bot']['platform']
        if plat == 'telegram':
            from lib.bots.telegram_bot import TelegramBot
            from lib.bots.telegram_bot import telegram_bot_id
            from lib.bots.telegram_bot import TelegramMessagingService

            apikey = config['bot']['token']
            app_name = 'telegram_bot'

            tl = TelegramMessagingService(
                apikey=apikey,
                app_name=app_name,
                bot_id=telegram_bot_id(apikey),
                db=self.db,
                commands=commands,
            )

            self.bot = TelegramBot(
                internal_queue=self.internal_queue,
                apikey=apikey,
                app_name=app_name,
                bot_language='en',
                cache=self.cache,
                commands=commands,
                handler_fn=lambda: CommandHandler(
                    commands=commands,
                    app_name=app_name,
                    bot_id=telegram_bot_id(apikey),
                    messaging_service=tl,
                    internal_queue=self.internal_queue,
                    db=self.db,
                    storage=self.storage,
                    error_handler=self.error_handler,
                    metrics=self.metrics,
                    translator=self.translator,
                ),
            )
        else:
            raise Exception('unsupported platform:', plat)

    def run(self):
        self.bot.listen()


if __name__ == '__main__':
    app = App()
    app.run()
