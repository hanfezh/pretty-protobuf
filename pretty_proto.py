#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
from .ply import lex, yacc
from collections import OrderedDict
import sublime
import sublime_plugin

class Parser:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.debug = kw.get('debug', 0)
        self.names = {}
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                1] + "_" + self.__class__.__name__
        except:
            modname = "parser" + "_" + self.__class__.__name__
        self.debugfile = modname + ".dbg"
        # print self.debugfile

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile)

    def parse(self, s):
        return yacc.parse(s)

class ProtoParser(Parser):
    tokens = (
        'NAME', 'BOOL', 'NUMBER', 'STRING'
    )

    literals = ['{', '}', '[', ']', ':']

    # Tokens

    t_NAME = r'(?!true|false)[a-zA-Z_][a-zA-Z0-9_]*'
    t_BOOL = r'true|false'
    t_NUMBER = r'-?([0-9]+)(.[0-9]+)?([eE][-+]?[0-9]+)?'

    def t_STRING(self, t):
        r'\"([^\\\n]|(\\(.|\n)))*?\"'
        def octrepl(m):
            return bytes([int(m[1], 8), int(m[2], 8), int(m[3], 8)]).decode()
        t.value = re.sub(r'\\(\d{3})\\(\d{3})\\(\d{3})', octrepl, t.value[1:-1])
        return t

    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Parsing rules

    def p_statement_expr(self, p):
        "statement : pair_list"
        p[0] = json.dumps(p[1], indent=4, ensure_ascii=False)

    def p_expression_literal(self, p):
        """literal : BOOL
                   | NUMBER
                   | STRING"""
        p[0] = p[1]

    def p_expression_pair(self, p):
        """pair : NAME ':' literal
                | NAME object"""
        if p[2] == ':':
            p[0] = OrderedDict({p[1]: p[3]})
        else:
            p[0] = OrderedDict({p[1]: p[2]})

    def p_expression_pair_list(self, p):
        """pair_list : pair
                     | pair_list pair"""
        p[0] = p[1]
        if len(p) <= 2:
            return
        for k, v in p[2].items():
            if k not in p[0]:
                p[0][k] = v
            elif isinstance(p[0][k], list):
                p[0][k].append(v)
            else:
                p[0][k] = [p[0][k], v]

    def p_expression_object(self, p):
        """object : '{' '}'
                  | '{' pair_list '}'"""
        if p[2] == '}':
            p[0] = OrderedDict()
        else:
            p[0] = p[2]

    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


class PrettyProtoCommand(sublime_plugin.TextCommand):
    parser = ProtoParser()

    def pretty_proto(self, s):
        return parser.parse(s)

    def run(self, edit):
        if len(self.view.sel()) < 1:
            return
        first_reg = self.view.sel()[0]
        if first_reg.empty():
            first_reg = sublime.Region(0, self.view.size())
        lines = self.view.substr(first_reg)
        if lines:
            lines = self.pretty_proto(lines)
            self.view.replace(edit, first_reg, lines)
