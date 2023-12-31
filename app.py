import os
import queue

from dotenv import load_dotenv

from lib.baseapp import BaseApp
from lib.commands.context import ClearContext
from lib.utils import abs_path

load_dotenv(
    dotenv_path=abs_path('.env' + '.' + os.environ.get("ENV", 'development')),
    verbose=True,
)


class App(BaseApp):

    def __init__(self):
        super().__init__(
            internal_queue=queue.Queue(),
        )

    def run(self):
        commands = [
            ClearContext(),
        ]

        plat = os.getenv('BOT_PLATFORM')
        if plat == 'telegram':
            from lib.bots.telegram_bot import TelegramBot
            from lib.bots.telegram_bot import telegram_bot_id
            from lib.bots.telegram_bot import TelegramMessagingService
            from lib.bots.command_handler import CommandHandler

            apikey = os.environ.get('TELEGRAM_APP_TOKEN')
            app_name = 'telegram_bot'
            bot = TelegramBot(
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
                    messaging_service=TelegramMessagingService(
                        apikey=apikey,
                        app_name=app_name,
                        bot_id=telegram_bot_id(apikey),
                        db=self.db,
                        commands=commands,
                    ),
                    internal_queue=self.internal_queue,
                    db=self.db,
                    storage=self.storage,
                    error_handler=self.error_handler,
                    metrics=self.metrics,
                    translator=self.translator,
                ),
            )

            bot.listen()

        else:
            raise Exception('unsupported platform:', plat)


if __name__ == '__main__':
    app = App()
    app.run()
