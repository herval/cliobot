import unittest
from typing import Optional
from unittest import mock

from pydantic_core._pydantic_core import ValidationError

from lib.bots.models import MessagingService
from lib.commands import parse_message, BasePromptModel, notify_errors


class TestClass(BasePromptModel):
    bla: str
    prompt: str
    ble: Optional[int] = None


class TestCommandHandler(unittest.IsolatedAsyncioTestCase):

    def test_parse_message(self):
        valid_res = parse_message("/test hello world --bla abc def", {}, TestClass)
        print(valid_res)
        assert valid_res is not None
        assert valid_res.command == 'test'
        assert valid_res.prompt == 'hello world'
        assert valid_res.bla == 'abc def'
        assert valid_res.ble is None

        valid_res = parse_message("/test hello world --ble 3", {'bla': 'abc def'}, TestClass)
        print(valid_res)
        assert valid_res is not None
        assert valid_res.command == 'test'
        assert valid_res.prompt == 'hello world'
        assert valid_res.bla == 'abc def'
        assert valid_res.ble == 3

        # fails if command is missing
        with self.assertRaises(ValidationError):
            parse_message("", {}, BasePromptModel)

        # fails if missing params
        with self.assertRaises(ValidationError):
            parse_message("/test", {}, TestClass)

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
