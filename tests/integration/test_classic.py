"""Testes de integração com problemas clássicos."""
import pytest
from pef_analyzer.core.domain.node import Node
from pef_analyzer.core.domain.element import Element
from pef_analyzer.core.domain.support import Support, SupportType
from pef_analyzer.core.domain.load import PointLoad, DistributedLoad
from pef_analyzer.core.solver.analyzer import Analyzer


class TestSimpleBeam:
    def test_uniform_load(self):
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.PINNED))
        n2 = Node(x=6, y=0, id="B")
        n2.set_support(Support(SupportType.ROLLER))
        beam = Element(node_i=n1, node_f=n2, id="Viga")
        beam.add_load(DistributedLoad(w_function=-10.0))
        analyzer = Analyzer(nodes=[n1, n2], elements=[beam])
        result = analyzer.analyze()
        assert result.isostatic
        ra = result.reactions.get("R_{y,A}", 0)
        rb = result.reactions.get("R_{y,B}", 0)
        assert abs(ra - 30.0) < 0.1
        assert abs(rb - 30.0) < 0.1
        forces = result.internal_forces["Viga"]
        _, V_mid, M_mid = forces.evaluate_at(3.0)
        assert abs(V_mid) < 0.5
        assert abs(M_mid - 45.0) < 0.5

    def test_point_load_center(self):
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.PINNED))
        n2 = Node(x=6, y=0, id="B")
        n2.set_support(Support(SupportType.ROLLER))
        beam = Element(node_i=n1, node_f=n2, id="Viga")
        beam.add_point_load(PointLoad(fy=-60.0, position=3.0))
        result = Analyzer(nodes=[n1, n2], elements=[beam]).analyze()
        ra = result.reactions.get("R_{y,A}", 0)
        rb = result.reactions.get("R_{y,B}", 0)
        assert abs(ra - 30.0) < 0.1
        assert abs(rb - 30.0) < 0.1
        forces = result.internal_forces["Viga"]
        _, _, M_mid = forces.evaluate_at(3.0)
        assert abs(M_mid - 90.0) < 0.5


class TestCantilever:
    def test_tip_load(self):
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.FIXED))
        n2 = Node(x=4, y=0, id="B")
        beam = Element(node_i=n1, node_f=n2, id="Balanço")
        beam.add_point_load(PointLoad(fy=-20.0, position=4.0))
        result = Analyzer(nodes=[n1, n2], elements=[beam]).analyze()
        assert result.isostatic
        ry = result.reactions.get("R_{y,A}", 0)
        m = result.reactions.get("M_{A}", 0)
        assert abs(ry - 20.0) < 0.1
        assert abs(m - 80.0) < 0.5
        forces = result.internal_forces["Balanço"]
        _, V_tip, M_tip = forces.evaluate_at(4.0)
        assert abs(V_tip + 20.0) < 0.1
        assert abs(M_tip) < 0.5

    def test_uniform_load(self):
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.FIXED))
        n2 = Node(x=4, y=0, id="B")
        beam = Element(node_i=n1, node_f=n2, id="Balanço")
        beam.add_load(DistributedLoad(w_function=-10.0))
        result = Analyzer(nodes=[n1, n2], elements=[beam]).analyze()
        ry = result.reactions.get("R_{y,A}", 0)
        m = result.reactions.get("M_{A}", 0)
        assert abs(ry - 40.0) < 0.5
        assert abs(m - 80.0) < 0.5


class TestHyperstatic:
    def test_two_span_is_hyperstatic(self):
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.PINNED))
        n2 = Node(x=6, y=0, id="B")
        n2.set_support(Support(SupportType.ROLLER))
        n3 = Node(x=10, y=0, id="C")
        n3.set_support(Support(SupportType.ROLLER))
        beam1 = Element(node_i=n1, node_f=n2, id="T1")
        beam2 = Element(node_i=n2, node_f=n3, id="T2")
        beam1.add_load(DistributedLoad(w_function=-10.0))
        analyzer = Analyzer(nodes=[n1, n2, n3], elements=[beam1, beam2])
        assert analyzer.is_hyperstatic
        assert analyzer.degree_of_indeterminacy == 1
