import collections
import itertools

class MappingTuple(collections.Mapping):
    __slots__ = ("_fields",)

    def __init__(self, d):
        if isinstance(d, collections.Mapping):
            keys = sorted(d.keys())
            self._fields = tuple((k, d[k]) for k in keys)
        else:
            f = tuple(sorted(d))
            if self._check_duplicates(f):
                raise RuntimeError("found duplicate keys in {0}".format(f))
            self._fields = f


    def _check_duplicates(self, f):
        if len(f) == 0:
            return False
        keys = [x[0] for x in f]
        return len(set(keys)) != len(keys)

    def __getitem__(self, name):
        for (k, v) in self._fields:
            if name == k:
                return v
        raise KeyError(name)

    def __len__(self):
        return len(self._fields)

    def __iter__(self):
        return iter(k for (k, _) in self._fields)

    def __repr__(self):
        if len(self._fields) == 0:
            return "MappingTuple.Empty"
        else:
            return "MappingTuple({0})".format(dict(self._fields))

    def __hash__(self):
        return hash(self._fields)

    def __eq__(self, other):
        return isinstance(other, MappingTuple) and self._fields == other._fields
        

    def matching_superset_of(self, other):
        okeys = set(other.keys())
        skeys = set(self.keys())

        # If there are any keys in other that aren't in the present
        # tuple then we are not matching.

        if any(k not in skeys for k in okeys):
            return False

        return  self.project(okeys) == other.project(okeys)


    def project(self, names):
        # names is a set!

        fixed_names = set()
        for name in names:
            if hasattr(name,  "name"):
                fixed_names.add(name.name)
            else:
                fixed_names.add(name)
                
        if len(fixed_names) == 0:
            return MappingTuple.Empty
        return MappingTuple((k, v) for (k, v) in self._fields if k in fixed_names)

    def _process_rename(self, mapping):
        for (k, v) in self._fields:
            # get k or default to k
            yield (mapping.get(k, k), v)

    def rename(self, mapping):
        return MappingTuple(self._process_rename(mapping))


    def union(self, other):
        # Avoid unneccessary object creation
        if self == MappingTuple.Empty:
            return other
        elif other == MappingTuple.Empty:
            return self

        if not isinstance(other, MappingTuple):
            other = MappingTuple(other)

        return MappingTuple(set(self._fields + other._fields))


    rho = rename
    pi = project

MappingTuple.Empty = MappingTuple(())

def values(keys, tuples):
    for t in tuples:
        yield MappingTuple(zip(keys, t))

def to_values_notation(tuples):
    # cast to an iterator so we can call next
    tuples = iter(tuples)

    first = next(tuples)

    keys = tuple(first.keys())


    values = [tuple(first.values())]

    for t in tuples:
        values.append(tuple(t.values()))

    return "values({0}, {1})".format(repr(keys), repr(tuple(values)))
