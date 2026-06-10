"""
PEF Analyzer - Software educacional para análise de estruturas isostáticas e hiperestáticas em 2D.

Este pacote fornece ferramentas para análise estrutural com ênfase didática,
exibindo as funções analíticas (equações) dos esforços internos além dos diagramas.
"""

__version__ = "0.1.0"
__author__ = "Engenheiro Estrutural"

from pef_analyzer.core.domain.node import Node
from pef_analyzer.core.domain.support import Support, SupportType
from pef_analyzer.core.domain.load import Load, PointLoad, DistributedLoad
from pef_analyzer.core.domain.element import Element
from pef_analyzer.core.solver.analyzer import Analyzer

__all__ = [
    "Node",
    "Support",
    "SupportType", 
    "Load",
    "PointLoad",
    "DistributedLoad",
    "Element",
    "Analyzer",
]
