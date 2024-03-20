from typing import Optional


class Database:

    def set_chat_context(self, user_id, context, preferences):
        raise NotImplementedError()

    def create_or_get_chat_session(self, user_id):
        raise NotImplementedError()

    def save_message(self,
                     user_id, chat_id, text, external_id,
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


