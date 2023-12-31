

class BaseCommand:

    def __init__(self, command, name, description, examples, reply_only=False):
        self.command = command
        self.name = name
        self.description = description
        self.examples = examples
        self.reply_only = reply_only

    async def run(self, message, context):
        raise NotImplementedError()



