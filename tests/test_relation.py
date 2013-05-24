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
