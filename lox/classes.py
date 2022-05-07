from .callable import Callable
from .instance import Instance

class Class(Callable):
    def __init__(self, name, methods):
        self.name = name
        self.methods = methods

    def __str__(self):
        return self.name

    def arity(self):
        init = self.find_method('init')
        if init is None:
            return 0

        return init.arity()

    def call(self, interpreter, arguments):
        instance = Instance(self)
        init = self.find_method('init')
        if init is not None:
            init.bind(instance).call(interpreter, arguments)

        return instance

    def find_method(self, name):
        return self.methods.get(name)
