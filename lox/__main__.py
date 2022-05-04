import argparse
import mmap
import os
import sys

from .error import LoxError
from .lex import Lexer
from .parse import Parser
from .ast.printer import ASTPrinter
from .interpret import Interpreter
from .resolve import Resolver

def run(interp, buffer):
    lexer = Lexer(buffer)
    parser = Parser(list(lexer.tokens()))
    statements = parser.parse()
    resolver = Resolver(interp)
    resolver.resolve(statements)
    interp.interpret(statements)

def run_REPL(interp):
    try:
        while line := input('lox> '):
            try:
                run(interp, line.encode())
            except LoxError as e:
                print(e, file=sys.stderr)
    except EOFError:
        print()

def run_script(interp, script):
    with (
        open(script) as inf,
        mmap.mmap(inf.fileno(), 0, access=mmap.ACCESS_READ) as mm
    ):
        try:
            run(interp, mm)
        except LoxError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('script', nargs='?')
args = parser.parse_args()

i = Interpreter()

if args.script is None:
    run_REPL(i)
else:
    if not os.path.exists(args.script):
        raise SystemExit(f'File does not exist: {args.script}')
    if 0 == os.path.getsize(args.script):
        sys.exit(0)
    run_script(i, args.script)
