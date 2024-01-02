import os

import i18n

from lib.cache import InMemoryCache
from lib.db import InMemoryDb
from lib.errors import BaseErrorHandler
from lib.metrics import BaseMetrics
from lib.storage import LocalStorage
from lib.translator import NullTranslator
from lib.utils import abs_path


class BaseApp:
    def __init__(self,
                 internal_queue,
                 storage,
                 metrics=None,
                 error_handler=None,
                 cache=None,
                 db=None,
                 translator=None
                 ):
        self.error_handler = error_handler or BaseErrorHandler()
        self.metrics = metrics or BaseMetrics(self.error_handler)
        self.internal_queue = internal_queue

        i18n.load_path.append(abs_path('i18n'))
        i18n.set('filename_format', '{locale}.{format}')

        self.cache = cache or InMemoryCache()

        self.db = db or InMemoryDb()

        self.storage = storage

        self.temp_dir = abs_path("tmp")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.translator = translator or NullTranslator()

    async def run(self):
        raise NotImplementedError()
