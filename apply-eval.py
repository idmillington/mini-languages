#!/usr/bin/env python

import inspect
import operator

class Environment(dict):
    """
    A dictionary that falls back to a parent. This can be used to
    manage binding environments.
    """
    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, item):
        if super(Environment, self).__contains__(item):
            return super(Environment, self).__getitem__(item)
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
        if super(Environment, self).__contains__(item):
            return super(Environment, self).__delitem__(item)
        elif self._parent:
            del self._parent[item]
        else:
            raise KeyError(repr(item))

    def __contains__(self, item):
        if super(Environment, self).__contains__(item):
            return True
        elif self._parent:
            return item in self._parent
        else:
            return False

class ApplyEvalInterpreter(object):
    """
    A very basic interpreter for a tiny subdialect of a LISP-like
    language. Note that the language doesn't try to parse, we use
    Python lists as the sexpressions in the language.
    """
    def __init__(self):
        self._builtins = {
            # Boolean aliases.
            '#t': True,
            '#nil': False,

            # Functions we have defined in this class.
            'set': self._set,
            'setq': self._setq,
            'cond': self._cond,
            'lambda': self._lambda,

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
        
        # These functions don't evaluate their operands immediately. Note that
        # this is an all or nothing thing, and the individual functions must
        # evaluate anything that wasn't already evaluated.
        self._lazy = ['lambda', 'cond', 'quote', 'setq']
        
    def make_global_environment(self):
        """
        Create the global environment, with references to the builtin set
        and itself.
        """
        globals_ = Environment(self._builtins)
        globals_['__builtins__'] = self._builtins
        globals_['__globals__'] = globals_
        return globals_
        
    def eval(self, sexpression, env=None):
        """
        Top level interpreter, returns the value associated with the given 
        expression, in the given environment (or a new default global, if
        none is given).
        """
        if env is None:
            env = self.make_global_environment
        return self._eval(sexpression, env)

    # Standard lisp-like apply/eval

    def _apply(self, fn, args, env):
        """
        Runs a function with a given set of arguments and an environment.
        """
        # We can use actual functions or lambdas
        if inspect.isroutine(fn):
            return fn(args, env)

        # If the target is a function or method, run it right away
        elif inspect.isroutine(env.get(fn)):
            return env[fn](args, env)

        # Otherwise the target is a lambda expression, so we need to
        # eval it in a new Environment. This implements lexical scoping.
        else:
            definition = env[fn]
            assert definition[0] == 'lambda'
            # Create a new environment from the stored one.
            env = Environment(definition[1])
            # Map the bindings of the variables
            env.update(dict(zip(definition[2], args)))
            return self._eval(definition[3], env)

    def _eval(self, sexpression, env):
        """
        Interprets an s-expression, returning its value.
        """
        if type(sexpression) != list:
            # If we can find it in the environment, it is probably a
            # primitive type, otherwise use the value unaltered.
            return env.get(sexpression, sexpression)
        else:
            fn = sexpression[0]
            args = sexpression[1:]

            # As long as we're not lazy, evaluate the arguments to the
            # function.
            if fn not in self._lazy:
                args = map(lambda n: self._eval(n, env), args)

            return self._apply(fn, args, env)

    # Functions that are callable from the language.
    
    def _lambda(self, sexpression, env):
        """
        Stores a lambda with its environment, ready for later application.
        """
        return ('lambda', env, sexpression[0], sexpression[1])

    def _set(self, sexpression, env):
        env[sexpression[0]] = sexpression[1]
        return sexpression[1]

    def _setq(self, sexpression, env):
        # Because setq is lazy, neither argument is evaled, so we need to 
        # manually eval the latter one.
        env[sexpression[0]] = self.eval(sexpression[1], env)
        return sexpression[1]

    def _cond(self, sexpression, env):
        for condition, effect in sexpression:
            if self._eval(condition, env):
                return self._eval(effect, env)
        else:
            return False

def main():
    l = ApplyEvalInterpreter()
    env = l.make_global_environment()
    l.eval(
        ['setq', 'factorial',
            ['lambda', ['x'],
                ['cond',
                    [['equal?', 'x', 0], 1],
                    [True, ['*', 'x', ['factorial', ['-', 'x', 1]]]]
                ]
            ]
        ], env)
    print l.eval(
        ['factorial', 5],
        env
        )

if __name__ == '__main__':
    main()












