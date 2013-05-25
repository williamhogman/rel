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

class _BaseRelation(object):
    """Class handling the absolute operations for relations"""

    def __init__(self, attributes, tuples):
        self._attributes = set(self._parse_attr(attributes))
        self._tuples = set(self._parse_tuples(tuples))

        self._check_tuples()


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
                msg = "Tried to place tuple {0} ({1}) into relation with attributes {2} ({3})"
                raise exc.InvalidTuple(msg.format(t,
                                                  len(t),
                                                  self.attributes, 
                                                  len(self.attributes)))

            for (name, val) in t.items():
                if not self.attribute(name).in_domain(val):
                    msg = "Value {0} was outside the domain of {1}"
                    raise ValueOutsideDomain(msg.format(val, domain))

    # Accessor propertyies for two components of the relation. Right
    # now there is no good reason for these to be properties. In the
    # future, however, things like laziness could be implemented using
    # these.

    @property
    def tuples(self):
        return self._tuples

    @property
    def attributes(self):
        return self._attributes

    # Attribute names is the attribute names expected in our mapping
    # tuples.

    @property
    def attribute_names(self):
        return [attr.name for attr in self._attributes]

    # The cardinality is the number of tuples in the body of the
    # relation.

    @property
    def cardinality(self):
        return len(self._tuples)

    # The order of a relation is defined as the cardinality of the set
    # of attributes, that is to say the number of attributes.
    @property
    def order(self):
        return len(self._attributes)

    # The length of a relation, or rather what Python we want python
    # to consider to be the length is the cardinality of the
    # relation. This is because the Python convention is row-major
    # order.
    def __len__(self):
        return self.cardinality

    # Two relations are equals if and only if they have exactly the
    # same attributes and each the each tuple in the bodies are equal.
    def __eq__(self, other):
        return (
            self.attributes == other.attributes and
            self.tuples == other.tuples
        )

    def attribute(self, name):
        for a in self.attributes:
            if a._name == name:
                return a


    def project(self, attribute_names):
        # Projecting onto the empty set of attribute names returns
        # 0-order relation, either Dee or Doe.

        if len(attribute_names) == 0:
            if self.cardinality == 0:
                return Doe
            else:
                return Dee

        nt = set(t.project(attribute_names) for t in self._tuples)
        attr = set(self.attribute(name) for name in attribute_names)
        return Relation(attr, nt)

    def select(self, expr):
        # None is treated as the empty set of restrictions.
        # True is treated as a tautology 

        # Therefore None or True should yield the relation as is and
        # thus are equivalent to the identity function.
        if expr is None or expr == True:
            return self
        elif expr == False:
            # False is treated as a contradiction, yielding an empty body
            return Relation(self._attributes, ())
        elif callable(expr):
            return Relation(self._attributes,
                            (t for t in self.tuples if expr(t)))
        elif isinstance(expr, sympy.Expr):
            # Sympy expressions 
            return Relation(self._attributes,
                            (t for t in self.tuples if expr.subs(t.items())))
        # Everything else is undefined for now!
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


    def product(self, other):

        # For the product of an arbitrary relation and Dee, the
        # identity law applies.
        if other == Dee:
            return self

        # Furthermore, for any given relation and a
        # zero-cardinality. The null law for products applies.
        if other.cardinality == 0:
            return Relation(self._attributes, ())
        
        # If neither the null or identity laws apply the we go with
        # the generic algorithm.

        # The attributes of the product is the union of the attributes
        # of the two sets.
        attr = self.attributes | other.attributes
        # The body is the union of each pair of mapping tuples in the
        # cartesian product of the sets of tuples
        body = (a.union(b) 
                for (a, b) in
                itertools.product(self.tuples, other.tuples))
        return Relation(attr, body)


