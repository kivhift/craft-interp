from .ast import expr, stmt
from .error import error
from .lex import Token, TokenType

class Parser:
    MAX_ARGUMENTS = 255
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
        result = self.or_()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(result, expr.Variable):
                name = result.name
                return expr.Assign(name, value)

            self.error(equals, 'Invalid assignment target')

        return result

    def or_(self):
        result = self.and_()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_()
            result = expr.Logical(result, operator, right)

        return result

    def and_(self):
        result = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            result = expr.Logical(result, operator, right)

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

        return self.call()

    def call(self):
        result = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                result = self.finish_call(result)
            else:
                break

        return result

    def finish_call(self, callee):
        arguments = []
        push_arg = lambda x: arguments.append(x)

        if not self.check(TokenType.RIGHT_PAREN):
            push_arg(self.expression())
            while self.match(TokenType.COMMA):
                if len(arguments) >= self.MAX_ARGUMENTS:
                    self.error(self.peek()
                        , f"Can't have more than {self.MAX_ARGUMENTS} arguments")
                push_arg(self.expression())

        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments")

        return expr.Call(callee, paren, arguments)

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
            if self.match(TokenType.FUN):
                return self.function('function')
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()

    def statement(self):
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return stmt.Block(self.block())

        return self.expression_statement()

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses")

        body = self.statement()

        if increment is not None:
            body = stmt.Block([body, stmt.Expression(increment)])

        if condition is None:
            condition = expr.Literal(True)

        body = stmt.While(condition, body)

        if initializer is not None:
            body = stmt.Block([initializer, body])

        return body

    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return stmt.If(condition, then_branch, else_branch)

    def print_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value")
        return stmt.Print(value)

    def return_statement(self):
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value")

        return stmt.Return(keyword, value)

    def expression_statement(self):
        result = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return stmt.Expression(result)

    def function(self, kind):
        name = self.consume(TokenType.IDENTIFIER, f'Expect {kind} name')
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name")
        parameters = []
        push_param = lambda x: parameters.append(x)

        if not self.check(TokenType.RIGHT_PAREN):
            push_param(self.consume(TokenType.IDENTIFIER, 'Expect parameter name'))
            while self.match(TokenType.COMMA):
                if len(parameters) >= self.MAX_ARGUMENTS:
                    self.error(self.peek()
                        , f"Can't have more than {self.MAX_ARGUMENTS} parameters")
                push_param(self.consume(TokenType.IDENTIFIER, 'Expect parameter name'))

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters")
        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body")

        body = self.block()
        return stmt.Function(name, parameters, body)

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, 'Expect variable name')
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")

        return stmt.Var(name, initializer)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition")
        body = self.statement()

        return stmt.While(condition, body)

    def block(self):
        statements = []
        _s = statements.append

        while not (self.check(TokenType.RIGHT_BRACE) or self.is_at_end()):
            _s(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block")

        return statements
