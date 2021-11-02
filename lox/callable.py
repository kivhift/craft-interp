from abc import ABC, abstractmethod

class Callable(ABC):
    @abstractmethod
    def arity(self): pass

    @abstractmethod
    def call(self, interpreter, arguments): pass
