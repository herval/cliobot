import json
import sqlite3
from typing import Optional

from lib.db import Database
from lib.utils import abs_path


class SqliteDb(Database):

    def __init__(self, file):
        self.conn = sqlite3.connect(file, check_same_thread=False)
        self.conn.row_factory = dict_factory
        self._create_tables()

    def create_or_get_chat_session(self, external_user_id, app):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM chat_sessions WHERE external_user_id = ? AND app = ?",
            (external_user_id, app)
        )
        res = cur.fetchone()
        if res is None:
            cur.execute(
                "INSERT INTO chat_sessions (external_user_id, app) VALUES (?, ?)",
                (external_user_id, app)
            )
            self.conn.commit()
            return self.create_or_get_chat_session(external_user_id, app)
        else:
            return res

    def save_message(self, user_id, chat_id, text, app, external_id,
                     image=None, audio=None, voice=None, video=None,
                     is_forward=False, context=None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages(external_id, external_user_id, external_chat_id, text, app, external_image_id, external_audio_id, external_voice_id, external_video_id, is_forward) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (external_id, user_id, chat_id, text, app, image, audio, voice, video, is_forward)
        )
        self.conn.commit()

    def get_chat_context(self, app_name, chat_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT context FROM chat_sessions WHERE id = ? AND app = ?",
            (chat_id, app_name)
        )
        res = cur.fetchone()
        if res is None:
            return {}
        else:
            return json.loads(res)

    def set_chat_context(self, app_name, chat_id, context):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE chat_sessions SET context = ? WHERE id = ? AND app = ?",
            (json.dumps(context), chat_id, app_name)
        )
        self.conn.commit()

    def get_asset(self, external_id, user_id, chat_id) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM assets WHERE external_id = ? AND external_user_id = ? AND external_chat_id = ?",
            (external_id, user_id, chat_id)
        )
        res = cur.fetchone()
        if res is None:
            return None

        return res


    def save_asset(self, external_id, user_id, chat_id, storage_path) -> (dict, bool):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO assets(external_id, external_user_id, external_chat_id, storage_path) VALUES (?, ?, ?, ?)",
            (external_id, user_id, chat_id, storage_path)
        )
        self.conn.commit()
        return self.get_asset(external_id, user_id, chat_id)


    def _create_tables(self):
        with open(abs_path('schema.sql'), 'r') as f:
            self.conn.executescript(f.read())


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
