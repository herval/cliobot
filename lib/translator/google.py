from lib.translator import BaseTranslator
import deep_translator


class Google(BaseTranslator):
    def __init__(self):
        self.translator = deep_translator.GoogleTranslator(source="auto", target="en")


    def translate(self, txt):
        return self.translator.translate(txt).text

