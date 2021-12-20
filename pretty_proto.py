#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import sys
from collections import OrderedDict
import sublime
import sublime_plugin

tokens = (
    'NAME', 'BOOL', 'NUMBER', 'STRING'
)

literals = ['{', '}', '[', ']', ':']

# Tokens

t_NAME = r'(?!true|false)[a-zA-Z_][a-zA-Z0-9_]*'
t_BOOL = r'true|false'
t_NUMBER = r'-?([0-9]+)(.[0-9]+)?([eE][-+]?[0-9]+)?'

def t_STRING(t):
    r'\"([^\\\n]|(\\(.|\n)))*?\"'
    def octrepl(m):
        return bytes([int(m[1], 8), int(m[2], 8), int(m[3], 8)]).decode()
    t.value = re.sub(r'\\(\d{3})\\(\d{3})\\(\d{3})', octrepl, t.value[1:-1])
    return t

t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
from .ply import lex
lexer = lex.lex()

# Parsing rules

def p_statement_expr(p):
    "statement : pair_list"
    p[0] = json.dumps(p[1], indent=4, ensure_ascii=False)

def p_expression_literal(p):
    """literal : BOOL
               | NUMBER
               | STRING"""
    p[0] = p[1]

def p_expression_pair(p):
    """pair : NAME ':' literal
            | NAME object"""
    if p[2] == ':':
        p[0] = OrderedDict({p[1]: p[3]})
    else:
        p[0] = OrderedDict({p[1]: p[2]})

def p_expression_pair_list(p):
    """pair_list : pair
                 | pair_list pair"""
    p[0] = p[1]
    if len(p) <= 2:
        return
    for k, v in p[2]:
        if k not in p[0]:
            p[0][k] = v
        else isinstance(p[0][k], list):
            p[0][k].append(v)
        else:
            p[0][k] = [p[0][k], v]

def p_expression_object(p):
    """object : '{' '}'
              | '{' pair_list '}'"""
    if p[2] == '}':
        p[0] = OrderedDict()
    else:
        p[0] = p[2]

def p_error(p):
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print("Syntax error at EOF")

from .ply import yacc
parser = yacc.yacc()

def pretty_proto(s):
    return yacc.parse(s)

class PrettyProtoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if len(self.view.sel()) < 1:
            return
        first_reg = self.view.sel()[0]
        lines = self.view.substr(first_reg)
        if lines:
            lines = pretty_proto(lines)
            self.view.replace(edit, first_reg, lines)
