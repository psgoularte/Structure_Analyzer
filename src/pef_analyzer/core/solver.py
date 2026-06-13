"""
Solver simplificado para estimar axial, shear e moment em barra a partir de cargas nodais e distribuídas.
Método demonstrativo:
 - axial = soma das projeções das forças nodais (vx,vy,vz) no eixo da barra
 - shear = soma das componentes transversais em módulo
 - moment = shear * L/2 (aproximação)
Para análise rigorosa use método FEM / elemento de viga 3D.
"""
from typing import List
from math import sqrt
from .bar import Bar
from .node import Node
from .load import eval_expr


def compute_bar_results(bar: Bar, nodes: List[Node]):
    ni = nodes[bar.node_i]
    nj = nodes[bar.node_j]
    dx = nj.x - ni.x
    dy = nj.y - ni.y
    dz = nj.z - ni.z
    L = sqrt(dx*dx + dy*dy + dz*dz) if (dx or dy or dz) else 1.0
    # eixo unitário
    ux, uy, uz = dx / L, dy / L, dz / L

    # somar cargas nodais: assumimos que cargas nodais foram colocadas nos nodes.loads
    axial = 0.0
    shear = 0.0

    # For each node, sum point loads (project along bar for axial, rest is shear magnitude)
    for idx, node in enumerate((ni, nj)):
        for ld in node.loads:
            if ld.get("type") == "point":
                # componente vetorial (vx, vy, vz)
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                # if expr present, evaluate at node param (t=0 for ni, t=1 for nj)
                expr = ld.get("expr")
                if expr:
                    t = 0.0 if idx == 0 else 1.0
                    # evaluate possible scalar magnitude to add to vy
                    try:
                        mag = eval_expr(expr, t)
                        # add along vy for example (user decides)
                        vy += mag
                    except Exception:
                        pass
                # axial (signed)
                axial += vx*ux + vy*uy + vz*uz
                # transverse component magnitude (approx)
                tvx = vx - (vx*ux + vy*uy + vz*uz)*ux
                tvy = vy - (vx*ux + vy*uy + vz*uz)*uy
                tvz = vz - (vx*ux + vy*uy + vz*uz)*uz
                shear += sqrt(tvx*tvx + tvy*tvy + tvz*tvz)

    # distributed loads along bar (approx integrate midpoint)
    for ld in bar.loads:
        if ld.get("type") == "dist":
            expr = ld.get("expr")
            direction = ld.get("direction", "vy")
            if expr:
                # sample at midpoint t=0.5
                try:
                    w = eval_expr(expr, 0.5)
                except Exception:
                    w = 0.0
                # treat w as transverse load per length
                shear += abs(w) * L

    # approximate moment as shear * L/2
    moment = shear * L / 2.0

    bar.results['axial'] = axial
    bar.results['shear'] = shear
    bar.results['moment'] = moment
    return bar.results


"""
Módulo Solver - Implementa a lógica para calcular os efeitos das cargas na estrutura.
"""

class Solver:
    def __init__(self, nodes, bars, loads):
        self.nodes = nodes
        self.bars = bars
        self.loads = loads

    def calculate_reactions(self):
        # Lógica para calcular as reações nos nós
        pass

    def calculate_internal_forces(self):
        # Lógica para calcular as forças internas nas barras
        pass

    def analyze_structure(self):
        self.calculate_reactions()
        self.calculate_internal_forces()
        # Outras análises podem ser adicionadas aqui
        pass

    def get_results(self):
        # Retorna os resultados da análise
        return {
            "nodes": self.nodes,
            "bars": self.bars,
            "loads": self.loads,
            # Adicione outros resultados conforme necessário
        }