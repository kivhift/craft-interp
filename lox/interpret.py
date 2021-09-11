from .ast import expr
from .lex import TokenType
from .error import error

class Interpreter(expr.Visitor):
    def interpret(self, e):
        print(self.stringify(self.evaluate(e)))

    def stringify(self, x):
        if x is None:
            return 'nil'

        s = str(x)

        if isinstance(x, float) and s.endswith('.0'):
            return s[:-2]

        return s

    def error(self, token, msg):
        error(token.line, msg)

    def visit_literal_expr(self, e):
        return e.value

    def visit_grouping_expr(self, e):
        return self.evaluate(e.expression)

    def evaluate(self, e):
        return e.accept(self)

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

    def is_equal(self, a, b):
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b
