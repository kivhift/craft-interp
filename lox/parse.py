from .ast import expr
from .error import error
from .lex import Token, TokenType

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        return self.expression()

    def previous(self):
        return self.tokens[self.current - 1]

    def peek(self):
        return self.tokens[self.current]

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def check(self, type):
        if self.is_at_end():
            return False

        return self.peek().type == type

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True

        return False

    def expression(self):
        return self.equality()

    def equality(self):
        result = self.comparison()
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            result = expr.Binary(result, operator, right)

        return result

    def comparison(self):
        result = self.term()
        while self.match(
            TokenType.GREATER, TokenType.GREATER_EQUAL,
            TokenType.LESS, TokenType.LESS_EQUAL
        ):
            operator = self.previous()
            right = self.term()
            result = expr.Binary(result, operator, right)

        return result

    def term(self):
        result = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            result = expr.Binary(result, operator, right)

        return result

    def factor(self):
        result = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            result = expr.Binary(result, operator, right)

        return result

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return expr.Unary(operator, right)

        return self.primary()

    def primary(self):
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(self.previous().lexeme)
        if self.match(TokenType.TRUE):
            return expr.Literal(True)
        if self.match(TokenType.FALSE):
            return expr.Literal(False)
        if self.match(TokenType.NIL):
            return expr.Literal(None)
        if self.match(TokenType.LEFT_PAREN):
            result = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression")
            return expr.Grouping(result)

        self.error(self.peek(), 'Expect expression')

    def consume(self, type, message):
        if self.check(type):
            return self.advance()

        self.error(self.peek(), message)

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            if self.peek().type in (
                TokenType.CLASS, TokenType.FOR, TokenType.FUN, TokenType.IF,
                TokenType.PRINT, TokenType.RETURN, TokenType.VAR, TokenType.WHILE
            ):
                return

            self.advance()

    def error(self, token, message):
        error(token.line, message
            , ' at end' if token.type == TokenType.EOF else f" '{token.lexeme}'")
