"""
Utilitários matemáticos para operações comuns na análise estrutural.
"""

from typing import Tuple
import numpy as np


def rotation_matrix_2d(angle: float) -> np.ndarray:
    """
    Retorna a matriz de rotação 2D para um ângulo dado.
    
    Args:
        angle: Ângulo em radianos.
        
    Returns:
        Matriz 2x2 de rotação.
        
    Example:
        >>> R = rotation_matrix_2d(np.pi/2)
        >>> R @ np.array([1, 0])  # [0, 1]
    """
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [c, -s],
        [s,  c]
    ])


def local_to_global_vector(local_vector: Tuple[float, float], angle: float) -> Tuple[float, float]:
    """
    Transforma um vetor de coordenadas locais para globais.
    
    Args:
        local_vector: Componentes (u, v) no sistema local.
        angle: Ângulo do sistema local em relação ao global.
        
    Returns:
        Tupla (X, Y) no sistema global.
    """
    R = rotation_matrix_2d(angle)
    global_vec = R @ np.array(local_vector)
    return (float(global_vec[0]), float(global_vec[1]))


def global_to_local_vector(global_vector: Tuple[float, float], angle: float) -> Tuple[float, float]:
    """
    Transforma um vetor de coordenadas globais para locais.
    
    Args:
        global_vector: Componentes (X, Y) no sistema global.
        angle: Ângulo do sistema local em relação ao global.
        
    Returns:
        Tupla (u, v) no sistema local.
    """
    R = rotation_matrix_2d(-angle)
    local_vec = R @ np.array(global_vector)
    return (float(local_vec[0]), float(local_vec[1]))


def line_intersection(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    p4: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Calcula a interseção entre duas retas definidas por dois pontos cada.
    
    Args:
        p1, p2: Pontos da primeira reta.
        p3, p4: Pontos da segunda reta.
        
    Returns:
        Tupla (x, y) com as coordenadas da interseção.
        
    Raises:
        ValueError: Se as retas forem paralelas.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    if abs(denom) < 1e-10:
        raise ValueError("Retas paralelas - não há interseção única")
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    
    return (x, y)
