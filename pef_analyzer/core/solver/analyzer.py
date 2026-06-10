"""
Módulo Analyzer - Motor de cálculo simbólico para análise estrutural.

Implementa o método das seções e equações de equilíbrio usando SymPy
para obter as funções analíticas dos esforços internos.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import sympy as sp
import numpy as np

from ..domain.node import Node
from ..domain.element import Element, ElementType
from ..domain.support import Support, SupportType
from ..domain.load import Load, PointLoad, DistributedLoad


@dataclass
class InternalForces:
    """
    Representa as funções simbólicas dos esforços internos em um elemento.
    
    Attributes:
        N: Função simbólica do esforço normal N(x).
        V: Função simbólica do esforço cortante V(x).
        M: Função simbólica do momento fletor M(x).
        x: Símbolo SymPy da coordenada local.
        element_id: ID do elemento associado.
    """
    N: sp.Expr
    V: sp.Expr
    M: sp.Expr
    x: sp.Symbol
    element_id: str
    
    def evaluate_at(self, position: float) -> Tuple[float, float, float]:
        """
        Avalia os esforços em uma posição específica.
        
        Args:
            position: Posição ao longo do elemento (0 a L).
            
        Returns:
            Tupla (N, V, M) com os valores numéricos.
        """
        subs_dict = {self.x: position}
        return (
            float(self.N.subs(subs_dict)),
            float(self.V.subs(subs_dict)),
            float(self.M.subs(subs_dict))
        )
    
    def get_maximum_values(self, length: float) -> Dict[str, Tuple[float, float]]:
        """
        Encontra os valores máximos e mínimos dos esforços ao longo do elemento.
        
        Args:
            length: Comprimento do elemento.
            
        Returns:
            Dicionário com máximos e mínimos de N, V e M.
        """
        results = {}
        for name, func in [('N', self.N), ('V', self.V), ('M', self.M)]:
            # Encontra pontos críticos (derivada = 0)
            d_func = sp.diff(func, self.x)
            critical_points = sp.solve(d_func, self.x)
            
            # Filtra pontos dentro do domínio
            valid_points = [0, length]
            for cp in critical_points:
                if cp.is_real and 0 <= float(cp) <= length:
                    valid_points.append(float(cp))
            
            # Avalia em todos os pontos
            values = [float(func.subs(self.x, p)) for p in valid_points]
            results[name] = (max(values), min(values))
        
        return results


@dataclass
class AnalysisResult:
    """
    Resultado completo da análise estrutural.
    
    Attributes:
        reactions: Dicionário de reações de apoio {node_id: {component: value}}.
        internal_forces: Dicionário de esforços internos {element_id: InternalForces}.
        equilibrium_check: Dicionário com verificação das equações de equilíbrio.
        isostatic: Indica se a estrutura é isostática.
        degree_of_indeterminacy: Grau de hiperestaticidade.
    """
    reactions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    internal_forces: Dict[str, InternalForces] = field(default_factory=dict)
    equilibrium_check: Dict[str, float] = field(default_factory=dict)
    isostatic: bool = False
    degree_of_indeterminacy: int = 0


class Analyzer:
    """
    Motor de cálculo simbólico para análise de estruturas planas.
    
    Implementa o equilíbrio global da estrutura e o método das seções
    para cálculo dos esforços internos, gerando funções analíticas
    usando SymPy.
    
    Attributes:
        nodes: Lista de nós da estrutura.
        elements: Lista de elementos da estrutura.
        
    Example:
        >>> from pef_analyzer.core.domain.node import Node
        >>> from pef_analyzer.core.domain.element import Element
        >>> 
        >>> # Criar estrutura simples
        >>> n1 = Node(x=0, y=0, id="A")
        >>> n2 = Node(x=3, y=0, id="B")
        >>> beam = Element(node_i=n1, node_f=n2)
        >>> 
        >>> # Analisar
        >>> analyzer = Analyzer(nodes=[n1, n2], elements=[beam])
        >>> result = analyzer.analyze()
    """
    
    def __init__(
        self,
        nodes: List[Node],
        elements: List[Element],
    ):
        """
        Inicializa o analisador com a geometria da estrutura.
        
        Args:
            nodes: Lista de todos os nós da estrutura.
            elements: Lista de todos os elementos da estrutura.
        """
        self.nodes = nodes
        self.elements = elements
        
        # Mapeamento de nós para elementos
        self._node_to_elements: Dict[str, List[Element]] = defaultdict(list)
        for elem in elements:
            self._node_to_elements[elem.node_i.id].append(elem)
            self._node_to_elements[elem.node_f.id].append(elem)
    
    @property
    def num_equations(self) -> int:
        """Número de equações de equilíbrio disponíveis (3 para estrutura plana)."""
        return 3
    
    @property
    def num_unknowns(self) -> int:
        """Número de incógnitas (reações de apoio)."""
        unknowns = 0
        for node in self.nodes:
            if node.support:
                unknowns += node.support.num_restrictions
        return unknowns
    
    @property
    def degree_of_indeterminacy(self) -> int:
        """
        Grau de hiperestaticidade da estrutura.
        
        Returns:
            Valor positivo para hiperestática, zero para isostática,
            negativo para hipostática (mecanismo).
        """
        return self.num_unknowns - self.num_equations
    
    @property
    def is_isostatic(self) -> bool:
        """Verifica se a estrutura é isostática."""
        return self.degree_of_indeterminacy == 0
    
    @property
    def is_hyperstatic(self) -> bool:
        """Verifica se a estrutura é hiperestática."""
        return self.degree_of_indeterminacy > 0
    
    @property
    def is_mechanism(self) -> bool:
        """Verifica se a estrutura é um mecanismo (hipostática)."""
        return self.degree_of_indeterminacy < 0
    
    def _collect_reaction_symbols(self) -> Dict[str, sp.Symbol]:
        """
        Coleta todos os símbolos de reações de apoio.
        
        Returns:
            Dicionário com todos os símbolos de reação.
        """
        symbols = {}
        for node in self.nodes:
            if node.support:
                node_symbols = node.support.get_reaction_symbols(node.id)
                symbols.update(node_symbols)
        return symbols
    
    def _build_global_equilibrium_equations(self) -> List[sp.Eq]:
        """
        Constrói as equações de equilíbrio global da estrutura.
        
        Returns:
            Lista de equações SymPy (ΣFx=0, ΣFy=0, ΣM=0).
        """
        # Símbolos de reações
        reaction_symbols = self._collect_reaction_symbols()
        
        # Soma de forças e momentos (convenção: anti-horário positivo)
        sum_fx = sp.Integer(0)
        sum_fy = sp.Integer(0)
        sum_mz = sp.Integer(0)
        
        # Ponto de referência para cálculo de momentos: primeiro nó da estrutura
        # (o valor absoluto das reações não depende do ponto, mas M de engaste sim)
        ref_node = self.nodes[0] if self.nodes else None
        cx = ref_node.x if ref_node else 0
        cy = ref_node.y if ref_node else 0
        
        # Adiciona reações de apoio
        for node in self.nodes:
            if node.support:
                components = node.support.get_reaction_components(node.id)
                for comp_name, (symbol, dir_x, dir_y) in components.items():
                    if comp_name == 'M':
                        # Momento é escalar
                        sum_mz += symbol
                    else:
                        sum_fx += symbol * dir_x
                        sum_fy += symbol * dir_y
                        # Momento da reação em relação ao referência (anti-horário +)
                        dx = node.x - cx
                        dy = node.y - cy
                        sum_mz += dx * symbol * dir_y - dy * symbol * dir_x
        
        # Adiciona cargas nodais
        for node in self.nodes:
            for load in node.loads:
                fx, fy = load.get_global_components()
                sum_fx += fx
                sum_fy += fy
                # Momento da carga (anti-horário +): M = dx*fy - dy*fx
                dx = node.x - cx
                dy = node.y - cy
                sum_mz += dx * fy - dy * fx
        
        # Adiciona cargas distribuídas (resultantes)
        for element in self.elements:
            for load in element.loads:
                res_mag, res_pos, _ = load.get_resultant(element.length, element.local_symbol)
                # Posição global da resultante
                res_x = element.node_i.x + res_pos * element.cos_angle
                res_y = element.node_i.y + res_pos * element.sin_angle
                # Componentes da carga resultante em coordenadas globais
                wx, wy = load.get_global_components(element.local_symbol, element.angle)
                # Integra para obter as componentes resultantes
                res_wx = sp.integrate(wx, (element.local_symbol, load.start_position, 
                                          load.end_position if load.end_position is not None else element.length))
                res_wy = sp.integrate(wy, (element.local_symbol, load.start_position, 
                                          load.end_position if load.end_position is not None else element.length))
                sum_fx += res_wx
                sum_fy += res_wy
                # Momento da resultante (anti-horário +): M = dx*fy - dy*fx
                dx = res_x - cx
                dy = res_y - cy
                sum_mz += dx * res_wy - dy * res_wx
        
        # Adiciona cargas pontuais em elementos
        for element in self.elements:
            for load in element.point_loads:
                if load.position is not None:
                    # Posição global da carga
                    pos_ratio = load.position / element.length
                    load_x = element.node_i.x + pos_ratio * (element.node_f.x - element.node_i.x)
                    load_y = element.node_i.y + pos_ratio * (element.node_f.y - element.node_i.y)
                    sum_fx += load.fx
                    sum_fy += load.fy
                    # Momento (anti-horário +): M = dx*fy - dy*fx
                    dx = load_x - cx
                    dy = load_y - cy
                    sum_mz += dx * load.fy - dy * load.fx
        
        equations = [
            sp.Eq(sum_fx, 0),
            sp.Eq(sum_fy, 0),
            sp.Eq(sum_mz, 0),
        ]
        
        return equations
    
    def _solve_reactions(self) -> Dict[str, float]:
        """
        Resolve as equações de equilíbrio para encontrar as reações.
        
        Returns:
            Dicionário com os valores das reações de apoio no formato {symbol_name: value}.
        """
        equations = self._build_global_equilibrium_equations()
        symbols = list(self._collect_reaction_symbols().values())
        
        # Sistema pode ser indeterminado para estruturas hiperestáticas
        try:
            solution = sp.solve(equations, symbols, dict=True)
            if solution:
                if isinstance(solution, list):
                    solution = solution[0]
                return {str(k): float(v) for k, v in solution.items()}
        except Exception:
            pass
        
        # Para sistemas indeterminados, retorna símbolos não resolvidos
        return {str(s): None for s in symbols}
    
    def _calculate_internal_forces_beam(
        self,
        element: Element,
        reactions: Dict[str, float]
    ) -> InternalForces:
        """
        Calcula os esforços internos em um elemento tipo viga.
        
        Usa o método das seções com integração simbólica. As cargas distribuídas
        são modeladas usando funções de Heaviside para permitir cargas parciais.
        
        Args:
            element: Elemento a ser analisado.
            reactions: Dicionário de reações de apoio calculadas.
            
        Returns:
            Objeto InternalForces com as funções simbólicas.
        """
        x = element.local_symbol
        L = element.length
        
        # Inicializa esforços
        V0 = sp.Rational(0)  # Cortante em x=0
        M0 = sp.Rational(0)  # Momento em x=0
        N0 = sp.Rational(0)  # Normal em x=0
        
        # --- 1. Contribuições do nó inicial ---
        node_i = element.node_i
        
        # Reações do nó inicial
        if node_i.support:
            rx_key = "R_{x," + node_i.id + "}"
            ry_key = "R_{y," + node_i.id + "}"
            m_key = "M_{" + node_i.id + "}"
            
            if rx_key in reactions and reactions[rx_key] is not None:
                rx = reactions[rx_key]
                n_i, v_i = element.to_local_coordinates(rx, 0)
                N0 += n_i
                V0 += v_i
            
            if ry_key in reactions and reactions[ry_key] is not None:
                ry = reactions[ry_key]
                n_i, v_i = element.to_local_coordinates(0, ry)
                N0 += n_i
                V0 += v_i
            
            if m_key in reactions and reactions[m_key] is not None:
                M0 += reactions[m_key]
        
        # Cargas pontuais no nó inicial
        for load in node_i.loads:
            n_i, v_i = element.to_local_coordinates(load.fx, load.fy)
            N0 += n_i
            V0 += v_i
        
        # --- 2. Constrói a função de carga distribuída total usando Heaviside ---
        # w(x): carga transversal local (positiva no sentido local y)
        # p(x): carga axial local (positiva no sentido local x)
        w_total = sp.Rational(0)
        p_total = sp.Rational(0)
        
        for load in element.loads:
            a = load.start_position
            b = load.end_position if load.end_position is not None else L
            
            wx, wy = load.get_global_components(x, element.angle)
            # Converte para coordenadas locais do elemento
            # wy é perpendicular ao elemento -> carga transversal local
            # wx é paralelo ao elemento -> carga axial local
            p_local = wx * sp.cos(element.angle) + wy * sp.sin(element.angle)
            w_local = -wx * sp.sin(element.angle) + wy * sp.cos(element.angle)
            
            # Usa Heaviside para ativar carga apenas entre [a, b]
            H_a = sp.Heaviside(x - a)
            H_b = sp.Heaviside(x - b)
            w_total += w_local * (H_a - H_b)
            p_total += p_local * (H_a - H_b)
        
        # --- 3. Cargas pontuais ao longo do elemento ---
        for load in element.point_loads:
            if load.position is not None and 0 < load.position < L:
                n_i, v_i = element.to_local_coordinates(load.fx, load.fy)
                H_p = sp.Heaviside(x - load.position)
                V0 -= v_i * H_p
                N0 -= n_i * H_p
                M0 -= v_i * (x - load.position) * H_p
        
        # --- 4. Integração simbólica ---
        # Cortante: V(x) = V0 - integral de w_total(t) dt de 0 a x
        # Usamos integração indefinida + condição V(0) = V0
        t = sp.Symbol('t')
        w_t = w_total.subs(x, t)
        p_t = p_total.subs(x, t)
        
        V = -V0 - sp.integrate(w_t, (t, 0, x))
        N = -N0 - sp.integrate(p_t, (t, 0, x))
        
        # Momento: M(x) = -M0 - integral de V(t) dt de 0 a x
        M = -M0 - sp.integrate(V.subs(x, t), (t, 0, x))
        
        return InternalForces(
            N=sp.simplify(N),
            V=sp.simplify(V),
            M=sp.simplify(M),
            x=x,
            element_id=element.id
        )
    
    def analyze(self) -> AnalysisResult:
        """
        Executa a análise completa da estrutura.
        
        Returns:
            Objeto AnalysisResult com reações e esforços internos.
        """
        result = AnalysisResult()
        
        # Calcula propriedades da estrutura
        result.degree_of_indeterminacy = self.degree_of_indeterminacy
        result.isostatic = self.is_isostatic
        
        if self.is_mechanism:
            raise ValueError(
                f"Estrutura é um mecanismo (hipostática). "
                f"Grau de indeterminação: {self.degree_of_indeterminacy}"
            )
        
        # Resolve reações de apoio
        reactions = self._solve_reactions()
        
        # Reorganiza reações por nó
        organized_reactions = {}
        for node in self.nodes:
            if node.support:
                node_reactions = {}
                components = node.support.get_reaction_symbols(node.id)
                for comp_name, symbol in components.items():
                    symbol_str = str(symbol)
                    if symbol_str in reactions:
                        node_reactions[comp_name] = reactions[symbol_str]
                    else:
                        node_reactions[comp_name] = None
                organized_reactions[node.id] = node_reactions
        
        result.reactions = organized_reactions
        
        # Calcula esforços internos para cada elemento
        for element in self.elements:
            if element.element_type == ElementType.BEAM:
                forces = self._calculate_internal_forces_beam(element, reactions)
                result.internal_forces[element.id] = forces
            elif element.element_type == ElementType.BAR:
                # Implementação simplificada para barras de treliça
                x = element.local_symbol
                # Apenas esforço normal
                N = sp.Integer(1)  # Placeholder
                forces = InternalForces(N=N, V=sp.Integer(0), M=sp.Integer(0), 
                                       x=x, element_id=element.id)
                result.internal_forces[element.id] = forces
        
        # Verificação de equilíbrio
        result.equilibrium_check = self._verify_equilibrium(reactions)
        
        return result
    
    def _verify_equilibrium(self, reactions: Dict[str, float]) -> Dict[str, float]:
        """
        Verifica se as equações de equilíbrio são satisfeitas.
        
        Args:
            reactions: Dicionário de reações calculadas.
            
        Returns:
            Dicionário com os resíduos das equações de equilíbrio.
        """
        # Substitui valores das reações nas equações
        equations = self._build_global_equilibrium_equations()
        
        # Cria dicionário de substituição
        subs_dict = {}
        for key, value in reactions.items():
            if value is not None:
                symbol = sp.Symbol(key)
                subs_dict[symbol] = value
        
        # Avalia equações
        residuals = {}
        for i, eq_name in enumerate(['Fx', 'Fy', 'Mz']):
            eq = equations[i]
            if eq is False or eq == False:
                residuals[eq_name] = float('nan')
                continue
            if eq is True or eq == True:
                residuals[eq_name] = 0.0
                continue
            try:
                lhs = eq.lhs.subs(subs_dict)
                residuals[eq_name] = float(lhs)
            except Exception:
                residuals[eq_name] = float('nan')
        
        return residuals
