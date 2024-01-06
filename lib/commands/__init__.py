import shlex
from typing import Optional

from pydantic import BaseModel, ValidationError


class BasePromptModel(BaseModel):
    command: str
    prompt: str


def parse_message(message_text, context_dict, pydantic_type) -> BasePromptModel:
    # Split the input string into tokens
    tokens = message_text.split()

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

    for k, v in context_dict.items():
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

    return pydantic_type(**params)


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
    def __init__(self, command, name, description, examples, prompt_class=BasePromptModel, reply_only=False):
        self.command = command
        self.name = name
        self.description = description
        self.examples = examples
        self.reply_only = reply_only
        self.prompt_class = prompt_class

    async def parse(self, message, context, messaging_service) -> Optional[BasePromptModel]:
        """Parse message + context, returns True if command is fully parsed (no optionals missing)"""
        try:
            return parse_message(message.text, context.to_dict(), self.prompt_class)
        except ValidationError as e:
            await notify_errors(e, messaging_service, message.chat_id, message.message_id)
            return None

    async def run(self, parsed, message, context, bot) -> bool:
        """
        execute the command and return True if the command was completely handled, or False if the command was either
        not handled or needs more data (eg. a file upload is pending).

        After a command is handled, the current context is cleared.

        :param parsed:
        :param message:
        :param context:
        :param bot: bot instance
        :return:
        """
        raise NotImplementedError()
