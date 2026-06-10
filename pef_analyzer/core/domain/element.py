"""
Módulo Element - Define a classe base para elementos estruturais (barras/vigas).

Um elemento é uma conexão entre dois nós que pode receber cargas distribuídas
e sobre o qual são calculados os esforços internos.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, List
from enum import Enum, auto

import sympy as sp
import numpy as np

if TYPE_CHECKING:
    from .node import Node
    from .load import Load, PointLoad, DistributedLoad


class ElementType(Enum):
    """
    Tipos de elementos estruturais.
    
    Attributes:
        BAR: Barra (treliça) - suporta apenas esforço normal.
        BEAM: Viga - suporta cortante e momento fletor.
        FRAME: Pórtico - combina barra e viga.
    """
    BAR = auto()      # Treliça
    BEAM = auto()     # Viga
    FRAME = auto()    # Pórtico


@dataclass
class Element:
    """
    Representa um elemento estrutural (barra ou viga) conectando dois nós.
    
    O elemento é idealizado como uma linha perfeita (sem massa, sem espessura,
    sem propriedades de material). Seu propósito é conectar nós e servir como
    domínio para aplicação de cargas distribuídas. Os esforços internos
    (Normal, Cortante, Momento Fletor) são calculados exclusivamente pelo
    equilíbrio estático, sem considerar deformações ou resistência do material.
    
    Attributes:
        node_i: Nó inicial do elemento.
        node_f: Nó final do elemento.
        element_type: Tipo do elemento (BAR, BEAM, FRAME).
        id: Identificador único do elemento.
        loads: Lista de cargas distribuídas aplicadas ao elemento.
        
    Example:
        >>> from pef_analyzer.core.domain.node import Node
        >>> n1 = Node(x=0, y=0, id="A")
        >>> n2 = Node(x=3, y=0, id="B")
        >>> 
        >>> # Elemento tipo viga (perfeita, sem material)
        >>> beam = Element(node_i=n1, node_f=n2, element_type=ElementType.BEAM)
    """
    
    node_i: 'Node'
    node_f: 'Node'
    element_type: ElementType = ElementType.BEAM
    id: Optional[str] = None
    loads: List['DistributedLoad'] = field(default_factory=list)
    point_loads: List['PointLoad'] = field(default_factory=list)
    
    # Atributos calculados (não inicializados)
    _length: Optional[float] = field(default=None, repr=False)
    _angle: Optional[float] = field(default=None, repr=False)
    _local_x: sp.Symbol = field(default=None, repr=False)
    
    def __post_init__(self):
        """Inicialização e validação pós-criação."""
        if self.id is None:
            i_id = self.node_i.id or "i"
            f_id = self.node_f.id or "f"
            self.id = f"E_{i_id}_{f_id}"
        
        # Cria símbolo para coordenada local
        self._local_x = sp.Symbol('x', real=True, positive=True)
    
    @property
    def length(self) -> float:
        """Comprimento do elemento (calculado das coordenadas dos nós)."""
        if self._length is None:
            self._length = self.node_i.distance_to(self.node_f)
        return self._length
    
    @property
    def L(self) -> float:
        """Alias para length (comprimento)."""
        return self.length
    
    @property
    def angle(self) -> float:
        """
        Ângulo do elemento em relação ao eixo x global (em radianos).
        
        Returns:
            Ângulo entre -π e π.
        """
        if self._angle is None:
            dx = self.node_f.x - self.node_i.x
            dy = self.node_f.y - self.node_i.y
            self._angle = np.arctan2(dy, dx)
        return self._angle
    
    @property
    def angle_degrees(self) -> float:
        """Ângulo em graus."""
        return np.degrees(self.angle)
    
    @property
    def cos_angle(self) -> float:
        """Cosseno do ângulo do elemento."""
        return np.cos(self.angle)
    
    @property
    def sin_angle(self) -> float:
        """Seno do ângulo do elemento."""
        return np.sin(self.angle)
    
    @property
    def direction_vector(self) -> tuple[float, float]:
        """Vetor unitário na direção do elemento (i -> f)."""
        return (self.cos_angle, self.sin_angle)
    
    @property
    def normal_vector(self) -> tuple[float, float]:
        """Vetor unitário normal ao elemento (90° no sentido anti-horário)."""
        return (-self.sin_angle, self.cos_angle)
    
    @property
    def local_symbol(self) -> sp.Symbol:
        """Símbolo SymPy para coordenada local ao longo do elemento (0 a L)."""
        return self._local_x
    
    def add_load(self, load: 'DistributedLoad') -> None:
        """
        Adiciona uma carga distribuída ao elemento.
        
        Args:
            load: Carga distribuída a ser adicionada.
        """
        self.loads.append(load)
        # Atualiza o end_position da carga se não estiver definido
        if load.end_position is None:
            load.end_position = self.length
    
    def remove_load(self, load: 'DistributedLoad') -> None:
        """
        Remove uma carga distribuída do elemento.
        
        Args:
            load: Carga distribuída a ser removida.
        """
        if load in self.loads:
            self.loads.remove(load)
    
    def add_point_load(self, load: 'PointLoad') -> None:
        """
        Adiciona uma carga pontual ao elemento (em posição específica).
        
        Args:
            load: Carga pontual com position definida.
        """
        if load.position is None:
            raise ValueError("PointLoad deve ter position definida para ser adicionada a um elemento")
        self.point_loads.append(load)
    
    def remove_point_load(self, load: 'PointLoad') -> None:
        """
        Remove uma carga pontual do elemento.
        
        Args:
            load: Carga pontual a ser removida.
        """
        if load in self.point_loads:
            self.point_loads.remove(load)
    
    def get_loads_at_position(self, x: float) -> List[tuple[float, float]]:
        """
        Retorna todas as cargas ativas em uma posição específica.
        
        Args:
            x: Posição ao longo do elemento.
            
        Returns:
            Lista de tuplas (wx, wy) com as componentes globais das cargas.
        """
        loads_at_x = []
        for load in self.loads:
            if load.start_position <= x <= (load.end_position or self.length):
                wx, wy = load.get_global_components(self._local_x, self.angle)
                wx_val = float(wx.subs(self._local_x, x)) if load.is_sympy else wx
                wy_val = float(wy.subs(self._local_x, x)) if load.is_sympy else wy
                loads_at_x.append((wx_val, wy_val))
        return loads_at_x
    
    def to_local_coordinates(self, fx: float, fy: float) -> tuple[float, float]:
        """
        Transforma forças de coordenadas globais para locais.
        
        Args:
            fx: Componente global x.
            fy: Componente global y.
            
        Returns:
            Tupla (f_local_axial, f_local_transversal).
        """
        c = self.cos_angle
        s = self.sin_angle
        f_axial = fx * c + fy * s
        f_trans = -fx * s + fy * c
        return (f_axial, f_trans)
    
    def to_global_coordinates(self, f_local: float, f_trans: float) -> tuple[float, float]:
        """
        Transforma forças de coordenadas locais para globais.
        
        Args:
            f_local: Componente axial local.
            f_trans: Componente transversal local.
            
        Returns:
            Tupla (fx, fy) em coordenadas globais.
        """
        c = self.cos_angle
        s = self.sin_angle
        fx = f_local * c - f_trans * s
        fy = f_local * s + f_trans * c
        return (fx, fy)
    
    def get_point_loads_on_nodes(self) -> dict[str, List['PointLoad']]:
        """
        Coleta as cargas pontuais aplicadas nos nós do elemento.
        
        Returns:
            Dicionário com chaves 'i' e 'f' contendo listas de cargas.
        """
        return {
            'i': self.node_i.loads,
            'f': self.node_f.loads
        }
    
    def __repr__(self) -> str:
        """Representação em string do elemento."""
        return (f"Element(id='{self.id}', nodes=({self.node_i.id}, {self.node_f.id}), "
                f"L={self.length:.3f}m, θ={self.angle_degrees:.1f}°)")
    
    def __eq__(self, other: object) -> bool:
        """Comparação de igualdade baseada no id."""
        if not isinstance(other, Element):
            return NotImplemented
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash baseado no id."""
        return hash(self.id)
