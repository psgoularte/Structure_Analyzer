"""
Módulo Support - Define os tipos de vínculos/apoios estruturais.

Implementa os três gêneros de apoios segundo a teoria das estruturas:
- Primeiro Gênero (Apoio Móvel): 1 restrição (y)
- Segundo Gênero (Apoio Fixo): 2 restrições (x, y)
- Terceiro Gênero (Engaste): 3 restrições (x, y, rotação)
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

import sympy as sp


class SupportType(Enum):
    """
    Enumeração dos tipos de vínculos/apoios estruturais.
    
    Attributes:
        ROLLER: Apoio de primeiro gênero (móvel) - restringe deslocamento vertical.
        PINNED: Apoio de segundo gênero (fixo) - restringe deslocamentos x e y.
        FIXED: Apoio de terceiro gênero (engaste) - restringe deslocamentos e rotação.
    """
    ROLLER = auto()      # 1º gênero - apoio móvel
    PINNED = auto()      # 2º gênero - apoio fixo
    FIXED = auto()       # 3º gênero - engaste


@dataclass
class Support:
    """
    Representa um vínculo/apoio estrutural.
    
    Define as restrições de movimento e as reações de apoio associadas
    conforme o tipo de vínculo (1º, 2º ou 3º gênero).
    
    Attributes:
        support_type: Tipo do vínculo (ROLLER, PINNED, FIXED).
        angle: Ângulo da direção de restrição (apenas para apoios móveis).
               Em graus, medido a partir do eixo x positivo.
               Default: 90° (restrição na direção y).
               
    Example:
        >>> # Apoio móvel vertical (padrão)
        >>> support_roller = Support(SupportType.ROLLER)
        >>> 
        >>> # Apoio fixo
        >>> support_pinned = Support(SupportType.PINNED)
        >>> 
        >>> # Engaste
        >>> support_fixed = Support(SupportType.FIXED)
        >>> 
        >>> # Apoio móvel inclinado (45°)
        >>> support_inclined = Support(SupportType.ROLLER, angle=45)
    """
    
    support_type: SupportType
    angle: Optional[float] = None  # em graus
    
    def __post_init__(self):
        """Inicializa valores padrão após criação."""
        if self.support_type == SupportType.ROLLER and self.angle is None:
            self.angle = 90.0  # Vertical para cima é o padrão
    
    @property
    def num_restrictions(self) -> int:
        """
        Retorna o número de restrições impostas pelo vínculo.
        
        Returns:
            1 para ROLLER, 2 para PINNED, 3 para FIXED.
        """
        restrictions = {
            SupportType.ROLLER: 1,
            SupportType.PINNED: 2,
            SupportType.FIXED: 3,
        }
        return restrictions[self.support_type]
    
    @property
    def has_rotation_restriction(self) -> bool:
        """Verifica se o vínculo restringe rotação (engaste)."""
        return self.support_type == SupportType.FIXED
    
    @property
    def has_horizontal_restriction(self) -> bool:
        """Verifica se o vínculo restringe deslocamento horizontal."""
        if self.support_type in (SupportType.PINNED, SupportType.FIXED):
            return True
        if self.support_type == SupportType.ROLLER:
            # Roller restringe perpendicular à direção de rolamento
            # Se angle = 0° (rolamento vertical), restringe horizontal
            return self.angle is not None and abs(self.angle % 180) < 1e-6
        return False
    
    @property
    def has_vertical_restriction(self) -> bool:
        """Verifica se o vínculo restringe deslocamento vertical."""
        if self.support_type in (SupportType.PINNED, SupportType.FIXED):
            return True
        if self.support_type == SupportType.ROLLER:
            # Se angle = 90° (rolamento horizontal), restringe vertical
            return self.angle is not None and abs((self.angle - 90) % 180) < 1e-6
        return False
    
    def get_reaction_symbols(self, node_id: str) -> dict[str, sp.Symbol]:
        """
        Gera os símbolos SymPy para as reações de apoio.
        
        Args:
            node_id: Identificador do nó onde o vínculo está aplicado.
            
        Returns:
            Dicionário com símbolos das reações de apoio.
            - ROLLER: {'R_normal': Symbol}
            - PINNED: {'Rx': Symbol, 'Ry': Symbol}
            - FIXED: {'Rx': Symbol, 'Ry': Symbol, 'M': Symbol}
        """
        reactions = {}
        
        if self.support_type == SupportType.ROLLER:
            # Apoio móvel: reação na direção de restrição.
            if self.angle is None or abs((self.angle - 90) % 180) < 1e-6:
                reactions['R_normal'] = sp.Symbol(f'R_{{y,{node_id}}}')
            elif abs(self.angle % 180) < 1e-6:
                reactions['R_normal'] = sp.Symbol(f'R_{{x,{node_id}}}')
            else:
                reactions['R_normal'] = sp.Symbol(f'R_{{{node_id}}}')
            
        elif self.support_type == SupportType.PINNED:
            # Apoio fixo: reações horizontais e verticais
            reactions['Rx'] = sp.Symbol(f'R_{{x,{node_id}}}')
            reactions['Ry'] = sp.Symbol(f'R_{{y,{node_id}}}')
            
        elif self.support_type == SupportType.FIXED:
            # Engaste: reações horizontais, verticais e momento
            reactions['Rx'] = sp.Symbol(f'R_{{x,{node_id}}}')
            reactions['Ry'] = sp.Symbol(f'R_{{y,{node_id}}}')
            reactions['M'] = sp.Symbol(f'M_{{{node_id}}}')
        
        return reactions
    
    def get_reaction_components(self, node_id: str) -> dict[str, tuple[sp.Symbol, float, float]]:
        """
        Retorna as componentes das reações de apoio.
        
        Args:
            node_id: Identificador do nó onde o vínculo está aplicado.
            
        Returns:
            Dicionário com tuplas (símbolo, cos(theta), sin(theta)) para cada componente.
            Os valores cos/sin definem a direção da reação.
        """
        components = {}
        reactions = self.get_reaction_symbols(node_id)
        
        if self.support_type == SupportType.ROLLER:
            # Reação na direção de restrição do rolete.
            theta = sp.rad(self.angle) if self.angle is not None else sp.pi / 2
            symbol = reactions.get('R_normal')
            components['R_normal'] = (symbol, sp.cos(theta), sp.sin(theta))
            
        elif self.support_type == SupportType.PINNED:
            # Reações nas direções x e y
            components['Rx'] = (reactions['Rx'], 1.0, 0.0)
            components['Ry'] = (reactions['Ry'], 0.0, 1.0)
            
        elif self.support_type == SupportType.FIXED:
            # Reações nas direções x, y e momento
            components['Rx'] = (reactions['Rx'], 1.0, 0.0)
            components['Ry'] = (reactions['Ry'], 0.0, 1.0)
            components['M'] = (reactions['M'], 0.0, 0.0)  # Momento é escalar
        
        return components
    
    def __repr__(self) -> str:
        """Representação em string do vínculo."""
        type_names = {
            SupportType.ROLLER: "ROLLER",
            SupportType.PINNED: "PINNED",
            SupportType.FIXED: "FIXED",
        }
        if self.angle is not None:
            return f"Support(type={type_names[self.support_type]}, angle={self.angle}°)"
        return f"Support(type={type_names[self.support_type]})"
