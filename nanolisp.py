import inspect
import operator

class LispInterpreter(object):
    def __init__(self):
        self._globals = {
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
        
    def _is_primitive(self, name):
        return inspect.isroutine(self._globals.get(name))
        
    def _is_lazy(self, name): 
        return name in ['cond', 'quote', 'setq'] \
            if self._is_primitive(name) else \
            self._globals.get(name, [None]) == 'macro'
    
    def _is_atom(self, name):
        return type(name) != list and type(name) != dict

    # Standard lisp apply/eval
    
    def _apply(self, fn, args, context):
        if self._is_primitive(fn): 
            return self._globals[fn](args, context)
        else:
            context = dict(zip(self._globals[fn][1], args))
            return self._eval(self._globals[fn][2], context)

    def _eval(self, expression, context):
        if self._is_atom(expression):
            if expression in context:
                return context[expression]
            else:
                return expression
        else:
            fn = expression[0]
            args = expression[1]

            # Evaluate the arguments to the function
            if not self._is_lazy(fn):
                args = map(lambda n: self._eval(n, context), args)

            return self._apply(fn, args, context)

    # Functions that are callable from the language.
        
    def _setq(self, expression, context):
        self._globals[expression[0]] = expression[1]
        return expression[1]
                    
    def _cond(self, expression, context):
        for condition, effect in expression:
            if self._eval(condition, context):
                return self._eval(effect, context)
        else:
            return False

def main():
    l = LispInterpreter()
    print l._eval(
        ['setq', 'factorial', 
            ['lambda', ['x'], 
                ['cond', [['equal?', 'x', 0], 1],
                    [True, ['*', 'x', ['factorial', ['-', 'x', 1]]]]
                ]
            ]
        ], l._globals)
    
if __name__ == '__main__':
    main()












