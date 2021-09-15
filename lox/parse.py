from .ast import expr, stmt
from .error import error
from .lex import Token, TokenType

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        _s = statements.append
        while not self.is_at_end():
            _s(self.declaration())

        return statements

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
        return self.assignment()

    def assignment(self):
        result = self.equality()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(result, expr.Variable):
                name = result.name
                return expr.Assign(name, value)

            self.error(equals, 'Invalid assignment target')

        return result

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
            return expr.Literal(self.previous().literal)
        if self.match(TokenType.TRUE):
            return expr.Literal(True)
        if self.match(TokenType.FALSE):
            return expr.Literal(False)
        if self.match(TokenType.NIL):
            return expr.Literal(None)
        if self.match(TokenType.IDENTIFIER):
            return expr.Variable(self.previous())
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

    def declaration(self):
        try:
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()

    def statement(self):
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.LEFT_BRACE):
            return stmt.Block(self.block())

        return self.expression_statement()

    def print_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value")
        return stmt.Print(value)

    def expression_statement(self):
        result = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return stmt.Expression(result)

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, 'Expect variable name')
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")

        return stmt.Var(name, initializer)

    def block(self):
        statements = []
        _s = statements.append

        while not (self.check(TokenType.RIGHT_BRACE) or self.is_at_end()):
            _s(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block")

        return statements
