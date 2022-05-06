from .error import error

class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name, value):
        self.values[name] = value

    def ancestor(self, distance):
        env = self
        for _ in range(distance):
            env = env.enclosing

        return env

    def assign_at(self, distance, name, value):
        self.ancestor(distance).values[name.lexeme] = value

    def get_at(self, distance, name):
        return self.ancestor(distance).values.get(name)

    def get(self, name):
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        self.error(name, f"Undefined variable '{name.lexeme}'")

    def assign(self, name, value):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        self.error(name, f"Undefined variable '{name.lexeme}'")

    def error(self, token, msg):
        error(token.line, msg)
