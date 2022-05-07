from .callable import Callable
from .environment import Environment
from .returnable import Return

class Function(Callable):
    def __init__(self, declaration, closure, is_initializer):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def __str__(self):
        return f'<fun {self.declaration.name.lexeme}>'

    def arity(self):
        return len(self.declaration.parameters)

    def call(self, interpreter, arguments):
        env = Environment(self.closure)
        for i in range(len(self.declaration.parameters)):
            env.define(self.declaration.parameters[i].lexeme, arguments[i])

        try:
            interpreter.execute_block(self.declaration.body, env)
        except Return as R:
            if self.is_initializer:
                return self.closure.get_at(0, 'this')
            return R.value

        if self.is_initializer:
            return self.closure.get_at(0, 'this')

    def bind(self, instance):
        env = Environment(self.closure)
        env.define('this', instance)
        return Function(self.declaration, env, self.is_initializer)
