#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from .ply import lex, yacc
from collections import OrderedDict
import sublime

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
        'BOOL', 'NAME', 'FLOAT', 'INTEGER', 'STRING'
    )

    literals = ['{', '}', '[', ']', ':']

    # Tokens

    t_BOOL = r'true|false'
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_FLOAT = r'((\d+)(\.\d+)(e(\+|-)?(\d+))?)|((\d+)e(\+|-)?(\d+))([lL]|[fF])'
    t_INTEGER = r'-?([0-9]+)(\.[0-9]+)?([eE][-+]?[0-9]+)?'

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
        t.value = re.sub(r'((\\[0-7]{3})|(\\x[\da-fA-F]{2}))+', byterepl, t.value)
        return t

    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])

    # Parsing rules

    def p_statement_expr(self, p):
        """statement : pair_list
                     | object"""
        p[0] = p[1]

    def p_expression_key(self, p):
        """key : NAME
               | INTEGER"""
        p[0] = p[1]

    def p_expression_literal(self, p):
        """literal : NAME
                   | BOOL
                   | FLOAT
                   | INTEGER
                   | STRING"""
        # NAME support enum
        p[0] = p[1]

    def p_expression_pair(self, p):
        """pair : key ':' literal
                | key object"""
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

class ProtoSettings:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.__settings = sublime.load_settings('Pretty Protobuf.sublime-settings')
        self.__spaces = self.__settings.get('indent', 4)
        self.__sort_keys = self.__settings.get('sort_keys', False)
        self.__use_entire_file = self.__settings.get('use_entire_file_if_no_selection', True)

    @property
    def spaces(self):
        return self.__spaces

    @property
    def sort_keys(self):
        return self.__sort_keys

    @property
    def use_entire_file(self):
        return self.__use_entire_file

class DictFormatter:
    def __init__(self, obj):
        self.__settings = ProtoSettings()
        self.__obj = obj
        self.__lst = []
        self.__seperator = ' '

    def format(self):
        self.__format('', self.__obj)
        return '\n'.join(self.__lst)

    def __format(self, name, obj, times=0):
        if isinstance(obj, dict):
            spaces = self.__seperator * times
            self.__append(f'{spaces}{name} {{' if name else f'{spaces}{{')
            if self.__settings.sort_keys:
                obj = dict(sorted(obj.items(), key=lambda x: x[0]))
            for k, v in obj.items():
                self.__format(k, v, times + self.__settings.spaces)
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

class ProtoFormatter:
    parser = ProtoParser()

    def __init__(self, debug_str):
        # Keep original debug string
        self.__debug_string = debug_str

    def format(self):
        obj = self.parser.parse(self.__debug_string)
        return DictFormatter(obj).format()
