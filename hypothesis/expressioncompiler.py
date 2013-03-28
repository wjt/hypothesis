import sys
from parsley import makeGrammar
from collections import namedtuple
from inspect import currentframe
from functools import wraps
import random

class IDGenerator(object):
    def __init__(self):
        self.data = {}

    def gen(self, x):
        return self.data.setdefault(x, len(self.data))

    def seen(self, x):
        return x in self.data

State = namedtuple("State", ("terminal", "transitions"))

class Expression(object):
    @classmethod
    def parse(cls, expression):
        return RegExp(expression).exps()

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

    def matches(self, string):
        s = self.dfa()[0]
        i = 0
        while i < len(string):
            try:
                s = self.dfa()[s.transitions[string[i]]]
                i += 1
            except KeyError:
                return False
        return s.terminal

    def matching_substrings(self, string):
        s = self.dfa()[0]
        i = 0
        while i < len(string):
            try:
                s = self.dfa()[s.transitions[string[i]]]
                i += 1
                if s.terminal:
                    yield string[0:i]
            except KeyError:
                return


    def nth_string(self, n):
        if n < 0:
            raise IndexError("n cannot be negative: n=%s" % n)
        if not self.is_language_infinite() and n >= self.language_size():
            raise IndexError("n cannot be > language size %s: n=%s" % (self.language_size(), n))
        
        for l, m in self.strings_at_length():
            if m > n: break
            n -= m

        cs = []

        state_index = 0

        while len(cs) < l:
            state = self.dfa()[state_index]

            for c, ns in sorted(state.transitions.items(),key = lambda x:x[0]):
                in_bucket = self.strings_from_state(ns, l - len(cs) - 1)
                if in_bucket <= n:
                    n -= in_bucket
                else:
                    state_index = ns
                    cs.append(c)
                    break
            
        return ''.join(cs)
        

    def strings_from_state(self, state_index, length):
        if not hasattr(self, 'string_counts_from_states'):
            self.string_counts_from_states = [{} for _ in xrange(len(self.dfa()))]
        if length < 0:
            return ValueError("Can't have a negative length: %s" % length)
        table = self.string_counts_from_states[state_index]
        if length in table:
            return table[length]
        state = self.dfa()[state_index]
        if length == 0:
            result = 1 if state.terminal else 0
        else:
            result = sum((
                self.strings_from_state(si, length - 1)
                for c, si in state.transitions.items()))
        table[length] = result
        return result 

    def is_language_infinite(self):
        if not hasattr(self, '_is_language_infinite'):
            stack = []
            def seek_cycle_from(i):
                if i in stack: return True
                stack.append(i)
                for j in self.dfa()[i].transitions.values():
                    if seek_cycle_from(j): return True
                stack.pop()
                return False
            self._is_language_infinite = seek_cycle_from(0)

        return self._is_language_infinite

    def language_size(self):
        if not hasattr(self, '_language_size'):
            def lsfrom(i):
                state = self.dfa()[i]
                size = sum(lsfrom(j) for j in state.transitions.values())
                if state.terminal: size += 1 
                return size
            self._language_size  = lsfrom(0)
        return self._language_size

    def strings_at_length(self):
        i = 0
        while True:
            yield i, self.strings_from_state(0, i)
            i += 1

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

    def dfa(self):
        if not hasattr(self, '_dfa'):
            self._dfa = self.compile()
        return self._dfa

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
            simple_states[source_id] = State(source.matches_empty(), s)
            for c, target in transitions.items():
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

class CharClass(Expression):
    def __init__(self, chars):
        self.chars = set()

        i = 0
        while i < len(chars):
            j = i + 1
            if j < len(chars) and chars[j][0] == '-':
                for c in xrange(ord(chars[i]), ord(chars[j][1])+1):
                    self.chars.add(chr(c))
                i += 2
            else:
                self.chars.add(chars[i])
                i += 1

    def add_valid_starts(self, it):
        for t in self.chars:
            it.add(t)

    def exp(self):
        return "[%s]" % self.chars

    def _differentiate(self, c):
        if c in self.chars:
            return Empty()
        else:
            return Nothing()

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
        return ''

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
    def matches_empty(self):
        return self.left.matches_empty() or self.right.matches_empty()

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


letters = ''.join(map(chr, range(ord('a'), ord('a') + 26)))
numbers = ''.join(map(str,range(0,10))) 
extra_chars = ' '
alphanumerics = numbers + letters + letters.upper()  + extra_chars
specialchars = '|+*?\\'

regexpGrammar = """
    regularchar = anything:x ?(x in alphanumerics) -> x
    escapedspecialchar = '\\\\' anything:x ?(x in specialchars) -> x
    char = regularchar | escapedspecialchar
    token = (char)+:ds -> Token(''.join(ds))
    cr = '-' char:y -> '-' + y
    charclass = '[' char:x (char|cr)*:xs ']' -> CharClass([x] + xs)
    alt = '|' exps:x -> x
    bracketed = '(' exps:xs ')' -> xs
    suffix = ('*'|'+'|'?'):s -> s
    exp = (bracketed | token | charclass):x suffix?:s -> maybe_suffix(x, s)
    exps = exp*:x alt?:al suffix?:s -> maybe_suffix(exprs(x,al), s)
    """

RegExp = makeGrammar(regexpGrammar, currentframe().f_locals)
