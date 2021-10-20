#!/usr/bin/env python3

from pathlib import Path

def define_AST(base, types):
    o = []
    a = o.append
    a('# Automatically generated')
    a('from abc import ABC, abstractmethod')
    a(f'class {base}(ABC):')
    a('    @abstractmethod')
    a('    def accept(self, visitor): pass')

    names = []
    add_name = names.append
    tag = base.lower()
    for line in (x.strip() for x in types.strip().splitlines()):
        name, *fields = line.split()
        add_name(name.lower())
        a(f'class {name}({base}):')
        a(f'    def __init__(self, {", ".join(fields)}):')
        for field in fields:
            a(f'        self.{field} = {field}')
        a('    def accept(self, visitor):')
        a(f'        return visitor.visit_{names[-1]}_{tag}(self)')

    a(f'class Visitor(ABC):')
    for name in names:
        a('    @abstractmethod')
        a(f'    def visit_{name}_{tag}(self, {tag[0]}): pass')

    return '\n'.join(o)

basedir = Path('lox/ast')
if not basedir.exists():
    raise SystemExit(f'Could not find ast package directory: {basedir}')

ASTs = dict(
    Expr = '''
        Assign name value
        Binary left operator right
        Grouping expression
        Literal value
        Logical left operator right
        Unary operator right
        Variable name
    '''
    , Stmt = '''
        Block statements
        Expression expression
        If condition then_branch else_branch
        Print expression
        Var name initializer
        While condition body
    '''
)

for key in ASTs:
    with (basedir / f'{key.lower()}.py').open(mode='w', encoding='utf-8') as out:
        out.write(define_AST(key, ASTs[key]))
        out.write('\n')
