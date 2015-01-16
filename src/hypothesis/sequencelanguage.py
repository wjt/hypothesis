from hypothesis.internal.utils.distributions import biased_coin
from hypothesis.internal.utils.decorators import memoized


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
        assert self.values

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


class NotAStart(Exception):
    pass


class DFA(object):
    def __init__(self, transitions, terminal_states):
        self.transitions = tuple(map(tuple, transitions))
        self.terminal_states = frozenset(terminal_states)

    def __repr__(self):
        return "DFA(transitions=%r, terminal_states=%r)" % (
            self.transitions, self.terminal_states,
        )

    def generate(self, random, stopping_chance):
        current_state = 0
        while True:
            if (
                current_state in self.terminal_states and (
                    not self.transitions[current_state] or
                    biased_coin(random, stopping_chance)
                )
            ):
                return
            transitions = self.transitions[current_state]
            assert transitions, (current_state, self)
            c, next_state = random.choice(transitions)
            current_state = next_state
            yield c

    def produce(self, random, stopping_chance):
        return list(self.generate(random, stopping_chance))

    def matches(self, value):
        current_state = 0
        for v in value:
            transitions = self.transitions[current_state]
            for c, next_state in transitions:
                if v == c:
                    current_state = next_state
                    break
            else:
                return False
        return current_state in self.terminal_states


class SequenceCompiler(object):
    def __init__(self):
        self.starts_table = {}
        self.emptiness_table = {}
        self.satisfiable_table = {}
        self.simplify_table = {}

    def starting_elements(self, expr):
        if not expr:
            return frozenset()
        try:
            return self.starts_table[expr]
        except KeyError:
            pass

        if isinstance(expr, Literal):
            result = frozenset({expr.values[0]})
        elif isinstance(expr, Alternation):
            result = frozenset()
            for e in expr.alternatives:
                result |= self.starting_elements(e)
        elif isinstance(expr, Concatenation):
            result = self.starting_elements(expr.subsequences[0])
        elif isinstance(expr, Optional):
            result = self.starting_elements(expr.expression)
        elif isinstance(expr, Repetition):
            result = self.starting_elements(expr.expression)
        elif isinstance(expr, Intersection):
            result = self.starting_elements(expr.requirements[0])
            for x in expr.requirements[1:]:
                result &= self.starting_elements(x)
        else:
            assert False, expr
        self.starts_table[expr] = result
        return result

    def differentiate(self, expr, c):
        if isinstance(expr, Literal):
            if c == expr.values[0]:
                return literal(*expr.values[1:])
            else:
                raise NotAStart()
        elif isinstance(expr, Alternation):
            return alternation(*[
                self.differentiate(a, c) for a in expr.alternatives
                if c in self.starting_elements(a)
            ])
        elif isinstance(expr, Concatenation):
            return self.differentiate(expr.subsequences[0], c) + (
                concatenation(*expr.subsequences[1:])
            )
        elif isinstance(expr, Optional):
            return self.differentiate(expr.expression, c)
        elif isinstance(expr, Repetition):
            return self.differentiate(expr.expression, c) + expr
        elif isinstance(expr, Intersection):
            return intersection(*[
                self.differentiate(r, c)
                for r in expr.requirements
            ])
        else:
            assert False, expr

    def can_match_empty(self, expr):
        if not expr:
            return True
        try:
            return self.emptiness_table[expr]
        except KeyError:
            pass

        if isinstance(expr, (Optional, Repetition)):
            result = True
        elif isinstance(expr, (Concatenation, Intersection)):
            result = all(
                self.can_match_empty(c) for c in expr.children()
            )
        elif isinstance(expr, Alternation):
            result = any(
                self.can_match_empty(c) for c in expr.children()
            )
        elif isinstance(expr, Literal):
            result = False
        else:
            assert False, expr

        self.emptiness_table[expr] = result
        return result

    def is_satisfiable(self, expr):
        if not expr:
            return True
        try:
            return self.satisfiable_table[expr]
        except KeyError:
            pass

        if self.can_match_empty(expr):
            result = True
        else:
            cs = self.starting_elements(expr)
            result = any(
                self.is_satisfiable(self.differentiate(expr, c))
                for c in cs
            )
        self.satisfiable_table[expr] = result
        return result

    def transitions(self, expr):
        children = [
            (c, self.differentiate(expr, c))
            for c in self.starting_elements(expr)
        ]
        children = [t for t in children if self.is_satisfiable(t[1])]
        return children

    def compile(self, expr):
        expressions = {}
        elements = []

        sequence_stack = [expr]
        while sequence_stack:
            head = sequence_stack.pop()
            if head in expressions:
                continue
            else:
                assert len(expressions) == len(elements)
                expressions[head] = len(expressions)
                elements.append(head)
                for _, e in self.transitions(head):
                    if e not in elements:
                        sequence_stack.append(e)
        assert expressions
        assert len(elements) == len(expressions)

        return DFA(
            terminal_states=frozenset(
                expressions[e]
                for e in expressions
                if self.can_match_empty(e)
            ),
            transitions=tuple(
                [(c, expressions[e2]) for c, e2 in self.transitions(e)]
                for e in expressions
            )

        )
