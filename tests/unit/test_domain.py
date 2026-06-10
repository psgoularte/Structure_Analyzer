"""
Testes unitários para as classes de domínio.
"""

import pytest
import sympy as sp

from pef_analyzer.core.domain.node import Node
from pef_analyzer.core.domain.element import Element, ElementType
from pef_analyzer.core.domain.support import Support, SupportType
from pef_analyzer.core.domain.load import PointLoad, DistributedLoad, LoadDirection


class TestNode:
    """Testes para a classe Node."""
    
    def test_node_creation(self):
        """Testa criação básica de um nó."""
        node = Node(x=0, y=0, id="A")
        assert node.x == 0
        assert node.y == 0
        assert node.id == "A"
        assert node.support is None
        assert node.loads == []
    
    def test_node_auto_id(self):
        """Testa geração automática de ID."""
        node = Node(x=1, y=2)
        assert node.id is not None
        assert node.id.startswith("N_")
    
    def test_node_coordinates(self):
        """Testa propriedade coordinates."""
        node = Node(x=3, y=4)
        assert node.coordinates == (3, 4)
    
    def test_node_distance(self):
        """Testa cálculo de distância entre nós."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=4, id="B")
        assert n1.distance_to(n2) == 5.0
    
    def test_node_add_load(self):
        """Testa adição de carga ao nó."""
        node = Node(x=0, y=0)
        load = PointLoad(fx=10, fy=-20)
        node.add_load(load)
        assert len(node.loads) == 1
        assert node.loads[0] == load
    
    def test_node_support(self):
        """Testa atribuição de apoio ao nó."""
        node = Node(x=0, y=0)
        support = Support(SupportType.PINNED)
        node.set_support(support)
        assert node.support == support
        assert node.support.support_type == SupportType.PINNED
    
    def test_node_reactions(self):
        """Testa símbolos de reações."""
        node = Node(x=0, y=0, id="A")
        support = Support(SupportType.PINNED)
        node.set_support(support)
        reactions = node.reactions
        assert 'Rx' in reactions
        assert 'Ry' in reactions


class TestSupport:
    """Testes para a classe Support."""
    
    def test_roller_support(self):
        """Testa apoio de primeiro gênero."""
        support = Support(SupportType.ROLLER)
        assert support.num_restrictions == 1
        assert not support.has_rotation_restriction
        assert not support.has_horizontal_restriction
        assert support.has_vertical_restriction
    
    def test_pinned_support(self):
        """Testa apoio de segundo gênero."""
        support = Support(SupportType.PINNED)
        assert support.num_restrictions == 2
        assert not support.has_rotation_restriction
        assert support.has_horizontal_restriction
        assert support.has_vertical_restriction
    
    def test_fixed_support(self):
        """Testa apoio de terceiro gênero (engaste)."""
        support = Support(SupportType.FIXED)
        assert support.num_restrictions == 3
        assert support.has_rotation_restriction
        assert support.has_horizontal_restriction
        assert support.has_vertical_restriction
    
    def test_reaction_symbols_roller(self):
        """Testa símbolos de reação para apoio móvel."""
        support = Support(SupportType.ROLLER)
        symbols = support.get_reaction_symbols("A")
        assert 'R_normal' in symbols
    
    def test_reaction_symbols_pinned(self):
        """Testa símbolos de reação para apoio fixo."""
        support = Support(SupportType.PINNED)
        symbols = support.get_reaction_symbols("B")
        assert 'Rx' in symbols
        assert 'Ry' in symbols
    
    def test_reaction_symbols_fixed(self):
        """Testa símbolos de reação para engaste."""
        support = Support(SupportType.FIXED)
        symbols = support.get_reaction_symbols("C")
        assert 'Rx' in symbols
        assert 'Ry' in symbols
        assert 'M' in symbols


class TestPointLoad:
    """Testes para a classe PointLoad."""
    
    def test_point_load_creation(self):
        """Testa criação de carga pontual."""
        load = PointLoad(fx=10, fy=-20)
        assert load.fx == 10
        assert load.fy == -20
        assert load.fz == 0
        assert load.position is None
    
    def test_point_load_magnitude(self):
        """Testa cálculo de magnitude."""
        load = PointLoad(fx=3, fy=4)
        assert load.magnitude == 5.0
    
    def test_point_load_global_components(self):
        """Testa componentes globais."""
        load = PointLoad(fx=10, fy=-20)
        x = sp.Symbol('x')
        fx, fy = load.get_global_components(x)
        assert float(fx) == 10.0
        assert float(fy) == -20.0


class TestDistributedLoad:
    """Testes para a classe DistributedLoad."""
    
    def test_uniform_load(self):
        """Testa carga uniformemente distribuída."""
        load = DistributedLoad(w_function=-10.0)
        assert load.is_sympy
        assert load.get_value_at(5) == -10.0
    
    def test_triangular_load(self):
        """Testa carga triangular com SymPy."""
        x = sp.Symbol('x')
        load = DistributedLoad(w_function=2*x, end_position=5)
        assert load.is_sympy
        assert load.get_value_at(0) == 0
        assert load.get_value_at(2.5) == 5.0
    
    def test_load_global_components(self):
        """Testa componentes globais de carga distribuída."""
        load = DistributedLoad(w_function=-10.0)
        x = sp.Symbol('x')
        wx, wy = load.get_global_components(x, angle=0)
        assert wy == -10.0
    
    def test_resultant_uniform(self):
        """Testa resultante de carga uniforme."""
        load = DistributedLoad(w_function=-10.0)
        resultant, centroid, _ = load.get_resultant(element_length=5)
        assert resultant == -50.0
        assert centroid == 2.5


class TestElement:
    """Testes para a classe Element."""
    
    def test_element_creation(self):
        """Testa criação de elemento."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=0, id="B")
        elem = Element(node_i=n1, node_f=n2, id="E1")
        
        assert elem.id == "E1"
        assert elem.length == 3.0
        assert elem.angle == 0
    
    def test_element_inclined(self):
        """Testa elemento inclinado."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=4, id="B")
        elem = Element(node_i=n1, node_f=n2)
        
        assert elem.length == 5.0
        assert abs(elem.angle - 0.9273) < 0.001  # atan2(4,3)
    
    def test_element_local_transform(self):
        """Testa transformação de coordenadas locais/globais."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=4, id="B")
        elem = Element(node_i=n1, node_f=n2)
        
        # Vetor na direção do elemento (axial)
        fx_global, fy_global = elem.to_global_coordinates(1, 0)
        assert abs(fx_global - 0.6) < 0.001
        assert abs(fy_global - 0.8) < 0.001
    
    def test_element_add_load(self):
        """Testa adição de carga distribuída."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=0, id="B")
        elem = Element(node_i=n1, node_f=n2)
        
        load = DistributedLoad(w_function=-10.0)
        elem.add_load(load)
        
        assert len(elem.loads) == 1
        assert elem.loads[0] == load
    
    def test_element_no_material(self):
        """Testa que elemento não tem propriedades de material (barras perfeitas)."""
        n1 = Node(x=0, y=0, id="A")
        n2 = Node(x=3, y=0, id="B")
        elem = Element(node_i=n1, node_f=n2)
        
        # Elemento deve ter apenas geometria, não E, A, I
        assert elem.length == 3.0
        assert elem.angle == 0
        # Não deve ter atributos E, A, I
        assert not hasattr(elem, 'E')
        assert not hasattr(elem, 'A')
        assert not hasattr(elem, 'I')