class Relation(_BaseRelation):

    def __repr__(self):
        # The two zero-order relations doe and dee are special cases
        if self.order == 0:
            # Dee if the cardinality is one
            return "Dee" if self.cardinality == 1 else "Doe"
        else:
            return "Relation({0}, {1})".format(repr(self.attributes), repr(self._tuples))

    def attributes_disjoint(self, other):
        return (
            self.attributes != other.attributes and
            all(a not in other.attributes for a in self.attributes)
        )

    def _join_tuples_naturally_on(self, other, on):
        tuples = self.tuples
        for (l, r) in itertools.product(tuples, other):
            # If the left side contains the common
            # attributes and they match
            if l.matching_superset_of(r.project(on)):
                # then yield the union
                yield l.union(r)


    def _join_tuples_on(self, other, on):
        on_self, on_other = zip(on)
        tuples = self.tuples
        for (l, r) in itertools.product(tuples, other):
            transformed = l.project(on_self).rename(on)
            if transformed == r.project(on_other):
                yield l.union(r)

    def equi_join(self, other, on):
        """Performs an equi-join between two relations
        
        Performs an equi-join between this relation and the passed-in
        relation on the pairs of columns passed in. The on attributes
        should be a list of two tuples where the first component is
        the name in the present relation and the second component is
        the name in the second relation. The rows returned is the
        subset of the cartesian product where the all the pairs of
        attributes match. Equi-joins as implemented in this system can
        generally be replaced with the more specific natural join or
        the more generic inner join. Equi-joins should be used, when
        the columns being matched are have some columns with the same
        name and some with a different name. This because the
        implementations of inner and equi joins wouldn't support
        that combination of arguments.

        """
        # Equi-joining on the empty set of constraints is simply the
        # product.
        if len(on) == 0:
            return self.product(other)

        attributes = self.attributes | other.attributes
        tuples = self._join_tuples_on(self.tuples, other, on)
        return Relation(attributes, tuples)

    def inner_join(self, other, on):
        """Performs an inner-join between two relations
        
        Performs an inner-join between this relation and the passed in
        relation keeping tuples satsifying the condition. The
        inner-join is basically the product of two tables constrained
        by an ON condition, which is simply a selection expression.

        There is, however, one important caveat with our
        implementation of the generic inner-join. Because we implement
        it as the selection on a product we cannot address attributes
        with the same name. It is therefore impossible to join two
        relations on a columns with the same name. A very simple
        solution to this is to use a rename prior to joining. Another
        option to consider is to use the equi_join, with equi_joins we
        select attribute pairs to join on rather than a logic
        expression. Furthermore, consider using natural-joins if at
        all possible, they are far more elegant than both our equi and
        inner joins.

        """
        # An inner-join is just sugar for sigma_CRITERIA(a X b)
        return self.product(other).select(on)

    def join(self, other):
        """Joins two relations naturally.

        Performs a natural join between this relation and the passed
        in relation keeping only the tuples where the shared
        attributes are equal. Given two relations x and y, x
        consisting of the attributes a and b. While y consists of the
        attributes a and c. Performing a natural-join on these
        relations would then return the subset of the product where
        the values for the sharred attributes, in this case just a,
        match. Natural joins are a special case of equi-joins which,
        in turn, are a special case of inner joins.

        """
        if self.attributes_disjoint(other):
            return self.product(other)
        else:
            # The new relation will have the union of the two relation's attributes
            attributes = self.attributes | other.attributes
            common = self.attributes & other.attributes
            tuples = self._join_tuples_on(self.tuples, other.tuples, common)
            return Relation(attributes, tuples)

    def _is_candidate_key(self, key):

        if isinstance(key, str):
            key = (key, )

        # If the cardinality of the entire relation is the same as
        # the cardinality of the projection of the relation onto the
        # key components are equal then the key is a candidate key.
        orig = len(self._tuples)
        
        return len(self.projection(key)) == orig

    @property
    def candidate_keys(self):
        names = tuple(self.attribute_names)

        # The full collection of attributes is always a candidate key
        yield names

        for i in range(1, self.order):
            for key in itertools.combinations(names, i):
                if self._is_candidate_key(key):
                    yield key

# We call the empty tuple et for readability
_et = tuple()

Dee = Relation(_et, (_et, ))
Doe = Relation(_et, _et)
