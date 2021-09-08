import argparse
import enum
import mmap
import sys

from dataclasses import dataclass

@enum.unique
class CodePoint(enum.IntEnum):
    LEFT_PAREN = ord('(')
    RIGHT_PAREN = ord(')')
    LEFT_BRACE = ord('{')
    RIGHT_BRACE = ord('}')
    COMMA = ord(',')
    DOT = ord('.')
    MINUS = ord('-')
    PLUS = ord('+')
    SEMICOLON = ord(';')
    SLASH = ord('/')
    STAR = ord('*')
    BANG = ord('!')
    EQUAL = ord('=')
    LESS = ord('<')
    GREATER = ord('>')
    NEWLINE = ord('\n')
    RETURN = ord('\r')
    SPACE = ord(' ')
    TAB = ord('\t')
    NULL = ord('\0')
    DOUBLE_QUOTE = ord('"')
    ZERO = ord('0')
    NINE = ord('9')
    UPPER_A = ord('A')
    UPPER_Z = ord('Z')
    LOWER_A = ord('a')
    LOWER_Z = ord('z')
    UNDERSCORE = ord('_')

TokenType = enum.Enum('TokenType',
    '''
    LEFT_PAREN RIGHT_PAREN LEFT_BRACE RIGHT_BRACE
    COMMA DOT MINUS PLUS SEMICOLON SLASH STAR

    BANG BANG_EQUAL EQUAL EQUAL_EQUAL
    GREATER GREATER_EQUAL LESS LESS_EQUAL

    IDENTIFIER STRING NUMBER

    AND CLASS ELSE FALSE FOR FUN IF NIL OR PRINT
    RETURN SUPER THIS TRUE VAR WHILE

    EOF
    '''
)

keywords = { k.lower().encode(): TokenType[k] for k in '''
    AND CLASS ELSE FALSE FOR FUN IF NIL OR PRINT
    RETURN SUPER THIS TRUE VAR WHILE
'''.split()}

@dataclass
class Token:
    type: TokenType
    start: int
    length: int
    lexeme: object
    line: int

class LoxError(Exception):
    pass

def error(line, message, where=''):
    raise LoxError(f'[line {line}] Error{where}: {message}')

