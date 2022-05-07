from .error import error

class Instance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def __str__(self):
        return f'{self.klass} instance'

    def error(self, token, msg):
        error(token.line, msg)

    def get(self, name):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        self.error(name, f"Undefined property '{name.lexeme}'")

    def set(self, name, value):
        self.fields[name.lexeme] = value
