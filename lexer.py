import re

import ply.lex

tokens = (
    # General
    'NUMBER', 'TENSOR',

    # In-Place Opertations
    'IADD', 'ILSHIFT'
)

# General
def t_NUMBER(t):
    r'\(-?\s*?\d+.?\d*\)'
    t.value = float(t.value[1:-1])
    return t


def t_TENSOR(t):
    r'\(\*\w+\)\[".*?"\]'
    name = re.search(r'\(\*\w+\)', t.value)[0][2:-1]
    idx = re.search(r'\[".*?"\]', t.value)[0][2:-2]

    t.value = (name, idx)
    return t

# In-Place Operators
t_IADD = r'\+='
t_ILSHIFT = r'<<='

t_ignore  = ' \t,*\n'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def get_tokens(data):
    lexer = ply.lex.lex()
    lexer.input(data)

    tokens = list(iter(lexer.token, None))
    return tokens

if __name__ == "__main__":
    data = r'''(*Kac)["ac"] <<= (-2.0) * (*Vhhpp)["klcd"] * (*Tpphh)["adkl"],'''
    print(get_tokens(data))