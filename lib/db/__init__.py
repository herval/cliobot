class InMemoryDb:
    def __init__(self):
        print("**** Keeping state in memory only ****")

        self.jobs = {}
        self.profiles = {}
        self.messages = {}
        self.chats = {}


    def update_job(self, job_id, app_name, fields):
        pass

    def get_or_create_profile(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_chat_context(self, app_name, chat_id):
        return self.chats.get(chat_id, {})

    def get_model(self, slug, kind):
        return None

    def set_chat_context(self, app_name, chat_id, context):
        self.chats[chat_id] = context

    def create_or_get_chat_session(self, chat_user_id, app):
        return {
            'user_id': chat_user_id,
            'chat_user_id': chat_user_id,
            'app': app,
        }

    def save_message(self, chat_user_id, chat_id, text, app, external_id,
                     image=None, audio=None, voice=None, video=None,
                     is_forward=False, context=None):
        pass
