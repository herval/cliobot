import unittest
from typing import Optional
from unittest import mock

from pydantic_core._pydantic_core import ValidationError

from lib.bots import MessagingService, Message, Context
from lib.commands import to_params, BasePrompt, notify_errors


def msg(txt):
    return Message(
        text=txt,
        user_id='123',
        chat_id='456',
        message_id='789',
        user={},
    )


def ctx(ctx):
    return Context(
        user_id='123',
        chat_id='456',
        app_name='test',
        context=ctx,
    )


class TestCommandHandler(unittest.IsolatedAsyncioTestCase):

    def test_parse_message(self):
        valid_res = to_params(
            msg("/test hello world ! --bla abc def"),
            ctx({}))

        print(valid_res)
        self.assertEqual(valid_res['command'], 'test')
        self.assertEqual(valid_res['prompt'], 'hello world !')
        self.assertEqual(valid_res['bla'], 'abc def')
        self.assertIsNone(valid_res.get('ble'))

        valid_res = to_params(msg("/test hello world --ble 3"), ctx({'bla': 'abc def'}))
        print(valid_res)
        self.assertEqual(valid_res['command'], 'test')
        self.assertEqual(valid_res['prompt'], 'hello world')
        self.assertEqual(valid_res['bla'], 'abc def')
        self.assertEqual(valid_res['ble'], '3')


    def test_notify_errors(self):
        ms = mock.Mock(MessagingService)
        err = mock.Mock(ValidationError)
        err.errors.return_value = [
            {'loc': ('bla',), 'msg': 'foo'}
        ]

        notify_errors(
            err,
            ms,
            123)

        ms.send_message.assert_called_once_with(text='Whoops!\nbla: foo', chat_id=123, reply_to_message_id=None)
        err.errors.assert_called_once()
