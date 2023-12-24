

class BaseTranslator:
    def translate(self, txt):
        raise NotImplementedError()

class NullTranslator:
    def __init__(self):
        print("**** Auto translation disabled ****")

    def translate(self, txt):
        return txt