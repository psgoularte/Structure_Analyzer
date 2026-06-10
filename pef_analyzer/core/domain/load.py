"""
Módulo Load - Define as classes de carregamento estrutural.

Implementa cargas pontuais e distribuídas usando SymPy para permitir
funções matemáticas arbitrárias.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Union, Callable
from enum import Enum, auto

import sympy as sp
import numpy as np


class LoadDirection(Enum):
    """
    Direções padrão para aplicação de cargas.
    
    Attributes:
        GLOBAL_X: Direção global X (horizontal).
        GLOBAL_Y: Direção global Y (vertical).
        GLOBAL_Z: Direção global Z (perpendicular ao plano).
        LOCAL_NORMAL: Direção normal local ao elemento.
        LOCAL_TANGENTIAL: Direção tangencial local ao elemento.
    """
    GLOBAL_X = auto()
    GLOBAL_Y = auto()
    GLOBAL_Z = auto()
    LOCAL_NORMAL = auto()
    LOCAL_TANGENTIAL = auto()


class Load(ABC):
    """
    Classe abstrata base para todos os tipos de carregamento.
    
    Define a interface comum para cargas estruturais, incluindo métodos
    para obter as componentes em coordenadas globais e locais.
    """
    
    @abstractmethod
    def get_global_components(self, x: sp.Symbol, angle: float = 0) -> tuple[sp.Expr, sp.Expr]:
        """
        Retorna as componentes da carga em coordenadas globais.
        
        Args:
            x: Variável simbólica de posição ao longo do elemento.
            angle: Ângulo do elemento em relação ao eixo x (em radianos).
            
        Returns:
            Tupla (Fx, Fy) com as componentes em coordenadas globais.
        """
        pass
    
    @abstractmethod
    def get_magnitude_at(self, position: float) -> float:
        """
        Retorna a magnitude da carga em uma posição específica.
        
        Args:
            position: Posição ao longo do elemento (0 a L).
            
        Returns:
            Magnitude da carga na posição especificada.
        """
        pass
    
    @abstractmethod
    def __repr__(self) -> str:
        """Representação em string da carga."""
        pass


@dataclass
class PointLoad(Load):
    """
    Representa uma carga pontual (concentrada) aplicada em um nó ou posição.
    
    Attributes:
        fx: Componente horizontal da carga (positivo para direita).
        fy: Componente vertical da carga (positivo para cima).
        fz: Componente perpendicular ao plano (positivo para fora).
        position: Posição ao longo do elemento (0 a L), se aplicado em barra.
                  None se aplicado em nó.
                  
    Example:
        >>> # Carga vertical para baixo de 10 kN
        >>> load = PointLoad(fy=-10.0)
        >>> 
        >>> # Carga inclinada aplicada no meio de uma barra
        >>> load = PointLoad(fx=5.0, fy=-8.0, position=2.5)
    """
    
    fx: float = 0.0
    fy: float = 0.0
    fz: float = 0.0
    position: Optional[float] = None
    
    def __post_init__(self):
        """Validação dos valores de entrada."""
        if self.position is not None and self.position < 0:
            raise ValueError("Posição da carga deve ser não-negativa")
    
    @property
    def magnitude(self) -> float:
        """Retorna a magnitude resultante da carga."""
        return (self.fx**2 + self.fy**2 + self.fz**2) ** 0.5
    
    @property
    def angle(self) -> float:
        """Retorna o ângulo da carga em relação ao eixo x (em radianos)."""
        return np.arctan2(self.fy, self.fx)
    
    def get_global_components(self, x: sp.Symbol = None, angle: float = 0) -> tuple[sp.Expr, sp.Expr]:
        """
        Retorna as componentes em coordenadas globais (constantes).
        
        Args:
            x: Não utilizado para carga pontual (para compatibilidade).
            angle: Não utilizado para carga pontual (já está em globais).
            
        Returns:
            Tupla (Fx, Fy) constantes.
        """
        return (sp.Float(self.fx), sp.Float(self.fy))
    
    def get_magnitude_at(self, position: float) -> float:
        """
        Retorna a magnitude se a posição corresponder, zero caso contrário.
        
        Para carga pontual, a magnitude é retornada apenas se a posição
        corresponder exatamente à posição da carga.
        """
        if self.position is None:
            return self.magnitude
        # Tolerância para comparação de floats
        if abs(position - self.position) < 1e-10:
            return self.magnitude
        return 0.0
    
    def __repr__(self) -> str:
        """Representação em string da carga pontual."""
        if self.position is not None:
            return f"PointLoad(fx={self.fx}, fy={self.fy}, pos={self.position})"
        return f"PointLoad(fx={self.fx}, fy={self.fy})"


@dataclass
class DistributedLoad(Load):
    """
    Representa uma carga distribuída ao longo de um elemento.
    
    Aceita funções matemáticas SymPy para definir a variação da carga,
    permitindo cargas uniformes, triangulares, trapézoidais ou curvas complexas.
    
    Attributes:
        w_function: Função SymPy ou callable que define a carga por unidade de 
                    comprimento em função da posição x ao longo do elemento.
                    Positivo no sentido do eixo y local (normal ao elemento).
        direction: Direção de aplicação da carga.
        start_position: Posição inicial da carga ao longo do elemento (default: 0).
        end_position: Posição final da carga ao longo do elemento (default: L do elemento).
        
    Example:
        >>> import sympy as sp
        >>> x = sp.Symbol('x')
        >>> 
        >>> # Carga uniformemente distribuída de 5 kN/m
        >>> w = DistributedLoad(w_function=5.0)
        >>> 
        >>> # Carga triangular crescente de 0 a 10 kN/m
        >>> w = DistributedLoad(w_function=2*x, end_position=5)
        >>> 
        >>> # Carga parabólica
        >>> w = DistributedLoad(w_function=x**2/4)
    """
    
    w_function: Union[sp.Expr, Callable[[float], float], float] = 0.0
    direction: LoadDirection = LoadDirection.LOCAL_NORMAL
    start_position: float = 0.0
    end_position: Optional[float] = None  # Será definido pelo elemento
    
    def __post_init__(self):
        """Processa a função de carga."""
        # Converte constante para expressão SymPy
        if isinstance(self.w_function, (int, float)):
            self.w_function = sp.Float(float(self.w_function))
        
        # Se for callable (função Python), mantém como está
        # Se for sympy.Expr, usa diretamente
    
    @property
    def is_sympy(self) -> bool:
        """Verifica se a função de carga é uma expressão SymPy."""
        return isinstance(self.w_function, sp.Expr)
    
    def get_value_at(self, x_val: float, x_symbol: sp.Symbol = None) -> float:
        """
        Avalia a carga em uma posição específica.
        
        Args:
            x_val: Valor numérico da posição.
            x_symbol: Símbolo SymPy usado na função (se aplicável).
            
        Returns:
            Valor da carga na posição especificada.
        """
        if self.is_sympy:
            if x_symbol is None:
                x_symbol = sp.Symbol('x')
            return float(self.w_function.subs(x_symbol, x_val))
        elif callable(self.w_function):
            return float(self.w_function(x_val))
        else:
            return float(self.w_function)
    
    def get_global_components(self, x: sp.Symbol, angle: float = 0) -> tuple[sp.Expr, sp.Expr]:
        """
        Converte a carga distribuída para componentes globais.
        
        Args:
            x: Variável simbólica de posição ao longo do elemento.
            angle: Ângulo do elemento em relação ao eixo x (em radianos).
            
        Returns:
            Tupla (wx_global, wy_global) com expressões SymPy.
        """
        # Obtém a função de carga na direção local normal
        w_local = self.w_function if self.is_sympy else sp.Symbol('w')
        
        if self.direction == LoadDirection.LOCAL_NORMAL:
            # Carga perpendicular ao elemento
            # Componente global: decompõe a carga normal
            # Normal local aponta a 90° do ângulo do elemento
            normal_angle = angle + sp.pi / 2
            wx = -w_local * sp.sin(angle)  # Componente x da normal
            wy = w_local * sp.cos(angle)    # Componente y da normal
            
        elif self.direction == LoadDirection.LOCAL_TANGENTIAL:
            # Carga tangencial ao elemento
            wx = w_local * sp.cos(angle)
            wy = w_local * sp.sin(angle)
            
        elif self.direction == LoadDirection.GLOBAL_X:
            # Carga na direção global X
            wx = w_local
            wy = sp.Integer(0)
            
        elif self.direction == LoadDirection.GLOBAL_Y:
            # Carga na direção global Y
            wx = sp.Integer(0)
            wy = w_local
            
        else:
            # Default: tratada como normal
            wx = -w_local * sp.sin(angle)
            wy = w_local * sp.cos(angle)
        
        return (wx, wy)
    
    def get_magnitude_at(self, position: float) -> float:
        """
        Retorna a magnitude da carga em uma posição específica.
        
        Args:
            position: Posição ao longo do elemento.
            
        Returns:
            Magnitude da carga se dentro do intervalo, 0 caso contrário.
        """
        if position < self.start_position:
            return 0.0
        if self.end_position is not None and position > self.end_position:
            return 0.0
        
        return self.get_value_at(position)
    
    def get_resultant(self, element_length: float, x_symbol: sp.Symbol = None) -> tuple[float, float, float]:
        """
        Calcula a resultante da carga distribuída.
        
        Args:
            element_length: Comprimento do elemento.
            x_symbol: Símbolo SymPy usado na função.
            
        Returns:
            Tupla (magnitude_resultante, posição_x_resultante, posição_y_resultante)
            onde as posições são relativas ao início do elemento.
        """
        if x_symbol is None:
            x_symbol = sp.Symbol('x')
        
        # Limites de integração
        a = self.start_position
        b = self.end_position if self.end_position is not None else element_length
        
        if self.is_sympy:
            # Integral da carga
            w_expr = self.w_function
            resultant = sp.integrate(w_expr, (x_symbol, a, b))
            
            # Posição da resultante (centróide da área de carga)
            if resultant != 0:
                centroid = sp.integrate(x_symbol * w_expr, (x_symbol, a, b)) / resultant
            else:
                centroid = (a + b) / 2
                
            return (float(resultant), float(centroid), 0.0)  # y=0 no eixo do elemento
        else:
            # Integração numérica para funções callable
            import scipy.integrate as integrate
            
            def integrand(x):
                return self.get_value_at(x, x_symbol)
            
            resultant, _ = integrate.quad(integrand, a, b)
            
            def moment_integrand(x):
                return x * self.get_value_at(x, x_symbol)
            
            if resultant != 0:
                first_moment, _ = integrate.quad(moment_integrand, a, b)
                centroid = first_moment / resultant
            else:
                centroid = (a + b) / 2
            
            return (resultant, centroid, 0.0)
    
    def __repr__(self) -> str:
        """Representação em string da carga distribuída."""
        func_str = str(self.w_function) if self.is_sympy else "callable"
        return f"DistributedLoad(w={func_str}, dir={self.direction.name})"