class Lexer:
    def __init__(self, source):
        self._start = 0
        self._current = 0
        self._line = 1
        self._tokens = None

        self.source = source

    def tokens(self):
        if self._tokens is None:
            self._tokens = []
            while not self._at_end():
                self._start = self._current
                self._scan_token()
            self._tokens.append(Token(TokenType.EOF, -1, -1, None, self._line))

        for token in self._tokens:
            yield token

    def _at_end(self):
        return self._current >= len(self.source)

    def _advance(self):
        ch = self.source[self._current]
        self._current += 1
        return ch

    def _add_token(self, type, lexeme=None):
        self._tokens.append(
            Token(type, self._start, self._current - self._start, lexeme, self._line)
        )

    def _match(self, expected):
        if self._at_end():
            return False

        if self.source[self._current] != expected:
            return False

        self._current += 1
        return True

    def _peek(self):
        if self._at_end():
            return CodePoint.NULL

        return self.source[self._current]

    def _peek_next(self):
        if (self._current + 1) >= len(self.source):
            return 0

        return self.source[self._current + 1]

    def _string(self):
        while CodePoint.DOUBLE_QUOTE != (p := self._peek()) and not self._at_end():
            if CodePoint.NEWLINE == p:
                self._line += 1
            self._advance()

        if self._at_end():
            error(self._line, 'Unterminated string')

        self._advance()

        self._add_token(
            TokenType.STRING , self.source[self._start + 1 : self._current - 1]
        )

    def _is_digit(self, ch):
        return CodePoint.ZERO <= ch <= CodePoint.NINE

    def _is_alpha(self, ch):
        return (
            (CodePoint.LOWER_A <= ch <= CodePoint.LOWER_Z)
            or (CodePoint.UPPER_A <= ch <= CodePoint.UPPER_Z)
            or (CodePoint.UNDERSCORE == ch)
        )

    def _is_alphanumeric(self, ch):
        return self._is_alpha(ch) or self._is_digit(ch)

    def _number(self):
        while self._is_digit(self._peek()):
            self._advance()

        if CodePoint.DOT == self._peek() and self._is_digit(self._peek_next()):
            self._advance()
            while self._is_digit(self._peek()):
                self._advance()

        self._add_token(
            TokenType.NUMBER, float(self.source[self._start : self._current])
        )

    def _comment(self):
        while self._peek() != CodePoint.NEWLINE and not self._at_end():
            self._advance()

    def _identifier(self):
        while self._is_alphanumeric(self._peek()):
            self._advance()

        self._add_token(
            keywords.get(self.source[self._start : self._current])
            or TokenType.IDENTIFIER
        )

    def _scan_token(self):
        match ch := self._advance():
            case CodePoint.LEFT_PAREN:
                self._add_token(TokenType.LEFT_PAREN)
            case CodePoint.RIGHT_PAREN:
                self._add_token(TokenType.RIGHT_PAREN)
            case CodePoint.LEFT_BRACE:
                self._add_token(TokenType.LEFT_BRACE)
            case CodePoint.RIGHT_BRACE:
                self._add_token(TokenType.RIGHT_BRACE)
            case CodePoint.COMMA:
                self._add_token(TokenType.COMMA)
            case CodePoint.DOT:
                self._add_token(TokenType.DOT)
            case CodePoint.MINUS:
                self._add_token(TokenType.MINUS)
            case CodePoint.PLUS:
                self._add_token(TokenType.PLUS)
            case CodePoint.SEMICOLON:
                self._add_token(TokenType.SEMICOLON)
            case CodePoint.STAR:
                self._add_token(TokenType.STAR)
            case CodePoint.BANG:
                self._add_token(TokenType.BANG_EQUAL
                    if self._match(CodePoint.EQUAL) else TokenType.BANG)
            case CodePoint.EQUAL:
                self._add_token(TokenType.EQUAL_EQUAL
                    if self._match(CodePoint.EQUAL) else TokenType.EQUAL)
            case CodePoint.LESS:
                self._add_token(TokenType.LESS_EQUAL
                    if self._match(CodePoint.EQUAL) else TokenType.LESS)
            case CodePoint.GREATER:
                self._add_token(TokenType.GREATER_EQUAL
                    if self._match(CodePoint.EQUAL) else TokenType.GREATER)
            case CodePoint.SLASH:
                if self._match(CodePoint.SLASH):
                    self._comment()
                else:
                    self._add_token(TokenType.SLASH)
            case CodePoint.SPACE | CodePoint.RETURN | CodePoint.TAB:
                pass
            case CodePoint.NEWLINE:
                self._line += 1
            case CodePoint.DOUBLE_QUOTE:
                self._string()
            case _:
                if self._is_digit(ch):
                    self._number()
                elif self._is_alpha(ch):
                    self._identifier()
                else:
                    error(self._line, f'Unexpected character: "{chr(ch)}"')

def run(buffer):
    lexer = Lexer(buffer)

    for token in lexer.tokens():
        print(token)

def run_REPL():
    try:
        while line := input('lox> '):
            try:
                run(line.encode())
            except LoxError as e:
                print(e, file=sys.stderr)
    except EOFError:
        print()

def run_script(script):
    with (
        open(script) as inf,
        mmap.mmap(inf.fileno(), 0, access=mmap.ACCESS_READ) as mm
    ):
        try:
            run(mm)
        except LoxError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('script', nargs='?')
    args = parser.parse_args(args or sys.argv[1:])

    if args.script is None:
        run_REPL()
    else:
        run_script(args.script)

if '__main__' == __name__:
    main()
