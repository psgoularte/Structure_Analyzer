"""
Bar / Element model (conecta dois nós, propriedades e cargas distribuídas).
"""
from typing import List, Dict, Any


class Bar:
    def __init__(self, bid: int, ni: int, nj: int, 
                 area: float = 0.01,         # Área da seção (m²)
                 e_mod: float = 210e9,       # Módulo de Elasticidade (Pa)
                 iy: float = 5e-5,           # Momento de Inércia no eixo Y local (m^4)
                 iz: float = 2e-4,           # Momento de Inércia no eixo Z local (m^4)
                 j_torsion: float = 1e-5,    # Constante de Torção (m^4)
                 g_mod: float = 80e9):       # Módulo de Cisalhamento (Pa)
        self.id = bid
        self.node_i = int(ni)
        self.node_j = int(nj)
        
        # Propriedades do Material e Seção
        self.area = float(area)
        self.e = float(e_mod)
        self.iy = float(iy)
        self.iz = float(iz)
        self.j = float(j_torsion)
        self.g = float(g_mod)
        
        # cargas distribuídas ou pontuais ao longo da barra
        self.loads: List[Dict[str, Any]] = []
        
        # resultados (serão preenchidos pelo solver)
        self.results = {
            'axial': 0.0,
            'shear': 0.0,
            'moment': 0.0
        }

    def add_force(self, force):
        self.loads.append(force)

    def __repr__(self):
        return f"Bar(id={self.id}, i={self.node_i}, j={self.node_j}, A={self.area}, E={self.e})"