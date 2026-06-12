"""
Bar / Element model (conecta dois nós, propriedades e cargas distribuídas).
"""
from typing import List, Dict, Any


class Bar:
    def __init__(self, bid: int, ni: int, nj: int, area: float = 1.0, e_mod: float = 210e9):
        self.id = bid
        self.node_i = int(ni)
        self.node_j = int(nj)
        self.area = float(area)
        self.e = float(e_mod)
        # cargas distribuídas ou pontuais ao longo da barra
        self.loads: List[Dict[str, Any]] = []
        # resultados simplificados
        self.results = {
            'axial': 0.0,
            'shear': 0.0,
            'moment': 0.0
        }

    def add_force(self, force):
        self.forces.append(force)

    def calculate_reaction(self):
        # Placeholder for reaction calculation logic
        pass

    def __repr__(self):
        return f"Bar(length={self.length}, material={self.material}, forces={self.forces})"