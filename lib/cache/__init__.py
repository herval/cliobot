

class BaseCache:

    def get_preferences(self, user_id):
        raise NotImplementedError()

    def clear_preferences(self, user_id):
        raise NotImplementedError()

    def delete(self, key):
        raise NotImplementedError()

    def set_preferences(self, user_id, prefs):
        raise NotImplementedError()

    def set_chat_context(self, app_name, chat_id, context):
        raise NotImplementedError()

    def get_chat_context(self, app_name, chat_id):
        raise NotImplementedError()


class InMemoryCache(BaseCache):
    def __init__(self):
        self.cache = {}

    def get_preferences(self, user_id):
        return self.cache.get(f'prefs_{user_id}', None)

    def clear_preferences(self, user_id):
        self.cache.pop(f'prefs_{user_id}', None)

    def delete(self, key):
        self.cache.pop(key, None)

    def set_preferences(self, user_id, prefs):
        self.cache[f'prefs_{user_id}'] = prefs

    def set_chat_context(self, app_name, chat_id, context):
        self.cache[f'context_{app_name}_{chat_id}'] = context

    def get_chat_context(self, app_name, chat_id):
        return self.cache.get(f'context_{app_name}_{chat_id}', None)
