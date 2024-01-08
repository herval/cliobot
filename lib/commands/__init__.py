from typing import List

from pydantic import BaseModel, ValidationError


class BasePrompt(BaseModel):
    command: str
    prompt: str
    model: str = None


async def send_error_message_image(messaging_service, text, message):
    try:
        await messaging_service.delete_message(
            chat_id=message.chat_id,
            message_id=message.message_id,
        )
    except Exception as e:
        print(e)

    await messaging_service.send_message(
        chat_id=message.chat_id,
        text=f"🚨 {text}",
    )


async def send_error_message(messaging_service, text, chat_id):
    await messaging_service.send_message(
        chat_id=chat_id,
        text=f"🚨 {text}",
    )


def to_params(message, context) -> dict:
    # Split the input string into tokens
    tokens = message.text.split()

    if message.audio:
        context.set('audio', message.audio)

    if message.voice:
        context.set('voice', message.voice)

    if message.video:
        context.set('video', message.video)

    if message.image:
        context.set('image', message.image)

    command = None
    if len(tokens) > 0:
        # Extract the command
        command = tokens[0]
        if command.startswith('/'):
            command = command[1:]

    prompt = None
    if len(tokens) > 1:
        # Extract the prompt (the part after the command)
        prompt = ' '.join(tokens[1:])
        if ' --' in prompt:
            prompt = prompt[:prompt.index(' --')]

    # Initialize the Pydantic model
    params = {
        'command': command,
        'prompt': prompt
    }

    for k, v in context.to_dict().items():
        params[k] = v

    # Iterate through the tokens to find key-value pairs (e.g., --bla abc)
    for i in range(1, len(tokens), 2):
        value = None
        if i + 1 < len(tokens) and tokens[i].startswith('--'):
            key = tokens[i][2:]

            while i + 1 < len(tokens) and not tokens[i + 1].startswith('--'):
                if value:
                    value += ' '
                else:
                    value = ''
                value += tokens[i + 1]
                i += 1

            params[key] = value

    return params


async def notify_errors(exc, messaging_service, chat_id, reply_to_message_id=None):
    if isinstance(exc, ValidationError):
        errors = []
        for e in exc.errors():
            errors.append(f'{e["loc"][0]}: {e["msg"]}')
        await messaging_service.send_message(
            text='Whoops!\n' + '\n'.join(errors),
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
        )
    else:
        raise exc


class BaseCommand:
    def __init__(self, command, name, description, examples, reply_only=False):
        self.command = command
        self.name = name
        self.description = description
        self.examples = examples
        self.reply_only = reply_only

    async def process(self, message, context, bot) -> bool:
        """
        parses message and returns the right model to handle it, or None if the message is not a valid command
        """
        raise NotImplementedError()


class ImageUrl(BaseModel):
    url: str
    prompt: str = None


class GenerationResults(BaseModel):
    texts: List[str] = None
    images: List[ImageUrl] = None


class Model:
    """
    A model is a class that contains a prompt class and a generate function that takes a prompt and returns a result
    """

    def __init__(self, prompt_class):
        self.prompt_class = prompt_class

    async def generate(self, parsed) -> GenerationResults:
        raise NotImplementedError()


class ModelBackedCommand(BaseCommand):
    def __init__(self, command, name, description, examples, models, reply_only=False):
        super().__init__(command, name, description, examples, reply_only)
        self.models = models

    async def run(self, parsed, model, message, context, bot) -> bool:
        """
        execute the command and return True if the command was completely handled, or False if the command was either
        not handled or needs more data (eg. a file upload is pending).

        After a command is handled, the current context is cleared.
        """
        raise NotImplementedError()

    async def process(self, message, context, bot) -> bool:
        """
        parses message and returns the right model to handle it, or None if the message is not a valid command
        """

        params = to_params(message, context)
        if params.get('model', None) is None:
            model = next(iter(self.models.values()))
        else:
            model = self.models.get(params['model'], None)
            if model is None:
                await send_error_message(bot.messaging_service,
                                         f"Model {params['model']} not found",
                                         message.chat_id)
                return False

        try:
            parsed = model.prompt_class(**params)
        except ValidationError as e:
            await notify_errors(e, bot.messaging_service, message.chat_id, message.message_id)
            return False

        return await self.run(parsed, model, message, context, bot)
