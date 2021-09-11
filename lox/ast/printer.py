from . import expr

class ASTPrinter(expr.Visitor):
    def print(self, x):
        return x.accept(self)
    def visit_binary_expr(self, x):
        return self.parenthesize(x.operator.lexeme, x.left, x.right)
    def visit_grouping_expr(self, x):
        return self.parenthesize('group', x.expression)
    def visit_literal_expr(self, x):
        if x.value is None:
            return 'nil'
        return str(x.value)
    def visit_unary_expr(self, x):
        return self.parenthesize(x.operator.lexeme, x.right)
    def parenthesize(self, name, *exprs):
        r = [f'({name}']
        a = r.append
        for x in exprs:
            a(' ')
            a(x.accept(self))
        a(')')
        return ''.join(r)
