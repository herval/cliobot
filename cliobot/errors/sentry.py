import os
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from cliobot.errors import BaseErrorHandler


class SentryHandler(BaseErrorHandler):

    def __init__(self, sentry_dsn):
        sentry_sdk.init(
            sentry_dsn,
            integrations=[
                AioHttpIntegration(),
            ],

            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0,
            environment=os.environ.get("ENV", 'development'),
        )

    def capture_exception(self, exception):
        sentry_sdk.capture_exception(exception)

    def set_context(self, data):
        with sentry_sdk.configure_scope() as scope:
            scope.set_user(data)