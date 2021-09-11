class LoxError(Exception):
    pass

def error(line, message, where=''):
    raise LoxError(f'[line {line}] Error{where}: {message}')
