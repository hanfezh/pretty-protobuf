#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
        def xint(s):
            is_hex = False
            if s[0] in ('x', 'X'):
                s = s[1:]
                is_hex = True
            return int(s, 16 if is_hex else 8)
        def byterepl(m):
            s = m.group(0).split('\\')[1:]
            b = bytearray()
            b.extend(map(xint, s))
            try:
                return b.decode()
            except UnicodeError as err:
                print(f'{m.group(0) = }\n{err = }')
                return m.group(0)
        # Transform octal '\nnn' or hex '\xnn' byte sequences to string object
        t.value = re.sub(r'((\\[0-7]{3})|(\\x[\da-fA-E]{2}))+', byterepl, t.value)
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
        """statement : pair_list
                     | object"""
        p[0] = p[1]

    def p_expression_literal(self, p):
        """literal : NAME
                   | BOOL
                   | NUMBER
                   | STRING"""
        # NAME support enum
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

class ProtoFormatter:
    def __init__(self, obj):
        self.__obj = obj
        self.__lst = []
        self.__spaces = 4
        self.__seperator = ' '

    def format(self):
        self.__format('', self.__obj)
        return '\n'.join(self.__lst)

    def __format(self, name, obj, times=0):
        if isinstance(obj, dict):
            spaces = self.__seperator * times
            self.__append(f'{spaces}{name} {{' if name else f'{spaces}{{')
            for k, v in obj.items():
                self.__format(k, v, times + self.__spaces)
            self.__append(f'{spaces}}}')
        elif isinstance(obj, list):
            for item in obj:
                self.__format(name, item, times)
        elif isinstance(obj, str):
            self.__append(f'{self.__seperator * times}{name}: {obj}')
        else:
            pass

    def __append(self, s):
        self.__lst.append(s)

class PrettyProtoCommand(sublime_plugin.TextCommand):
    parser = ProtoParser()

    def pretty_proto(self, s):
        obj = self.parser.parse(s)
        return ProtoFormatter(obj).format()

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
