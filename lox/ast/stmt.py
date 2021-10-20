# Automatically generated
from abc import ABC, abstractmethod
class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor): pass
class Block(Stmt):
    def __init__(self, statements):
        self.statements = statements
    def accept(self, visitor):
        return visitor.visit_block_stmt(self)
class Expression(Stmt):
    def __init__(self, expression):
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)
class Print(Stmt):
    def __init__(self, expression):
        self.expression = expression
    def accept(self, visitor):
        return visitor.visit_print_stmt(self)
class Var(Stmt):
    def __init__(self, name, initializer):
        self.name = name
        self.initializer = initializer
    def accept(self, visitor):
        return visitor.visit_var_stmt(self)
class Visitor(ABC):
    @abstractmethod
    def visit_block_stmt(self, s): pass
    @abstractmethod
    def visit_expression_stmt(self, s): pass
    @abstractmethod
    def visit_print_stmt(self, s): pass
    @abstractmethod
    def visit_var_stmt(self, s): pass
