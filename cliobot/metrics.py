class BaseMetrics:
    def capture_exception(self, exception, user_id='anonymous'):
        print(f"EXCEPTION: {exception} / {user_id}")

    def send_event(self, event, user_id='anonymous', params=None):
        print(f"EVENT: {event} / {user_id} / {params}")

