from cliobot.bots import Session
from cliobot.db import Database


class InMemoryDb(Database):
    def __init__(self):
        print("**** Keeping state in memory only ****")

        self.jobs = {}
        self.profiles = {}
        self.messages = {}
        self.chats = {}

    def update_job(self, job_id, fields):
        pass

    def get_model(self, slug, kind):
        return None

    def set_chat_context(self, user_id, context, preferences):
        self.chats[user_id] = context

    def create_or_get_chat_session(self, user_id):
        return Session(
            user_id=user_id,
            chat_id='1',
            context={},
            preferences={},
        )

    def save_message(self,
                     user_id,
                     chat_id,
                     text,
                     external_id,
                     image=None,
                     audio=None,
                     voice=None,
                     video=None,
                     is_forward=False,
                     context=None):
        pass
