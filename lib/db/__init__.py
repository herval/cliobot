class InMemoryDb:
    def __init__(self):
        print("**** Keeping state in memory only ****")

        self.jobs = {}
        self.profiles = {}
        self.messages = {}


    def update_job(self, job_id, app_name, fields):
        pass

    def get_or_create_profile(self, user_id):
        return {
            'user_id': user_id,
        }

    def get_model(self, slug, kind):
        return None

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
