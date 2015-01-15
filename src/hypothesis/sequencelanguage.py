def concatenation(*expressions):
    parts = []
    for x in expressions:
        if isinstance(x, Concatenation):
            parts.extend(x.subsequences)
        elif isinstance(x, Empty):
            continue
        else:
            parts.append(x)
    if len(parts) == 0:
        return empty()
    if len(parts) == 1:
        return parts[0]
    return Concatenation(parts)


def alternation(*expressions):
    parts = []

    def add(x):
        if x not in parts:
            parts.append(x)
    for x in expressions:
        if isinstance(x, Optional):
            add(x.expression)
            add(empty())
        elif isinstance(x, Alternation):
            for t in x.alternatives:
                add(t)
        else:
            add(x)
    if len(parts) == 1:
        alt = parts[0]
    else:
        alt = Alternation(parts)
    return alt


def intersection(*expressions):
    parts = []

    def add(x):
        if x not in parts:
            parts.append(x)
    for x in expressions:
        if isinstance(x, Intersection):
            for r in x.requirements:
                add(r)
        elif isinstance(x, Empty):
            return x
        else:
            add(x)
    if len(parts) == 1:
        return parts[0]
    else:
        return Intersection(parts)


def literal(*values):
    values = tuple(values)
    if not values:
        return Empty()
    return Literal(values)


def optional(expression):
    return expression.optional()


def repetition(expression):
    return expression.repetition()


def empty():
    return Empty()


class Expression(object):
    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            pass
        self._hash = self.compute_hash()
        return self._hash

    def __eq__(self, other):
        """Stupid workaround for python3 undefining an inherited hash method
        if you define __eq__"""
        return self._eq(other)

    def __nonzero__(self):
        return True

    def __bool__(self):
        return self.__nonzero__()

    def __add__(self, other):
        if not isinstance(other, Expression):
            raise ValueError("Cannot add Expression and %r" % (other,))
        return concatenation(self, other)

    def __or__(self, other):
        if not isinstance(other, Expression):
            raise ValueError("Cannot or Expression and %r" % (other,))
        return alternation(self, other)

    def __and__(self, other):
        if not isinstance(other, Expression):
            raise ValueError("Cannot and Expression and %r" % (other,))
        return intersection(self, other)

    def optional(self):
        return Optional(self)

    def repetition(self):
        return Repetition(self)

    def bracketed_repr(self):
        return "(%s)" % (repr(self),)


class Empty(Expression):
    def children(self):
        return ()

    def __hash__(self):
        return 17

    def compute_hash(self):
        return 17

    def _eq(self, other):
        return isinstance(other, Empty)

    def __repr__(self):
        return "empty()"

    def optional(self):
        return self

    def repetition(self):
        return self

    def __nonzero__(self):
        return False


def argument_list(args):
    args = tuple(map(repr, args))
    call = ', '.join(args)
    if len(args) > 255:
        return "*[%s]" % (call,)
    else:
        return call


class Literal(Expression):
    def children(self):
        return ()

    def __hash__(self):
        return super(Literal, self).__hash__()

    def __init__(self, values):
        self.values = tuple(values)

    def compute_hash(self):
        return hash(self.values)

    def _eq(self, other):
        return isinstance(other, Literal) and (
            self.values == other.values
        )

    def __repr__(self):
        return "literal(%s)" % (argument_list(self.values,))

    def bracketed_repr(self):
        return repr(self)


class Alternation(Expression):
    def __init__(self, alternatives):
        self.alternatives = tuple(alternatives)

    def children(self):
        return self.alternatives

    def compute_hash(self):
        return hash(self.alternatives)

    def _eq(self, other):
        return isinstance(other, Alternation) and (
            self.alternatives == other.alternatives
        )

    def __repr__(self):
        return "alternation(%s)" % (argument_list(self.alternatives),)

    def optional(self):
        return self | empty()


class Concatenation(Expression):
    def __init__(self, subsequences):
        self.subsequences = tuple(subsequences)

    def children(self):
        return self.subsequences

    def compute_hash(self):
        return hash(self.subsequences)

    def _eq(self, other):
        return isinstance(other, Concatenation) and (
            self.subsequences == other.subsequences
        )

    def __repr__(self):
        return "concatenation(%s)" % (argument_list(self.subsequences),)


class Intersection(Expression):
    def __init__(self, requirements):
        assert not any(isinstance(r, Empty) for r in requirements)
        self.requirements = tuple(requirements)

    def children(self):
        return self.requirements

    def compute_hash(self):
        return ~hash(self.requirements)

    def _eq(self, other):
        return isinstance(other, Intersection) and (
            self.requirements == other.requirements
        )

    def __repr__(self):
        return "intersection(%s)" % (argument_list(self.requirements),)


class Repetition(Expression):
    def __init__(self, expression):
        self.expression = expression

    def children(self):
        return (self.expression,)

    def compute_hash(self):
        return ~hash(self.expression)

    def _eq(self, other):
        return isinstance(other, Repetition) and (
            self.expression == other.expression
        )

    def optional(self):
        return self

    def repetition(self):
        return self

    def __repr__(self):
        return "repetition(%s)" % (repr(self.expression),)


class Optional(Expression):
    def __init__(self, expression):
        self.expression = expression

    def children(self):
        return (self.expression,)

    def compute_hash(self):
        return ~hash(self.expression)

    def _eq(self, other):
        return isinstance(other, Optional) and (
            self.expression == other.expression
        )

    def optional(self):
        return self

    def repetition(self):
        return self.expression.repetition()

    def __repr__(self):
        return "optional(%s)" % (repr(self.expression),)
