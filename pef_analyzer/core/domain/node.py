"""
Módulo Node - Define a classe base para nós estruturais.

Um nó é um ponto na estrutura onde elementos se conectam e onde podem ser
aplicadas cargas e/ou vínculos (apoios).
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

import sympy as sp

if TYPE_CHECKING:
    from .support import Support
    from .load import PointLoad


@dataclass
class Node:
    """
    Representa um nó na estrutura.
    
    Um nó é definido por suas coordenadas (x, y) no plano 2D e pode conter
    vínculos (apoios) e cargas pontuais aplicadas.
    
    Attributes:
        x: Coordenada x do nó.
        y: Coordenada y do nó.
        id: Identificador único do nó (gerado automaticamente se não fornecido).
        support: Vínculo/apoio aplicado ao nó (opcional).
        loads: Lista de cargas pontuais aplicadas ao nó.
        
    Example:
        >>> node = Node(x=0, y=0, id="A")
        >>> node_a = Node(x=3, y=4)
    """
    
    x: float
    y: float
    id: Optional[str] = None
    support: Optional['Support'] = None
    loads: list['PointLoad'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validação e inicialização pós-criação."""
        if self.id is None:
            self.id = f"N_{id(self)}"
    
    @property
    def coordinates(self) -> tuple[float, float]:
        """Retorna as coordenadas (x, y) do nó como uma tupla."""
        return (self.x, self.y)
    
    @property
    def reactions(self) -> dict[str, sp.Symbol]:
        """
        Retorna os símbolos das reações de apoio associadas a este nó.
        
        Returns:
            Dicionário com símbolos das reações (Rx, Ry, M) ou subconjunto
            dependendo do tipo de vínculo.
        """
        if self.support is None:
            return {}
        return self.support.get_reaction_symbols(self.id)
    
    def add_load(self, load: 'PointLoad') -> None:
        """
        Adiciona uma carga pontual ao nó.
        
        Args:
            load: Carga pontual a ser adicionada.
        """
        self.loads.append(load)
    
    def remove_load(self, load: 'PointLoad') -> None:
        """
        Remove uma carga pontual do nó.
        
        Args:
            load: Carga pontual a ser removida.
        """
        if load in self.loads:
            self.loads.remove(load)
    
    def set_support(self, support: 'Support') -> None:
        """
        Define o vínculo/apoio do nó.
        
        Args:
            support: Vínculo a ser aplicado ao nó.
        """
        self.support = support
    
    def distance_to(self, other: 'Node') -> float:
        """
        Calcula a distância euclidiana até outro nó.
        
        Args:
            other: Outro nó.
            
        Returns:
            Distância euclidiana entre os dois nós.
        """
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __repr__(self) -> str:
        """Representação em string do nó."""
        return f"Node(id='{self.id}', x={self.x}, y={self.y})"
    
    def __eq__(self, other: object) -> bool:
        """Comparação de igualdade baseada no id."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash baseado no id para uso em conjuntos e dicionários."""
        return hash(self.id)
