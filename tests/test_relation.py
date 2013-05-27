from nose.tools import eq_, ok_

import rel.relation as r
from rel import values

class TestRelationAxioms(object):
    @property
    def ex(self):
        return r.Relation([(int, "id")], 
                            values(("id", ), [(1, )]))        

    @property
    def ex_emp(self):
        return r.Relation(
            [(int, "id")],
            ()
        )


    def test_project_empty_non_empty_rel(self):
        eq_(self.ex.project([]),
            r.Dee,
            """Projecting a relation with a cardinality greater than one onto the
            empty set of attributes should return Dee"""
        )

    def test_project_empty_empty_rel(self):
        eq_(self.ex_emp.project([]),
            r.Doe,
            """Projecting a relation with a cardinality of exactly zero onto the empty
            set of attributes should return Doe"""
        )


    def test_project_identify(self):
        eq_(self.ex.project(self.ex.attribute_names),
            self.ex,
            """Projecting any relation onto the set of its own attributes should
            return itself"""
        )

    def test_select_false(self):
        selection = self.ex.select(False)

        eq_(selection.attributes,
            self.ex.attributes,
            "Selecting should yield the same set of attributes"
        )

        eq_(selection.cardinality,
            0,
            """Selecting for a contradiction should yield a relation with an empty
            body.""")

        eq_(selection,
            self.ex_emp,
            """Selecting a contracdiction should yield a relation with the same
            header and an empty body""")


    def test_select_tautology_true(self):
        selection = self.ex.select(True)

        eq_(selection,
            self.ex,
            """Selecting on a tautology indicated by the python Boolean value of
            true should be equivalent to the identity function.""")

    def test_select_tautology_none(self):
        selection = self.ex.select(None)

        eq_(selection,
            self.ex,
            """Selecting on a tautology indicated by the python None, in this case
            meaning the empty set of restrictions should be equivalent
            to the identity function""")


abc_header = [(int, "a"), (int, "b"), (int, "c")]

class TestKeys(object):
    @property
    def ex(self):
        return r.Relation(abc_header, 
                          values(("a", "b", "c"), [
                              (1, 10, 100),
                              (2, 20, 200),
                          ]))

    @property
    def ex_dup(self):
        return r.Relation(abc_header,
                          values(["a", "b", "c"], [
                              (1, 1337, 1337),
                              (2, 1337, 1337),
                          ]))

    def test_super_keys(self):
        rk = list(self.ex.super_keys)
        eq_(len(rk),
            2**3,
            """The number of superkeys for a relation where all attrbibutes are
            unique should be equal to the square of the order.""")

    def test_single_key_component():
        sk = list(self.ex_dup.super_keys)
        
        ok_(all("a" in sk for k in sk),
            """In a relation where a single attribute has all other columns
            depending on it and nothing else. It should be included in
            all superkeys"""
        )

    def test_candidate_keys(self):
        ck = list(sorted(self.ex.candidate_keys))
        an = list(sorted(set([k]) for k in self.ex.attribute_names))
        eq_(ck,
            an,
            """The candidate keys of a relation where all attributes are unique
            should be exactly equal to the attribute names""")

    def test_candidate_single_key(self):
        ck = list(self.ex.candidate_keys)
        eq(len(ck),
           1,
           """There should only be a single candidate key if it is the only
           unique attribute. All the superkeys (including itself) are
           therefore supersets of this key.""")
