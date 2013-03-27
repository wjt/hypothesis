import sys
from parsley import makeGrammar
from collections import namedtuple
from inspect import currentframe
from pprint import PrettyPrinter


letters = ''.join(map(chr, range(ord('a'), ord('a') + 26)))
numbers = ''.join(map(str,range(0,10))) 
extra_chars = ' '
alphanumerics = numbers + letters + letters.upper()  + extra_chars

class IDGenerator(object):
    def __init__(self):
        self.data = {}

    def gen(self, x):
        return self.data.setdefault(x, len(self.data))

    def seen(self, x):
        return x in self.data

class Expression(object):
    def valid_starts(self):
        if hasattr(self, '_valid_starts'):
            return self._valid_starts

        it = set()
        self.add_valid_starts(it)
        it = frozenset(it)
        self._valid_starts = it
        return it

    def __repr__(self):
        return "Expression(%s)" % self.exp()

    def __eq__(self, that):
        return self.cexp() == that.cexp()

    def __neq__(self, that):
        return self.cexp() != that.cexp()

    def __hash__(self):
        return hash(self.cexp())

    def cexp(self):
        if not hasattr(self, '_cexp'):
            self._cexp = self.exp()
        return self._cexp

    def qexp(self):
        e = self.exp()
        return "(%s)" % e

    def matches_empty(self):
        return False

    def differentiate(self, d):
        if d not in self.valid_starts(): return Nothing()
        else: return self._differentiate(d)

    def derivatives(self):
        for c in self.valid_starts():
            yield c, self.differentiate(c)

    def compile(self):
        pending = [self]

        states = {} 

        idg = IDGenerator()
        while pending:
            x = pending.pop()
            idg.gen(x)
            if x in states:
                continue

            s = {}
            states[x] = s
            for c, d in x.derivatives():
                s[c] = d
                pending.append(d)
                
        simple_states = {}

        for source, transitions in states.items():
            source_id = idg.gen(source)
            s = {}
            if source.matches_empty():
                s["end"] = "ok"

            simple_states[source_id] = s
            for c, target in transitions.items():
                print source, c, target
                s[c] = idg.gen(target)

        return [simple_states[i] for i in xrange(0, len(simple_states))]

class Token(Expression, namedtuple("Token", ("token"))):
    def add_valid_starts(self, it):
        it.add(self.token[0])

    def exp(self):
        return self.token

    def _differentiate(self, c):
        t = self.token[1:]
        if t:
            return Token(t)
        else:
            return Empty()

class Cat(Expression, namedtuple("Cat", "children")):
    def exp(self):
        return ''.join((x.qexp() for x in self.children))

    def add_valid_starts(self, it):
        self.children[0].add_valid_starts(it)
    
    def _differentiate(self, c):
        newchildren = list(self.children)
        newchildren[0] = newchildren[0]._differentiate(c)
        return cat(newchildren)

class Empty(Expression):
    def exp(self):
        return '\\e'

    def add_valid_starts(self, it):
        pass

    def matches_empty(self):
        return True

    def _differentiate(self, c):
        return Nothing()

class Nothing(Expression):
    def exp(self):
        return '\\n'

    def add_valid_starts(self, it):
        pass

    def matches_empty(self):
        return False

    def _differentiate(self, c):
        return Nothing()

class Maybe(Expression, namedtuple("Maybe", "child")):
    def exp(self):
        return self.child.qexp() + "?"

    def add_valid_starts(self, it):
        self.child.add_valid_starts(it)

    def matches_empty(self):
        return True

    def _differentiate(self, c):
        return self.child.differentiate(c)

class Star(Expression, namedtuple("Star", "child")):
    def exp(self):
        return self.child.qexp() + "*"

    def add_valid_starts(self, it):
        self.child.add_valid_starts(it)
    
    def matches_empty(self):
        return True

    def _differentiate(self, c):
        return cat([self.child.differentiate(c), self])

class Plus(Expression, namedtuple("Plus", "child")):
    def _differentiate(self, c):
        return Star(self.child).differentiate(c)

    def exp(self):
        return self.child.qexp() + "+"

    def add_valid_starts(self, it):
        self.child.add_valid_starts(it)

class Alt(Expression, namedtuple("Alt", ("left", "right"))):
    def exp(self):
        return self.left.qexp() + "|" + self.right.qexp()

    def add_valid_starts(self, it):
        self.left.add_valid_starts(it)
        self.right.add_valid_starts(it)

    def _differentiate(self, c):
        return alt(self.left.differentiate(c), self.right.differentiate(c))

def maybe_suffix(x, suffix):
    if suffix:
        if suffix == '*':
            f = Star
        elif suffix == '+':
            f = Plus
        elif suffix == '?':
            f = Maybe
        else:
            raise ValueError("Invalid suffix %s" % suffix)
        return f(x)
    return x
        
def cat(xs):
    if not isinstance(xs, list):
        raise ValueError("Not a list %s" % str(xs))
    if any((isinstance(x, Nothing) for x in xs)):
        return Nothing()
    xs = [x for x in xs if not isinstance(x, Empty)]
    if not xs:
        return Empty()
    elif len(xs) == 1:
        return xs[0]
    else:
        return Cat(xs)

def expr(token, rest):
    return [token] + rest

def exprs(xs, alt):
    xs = cat(xs)
    
    if alt:
        return Alt(xs, alt)

    return xs

def alt(xs, alt):
    if isinstance(xs, Nothing): return alt
    if isinstance(alt, Nothing): return xs
    return Alt(xs, alt)

regexpGrammar = """
    regularchars = anything:x ?(x in '%s') -> x
    token = regularchars+:ds -> Token(''.join(ds))
    alt = '|' exps:x -> x
    bracketed = '(' exps:xs ')' -> xs
    suffix = ('*'|'+'|'?'):s -> s
    exp = (bracketed | token):x suffix?:s -> maybe_suffix(x, s)
    exps = exp+:x alt?:al suffix?:s -> maybe_suffix(exprs(x,al), s)
    """ % alphanumerics

RegExp = makeGrammar(regexpGrammar, currentframe().f_locals)

if __name__ == '__main__':
    while True:
        line = sys.stdin.readline()
        if not line: break
        e = RegExp(line.strip()).exps()
        print e
        print e.compile()

