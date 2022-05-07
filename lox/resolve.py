import enum

from .ast import expr, stmt
from .error import error

FunctionType = enum.Enum('FunctionType', 'NONE FUNCTION INITIALIZER METHOD')
ClassType = enum.Enum('ClassType', 'NONE CLASS')

class Resolver(expr.Visitor, stmt.Visitor):
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.scopes = []
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def error(self, token, msg):
        error(token.line, msg)

    def resolve(self, statements):
        for statement in statements:
            self.resolve_stmt(statement)

    def resolve_stmt(self, s):
        s.accept(self)

    def resolve_expr(self, e):
        e.accept(self)

    def begin_scope(self):
        self.scopes.append(dict())

    def end_scope(self):
        self.scopes.pop()

    def visit_block_stmt(self, s):
        self.begin_scope()
        self.resolve(s.statements)
        self.end_scope()

    def visit_class_stmt(self, s):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(s.name)
        self.define(s.name)

        self.begin_scope()
        self.scopes[-1]['this'] = True

        for method in s.methods:
            decl = FunctionType.METHOD
            if 'init' == method.name.lexeme:
                decl = FunctionType.INITIALIZER
            self.resolve_function(method, decl)

        self.end_scope()

        self.current_class = enclosing_class

    def visit_var_stmt(self, s):
        self.declare(s.name)
        if s.initializer is not None:
            self.resolve_expr(s.initializer)
        self.define(s.name)

    def declare(self, name):
        if not self.scopes:
            return

        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.error(
                name, f"Already a variable '{name.lexeme}' in this scope"
            )

        scope[name.lexeme] = False

    def define(self, name):
        if not self.scopes:
            return

        self.scopes[-1][name.lexeme] = True

    def visit_variable_expr(self, e):
        if self.scopes and (self.scopes[-1].get(e.name.lexeme) is False):
            self.error(e.name
                , "Can't read local variable in its own initializer")

        self.resolve_local(e, e.name)

    def resolve_local(self, e, name):
        for distance, scope in enumerate(reversed(self.scopes)):
            if name.lexeme in scope:
                self.interpreter.resolve(e, distance)
                return

    def visit_assign_expr(self, e):
        self.resolve_expr(e.value)
        self.resolve_local(e, e.name)

    def visit_function_stmt(self, s):
        self.declare(s.name)
        self.define(s.name)
        self.resolve_function(s, FunctionType.FUNCTION)

    def resolve_function(self, function, function_type):
        enclosing_function = self.current_function
        self.current_function = function_type
        self.begin_scope()
        for param in function.parameters:
            self.declare(param)
            self.define(param)
        self.resolve(function.body)
        self.end_scope()
        self.current_function = enclosing_function

    def visit_expression_stmt(self, s):
        self.resolve_expr(s.expression)

    def visit_if_stmt(self, s):
        self.resolve_expr(s.condition)
        self.resolve_stmt(s.then_branch)
        if s.else_branch is not None:
            self.resolve_stmt(s.else_branch)

    def visit_print_stmt(self, s):
        self.resolve_expr(s.expression)

    def visit_return_stmt(self, s):
        if self.current_function == FunctionType.NONE:
            self.error(s.keyword, "Can't return from top-level code")

        if s.value is not None:
            if FunctionType.INITIALIZER == self.current_function:
                self.error(s.keyword, "Can't return a value from init")
            self.resolve_expr(s.value)

    def visit_while_stmt(self, s):
        self.resolve_expr(s.condition)
        self.resolve_stmt(s.body)

    def visit_binary_expr(self, e):
        self.resolve_expr(e.left)
        self.resolve_expr(e.right)

    def visit_call_expr(self, e):
        self.resolve_expr(e.callee)

        for arg in e.arguments:
            self.resolve_expr(arg)

    def visit_get_expr(self, e):
        self.resolve_expr(e.object)

    def visit_grouping_expr(self, e):
        self.resolve_expr(e.expression)

    def visit_literal_expr(self, e):
        pass # Nichts zu tun...

    def visit_logical_expr(self, e):
        self.resolve_expr(e.left)
        self.resolve_expr(e.right)

    def visit_set_expr(self, e):
        self.resolve_expr(e.value)
        self.resolve_expr(e.object)

    def visit_this_expr(self, e):
        if ClassType.NONE == self.current_class:
            self.error(e.keyword, "Can't use 'this' outside of a class")

        self.resolve_local(e, e.keyword)

    def visit_unary_expr(self, e):
        self.resolve_expr(e.right)
