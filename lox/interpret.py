from .ast import expr, stmt
from .environment import Environment
from .error import error
from .lex import TokenType

class Interpreter(expr.Visitor, stmt.Visitor):
    def __init__(self):
        self.environment = Environment()

    def interpret(self, statements):
        for statement in statements:
            self.execute(statement)

    def stringify(self, x):
        if x is None:
            return 'nil'

        s = str(x)

        if 'True' == s:
            return 'true'

        if 'False' == s:
            return 'false'

        if isinstance(x, float) and s.endswith('.0'):
            return s[:-2]

        return s

    def error(self, token, msg):
        error(token.line, msg)

    def visit_literal_expr(self, e):
        return e.value

    def visit_logical_expr(self, e):
        left = self.evaluate(e.left)

        if e.operator.type == TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left

        return self.evaluate(e.right)

    def visit_grouping_expr(self, e):
        return self.evaluate(e.expression)

    def evaluate(self, e):
        return e.accept(self)

    def execute(self, s):
        s.accept(self)

    def execute_block(self, statements, environment):
        previous_env = self.environment
        try:
            # Switching out the environment is hacky...
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous_env

    def check_number_operands(self, op, *operands):
        for operand in operands:
            if not isinstance(operand, float):
                self.error(op, f'Operand must be a number: {operand}')

    def visit_unary_expr(self, e):
        right = self.evaluate(e.right)
        match e.operator.type:
            case TokenType.BANG:
                return not self.is_truthy(right)
            case TokenType.MINUS:
                self.check_number_operands(e.operator, right)
                return -right

    def is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    def visit_binary_expr(self, e):
        left = self.evaluate(e.left)
        right = self.evaluate(e.right)
        match e.operator.type:
            case TokenType.GREATER:
                self.check_number_operands(e.operator, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self.check_number_operands(e.operator, left, right)
                return left >= right
            case TokenType.LESS:
                self.check_number_operands(e.operator, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self.check_number_operands(e.operator, left, right)
                return left <= right
            case TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            case TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)
            case TokenType.MINUS:
                self.check_number_operands(e.operator, left, right)
                return left - right
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                self.error(
                    e.operator, 'Operands must be two numbers or two strings'
                )
            case TokenType.SLASH:
                self.check_number_operands(e.operator, left, right)
                if right == 0.0:
                    self.error(e.operator, 'Division by zero')
                return left / right
            case TokenType.STAR:
                self.check_number_operands(e.operator, left, right)
                return left * right

    def visit_variable_expr(self, e):
        return self.environment.get(e.name)

    def visit_assign_expr(self, e):
        value = self.evaluate(e.value)
        self.environment.assign(e.name, value)
        return value

    def is_equal(self, a, b):
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def visit_expression_stmt(self, s):
        self.evaluate(s.expression)

    def visit_print_stmt(self, s):
        print(self.stringify(self.evaluate(s.expression)))

    def visit_var_stmt(self, s):
        value = None
        if s.initializer is not None:
            value = self.evaluate(s.initializer)

        self.environment.define(s.name.lexeme, value)

    def visit_while_stmt(self, s):
        while self.is_truthy(self.evaluate(s.condition)):
            self.execute(s.body)

    def visit_block_stmt(self, s):
        self.execute_block(s.statements, Environment(self.environment))

    def visit_if_stmt(self, s):
        if self.is_truthy(self.evaluate(s.condition)):
            self.execute(s.then_branch)
        elif s.else_branch is not None:
            self.execute(s.else_branch)
