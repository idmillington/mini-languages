#!/usr/bin/env python

import inspect
import operator

class Scope(dict):
    """
    A dictionary that falls back to a parent. This can be used to
    manage scopes.
    """
    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, item):
        if super(Scope, self).__contains__(item):
            return super(Scope, self).__getitem__(item)
        elif self._parent:
            return self._parent[item]
        else:
            raise KeyError(repr(item))

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __delitem__(self, item):
        if super(Scope, self).__contains__(item):
            return super(Scope, self).__delitem__(item)
        elif self._parent:
            del self._parent[item]
        else:
            raise KeyError(repr(item))

    def __contains__(self, item):
        if super(Scope, self).__contains__(item):
            return True
        elif self._parent:
            return item in self._parent
        else:
            return False

class LispInterpreter(object):
    """
    A very basic interpreter for a tiny subdialect of a LISP-like
    language. Note that the language doesn't try to parse, we use
    Python lists as the sexpressions in the language.
    """
    def __init__(self):
        self._globals = {
            # Boolean aliases.
            '#t': True,
            '#nil': False,

            # Functions we have defined in this class.
            'setq': self._setq,
            'cond': self._cond,

            # Functions we can define inline.
            'car': lambda expr, ctx: expr[0][0],
            'cdr': lambda expr, ctx: expr[0][1:],
            'quote': lambda expr, ctx: expr[0],
            '+': lambda expr, ctx: sum(expr),
            '-': lambda expr, ctx: reduce(operator.sub, expr),
            '*': lambda expr, ctx: reduce(operator.mul, expr),
            '/': lambda expr, ctx: reduce(operator.div, expr),
            'equal?': lambda expr, ctx: expr[0] == expr[1]
        }
        self._lazy = ['cond', 'quote', 'setq']

    # Standard lisp apply/eval

    def _apply(self, fn, args, context):
        """
        Runs a function with a given set of arguments and a scope
        context.
        """
        # We can use actual functions or lambdas
        if inspect.isroutine(fn):
            return fn(args, context)

        # If the target is a function or method, run it right away
        elif inspect.isroutine(context.get(fn)):
            return context[fn](args, context)

        # Otherwise the target is a lambda expression, so we need to
        # eval it in a new scope (note that the scoping system in this
        # section means that our LISP is dynamically rather than
        # statically scoped).
        else:
            definition = context[fn]
            assert definition[0] == 'lambda'
            # Create a new sub-scope with our arguments in it, and
            # eval the lambda body.
            context = Scope(context)
            context.update(dict(zip(definition[1], args)))
            return self._eval(definition[2], context)

    def _eval(self, sexpression, context):
        """
        Interprets an s-expression, returning its value.
        """
        if type(sexpression) != list:
            # If we can find it in the context, it is probably a
            # string, otherwise use the value unaltered.
            return context.get(sexpression, sexpression)
        else:
            fn = sexpression[0]
            args = sexpression[1:]

            # As long as we're not lazy, evaluate the arguments to the
            # function.
            if fn not in self._lazy:
                args = map(lambda n: self._eval(n, context), args)

            return self._apply(fn, args, context)

    # Functions that are callable from the language.

    def _setq(self, sexpression, context):
        context[sexpression[0]] = sexpression[1]
        return sexpression[1]

    def _cond(self, sexpression, context):
        for condition, effect in sexpression:
            if self._eval(condition, context):
                return self._eval(effect, context)
        else:
            return False

def main():
    l = LispInterpreter()

    context = Scope(l._globals)
    l._eval(
        ['setq', 'factorial',
            ['lambda', ['x'],
                ['cond',
                    [['equal?', 'x', 0], 1],
                    [True, ['*', 'x', ['factorial', ['-', 'x', 1]]]]
                ]
            ]
        ], context)
    print l._eval(
        ['factorial', 5],
        context
        )

if __name__ == '__main__':
    main()












