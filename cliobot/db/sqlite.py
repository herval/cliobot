import json
import sqlite3
from typing import Optional

from cliobot.db import Database
from cliobot.utils import abs_path


class SqliteDb(Database):

    def __init__(self, file):
        self.conn = sqlite3.connect(file, check_same_thread=False)
        self.conn.row_factory = dict_factory
        self._create_tables()

    def create_or_get_chat_session(self, external_user_id):
        cur = self.conn.cursor()  # TODO fix prefs
        cur.execute(
            "SELECT * FROM chat_sessions WHERE external_user_id = ?",
            (external_user_id)
        )
        res = cur.fetchone()
        if res is None:
            cur.execute(
                "INSERT INTO chat_sessions (external_user_id) VALUES (?, ?)",
                (external_user_id)
            )
            self.conn.commit()
            return self.create_or_get_chat_session(external_user_id)
        else:
            res['context'] = json.loads(res['context'])
            res['preferences'] = json.loads(res['preferences'])
            return res

    def save_message(self,
                     user_id,
                     chat_id,
                     text,
                     external_id,
                     image=None,
                     audio=None,
                     voice=None,
                     video=None,
                     is_forward=False):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages(external_id, external_user_id, external_chat_id, text, external_image_id, external_audio_id, external_voice_id, external_video_id, is_forward) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (external_id, user_id, chat_id, text, image, audio, voice, video, is_forward)
        )
        self.conn.commit()

    def set_chat_context(self, user_id, context, preferences):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE chat_sessions SET context = ?, preferences = ? WHERE external_user_id = ?",
            (json.dumps(context), json.dumps(preferences), user_id)
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
