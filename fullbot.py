from cliobot.config import ConfigLoader

if __name__ == '__main__':
    bot = ConfigLoader('config.yml', 'tmp').build()

    bot.listen()
