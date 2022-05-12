from .callable import Callable
from .instance import Instance

class Class(Callable):
    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
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
        if name in self.methods:
            return self.methods[name]

        if self.superclass is not None:
            return self.superclass.find_method(name)
