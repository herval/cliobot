from typing import Optional


class Database:

    def set_chat_context(self, app_name, user_id, context, preferences):
        raise NotImplementedError()

    def create_or_get_chat_session(self, user_id, app):
        raise NotImplementedError()

    def save_message(self,
                     user_id, chat_id, text, app, external_id,
                     image=None,
                     audio=None,
                     voice=None,
                     video=None,
                     is_forward=False, context=None):
        raise NotImplementedError()

    def get_asset(self, external_id, user_id, chat_id) -> Optional[dict]:
        raise NotImplementedError()

    def save_asset(self, external_id, user_id, chat_id, storage_path) -> dict:
        raise NotImplementedError()


class InMemoryDb(Database):
    def __init__(self):
        print("**** Keeping state in memory only ****")

        self.jobs = {}
        self.profiles = {}
        self.messages = {}
        self.chats = {}

    def update_job(self, job_id, app_name, fields):
        pass

    def get_model(self, slug, kind):
        return None

    def set_chat_context(self, app_name, user_id, context, preferences):
        self.chats[user_id] = context

    def create_or_get_chat_session(self, user_id, app):
        return {
            'user_id': user_id,
            'app': app,
        }

    def save_message(self,
                     user_id,
                     chat_id,
                     text,
                     app,
                     external_id,
                     image=None,
                     audio=None,
                     voice=None,
                     video=None,
                     is_forward=False,
                     context=None):
        pass
