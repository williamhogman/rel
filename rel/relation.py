import collections
import itertools

import sympy

from rel import exc
from rel.structure import MappingTuple, values, to_values_notation


def in_domain(value, domain):
    return isinstance(value, domain)

def tuple_in_domain(t, domains):
    return all(in_domain(v, d) for (v, d) in zip(t, domains))
    

class Attribute(object):
    __slots__ = ("_name", "_type")

    def __init__(self, t, name):
        self._type = t
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    def in_domain(self, v):
        return in_domain(v, self._type)

    def __repr__(self):
        return "Attribute({0}, {1})".format(repr(self._type), repr(self._name))

    def rename(self, to):
        if to == self._name:
            return self
        else:
            return Attribute(self._type, to)
    def __eq__(self, other):
        return isinstance(other, Attribute) and self._type == other._type and self._name == other._name

    def __hash__(self):
        return hash((self._type, self._name))

class Relation(object):

    @property
    def attributes(self):
        return self._attributes

    @property
    def attribute_names(self):
        return [attr.name for attr in self._attributes]

    def attribute(self, name):
        for a in self.attributes:
            if a._name == name:
                return a

    @property
    def tuples(self):
        return self._tuples

    def _parse_attr(self, attributes):
        for attr in attributes:
            if isinstance(attr, Attribute):
                yield attr
            else:
                t, n = attr
                yield Attribute(t, n)

    def _parse_tuples(self, tuples):
        for t in tuples:
            if isinstance(t, MappingTuple):
                yield t
            else:
                yield MappingTuple(t)

    def _check_tuples(self):
        nattr = len(self._attributes)

        for t in self._tuples:
            if len(t) != nattr:
                raise exc.InvalidTuple("Tried to place tuple {0} ({1}) into relation with attributes {2} ({3})"
                                   .format(t, len(t), self.attributes, len(self.attributes)))

            for (name, val) in t.items():
                if not self.attribute(name).in_domain(val):
                    raise ValueOutsideDomain("Value {0} was outside the domain of {1}".format(val, domain))



    def __init__(self, attributes, tuples):
        self._attributes = set(self._parse_attr(attributes))
        self._tuples = set(self._parse_tuples(tuples))

        self._check_tuples()

    def __repr__(self):
        # The two zero-order relations doe and dee are special cases
        if self.order == 0:
            # Dee if the cardinality is one
            return "Dee" if self.cardinality == 1 else "Doe"
        else:
            return "Relation({0}, {1})".format(repr(self.attributes), repr(self._tuples))

    def project(self, attribute_names):
        if len(attribute_names) == 0:
            if self.cardinality == 0:
                return Doe
            else:
                return Dee

        nt = set(t.project(attribute_names) for t in self._tuples)
        attr = set(self.attribute(name) for name in attribute_names)
        return Relation(attr, nt)

    def select(self, expr):
        # Selecting None or True should yield the relation as is
        # and thus are equivalent to the identity function.
        # None is treated as the empty set of restrictions.
        # True is treated as a tautology 
        # False is treated as a contradiction, yielding an empty body


        if expr is None or expr == True:
            return self
        elif expr == False:
            return Relation(self._attributes, ())
        elif isinstance(expr, sympy.Expr):
            return Relation(self._attributes,
                            (t for t in self.tuples if expr.subs(t.items())))
        else:
            return None


    def _process_rename(self, mapping):
        for attribute in self._attributes:
            yield attribute.rename(mapping.get(attribute.name, attribute.name))

    def rename(self, mapping):
        mapping = dict(mapping)
        attr = self._process_rename(mapping)
        tuples = [t.rename(mapping) for t in self._tuples]
        return Relation(attr, tuples)

    def _join_tuples_on(self, left, right, on):
            for (l, r) in itertools.product(left, right):
                # If the left side contains the common
                # attributes and they match
                if l.matching_superset_of(r.project(on)):
                    # then yield the union
                    yield l.union(r)

    def join(self, other):
        disjoint = self.attributes != other.attributes and all(a not in other.attributes for a in self.attributes)
        if disjoint:
            return self.product(other)
        else:
            # The new relation will have the union of the two relation's attributes
            attributes = self.attributes | other.attributes
            common = self.attributes & other.attributes
            tuples = self._join_tuples_on(self.tuples, other.tuples, common)
            return Relation(attributes, tuples)


    def product(self, other):
        attr = self.attributes | other.attributes
        body = (a.union(b) for (a, b) in itertools.product(self.tuples, other.tuples))
        return Relation(attr, body)

    def _is_candidate_key(self, key):

        if isinstance(key, str):
            key = (key, )

        # If the cardinality of the entire relation is the same as
        # the cardinality of the projection of the relation onto the
        # key components are equal then the key is a candidate key.
        orig = len(self._tuples)
        
        return len(self.pi(key)) == orig

    @property
    def candidate_keys(self):
        names = tuple(self.attribute_names)

        # The full collection of attributes is always a candidate key
        yield names

        for i in range(1, self.order):
            for key in itertools.combinations(names, i):
                if self._is_candidate_key(key):
                    yield key

    @property
    def cardinality(self):
        return len(self._tuples)
        
    @property
    def order(self):
        return len(self._attributes)

    def __len__(self):
        return self.cardinality

    def __eq__(self, other):
        return (
            self.attributes == other.attributes and
            self.tuples == other.tuples
        )

    pi = project
    sigma = select
    rho = rename
        

# We call the empty tuple et for readability
_et = tuple()

Dee = Relation(_et, (_et, ))
Doe = Relation(_et, _et)
