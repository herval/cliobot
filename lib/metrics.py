class BaseMetrics:
    def capture_exception(self, exception, app_name, user_id='anonymous'):
        print(f"EXCEPTION: {exception} / {app_name} / {user_id}")

    def send_event(self, event, app_name, user_id='anonymous', params=None):
        print(f"EVENT: {event} / {app_name} / {user_id} / {params}")

