from mixpanel import Mixpanel
from mixpanel_async import AsyncBufferedConsumer
from retry import retry

from lib.metrics import BaseMetrics


class MixpanelMetrics(BaseMetrics):
    def __init__(self, key, error_handler):
        self.mp = None
        self.error_handler = error_handler
        if key != '':
            self.mp = Mixpanel(key, consumer=AsyncBufferedConsumer())

    def capture_exception(self, exception, app_name, user_id='anonymous'):
        self.error_handler.capture_exception(exception)
        self.send_event('error', app_name, user_id, {
            'error': exception.__str__()
        })

    @retry(tries=2, delay=1)
    def send_event(self, event, app_name, user_id='anonymous', params=None):
        if params is None:
            params = {}

        try:
            if self.mp:
                self.mp.track(user_id, event, {
                    'app': app_name,
                    **params,
                })
            else:
                print(f"EVENT: {event} / {app_name} / {user_id} / {params}")
        except Exception as e:
            self.error_handler.capture_exception(e)
