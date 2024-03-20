class BaseMetrics:
    def __init__(self, error_handler):
        self.error_handler = error_handler

    def capture_exception(self, exception, user_id='anonymous'):
        self.error_handler.capture_exception(exception)

    def send_event(self, event, user_id='anonymous', params=None):
        print(f"EVENT: {event} / {user_id} / {params}")
