"""
Solver simplificado para estimar axial, shear e moment em barra a partir de cargas nodais e distribuídas.
Método demonstrativo:
 - axial = soma das projeções das forças nodais (vx,vy,vz) no eixo da barra
 - shear = soma das componentes transversais em módulo
 - moment = shear * L/2 (aproximação)
Para análise rigorosa use método FEM / elemento de viga 3D.
"""
from typing import List, Dict, Callable
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

    # Initialize effort functions (callable that takes t from 0 to 1)
    def N(t: float) -> float:
        """Axial force N(t) along bar"""
        result = 0.0
        # Point loads at nodes
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    result += vx*ux + vy*uy + vz*uz
        # Point loads along bar
        for ld in bar.loads:
            if ld.get("type") == "point":
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                result += vx*ux + vy*uy + vz*uz
        # Distributed loads
        for ld in bar.loads:
            if ld.get("type") == "dist":
                expr = ld.get("expr")
                direction = ld.get("direction", "vy")
                if expr:
                    try:
                        w = eval_expr(expr, t)
                        if direction == "vx":
                            result += w * ux
                        elif direction == "vy":
                            result += w * uy
                        elif direction == "vz":
                            result += w * uz
                    except:
                        pass
        return result

    def Vy(t: float) -> float:
        """Shear force Vy(t) in local y direction"""
        result = 0.0
        # Point loads at nodes
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    # Project onto local y direction (perpendicular to bar in xy plane)
                    result += vy - (vx*ux + vy*uy + vz*uz)*uy
        # Point loads along bar
        for ld in bar.loads:
            if ld.get("type") == "point":
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                result += vy - (vx*ux + vy*uy + vz*uz)*uy
        # Distributed loads
        for ld in bar.loads:
            if ld.get("type") == "dist":
                expr = ld.get("expr")
                direction = ld.get("direction", "vy")
                if expr and direction == "vy":
                    try:
                        w = eval_expr(expr, t)
                        result += w * (1 - abs(uy))
                    except:
                        pass
        return result

    def Vz(t: float) -> float:
        """Shear force Vz(t) in local z direction"""
        result = 0.0
        # Point loads at nodes
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    # Project onto local z direction (perpendicular to bar in xz plane)
                    result += vz - (vx*ux + vy*uy + vz*uz)*uz
        # Point loads along bar
        for ld in bar.loads:
            if ld.get("type") == "point":
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                result += vz - (vx*ux + vy*uy + vz*uz)*uz
        # Distributed loads
        for ld in bar.loads:
            if ld.get("type") == "dist":
                expr = ld.get("expr")
                direction = ld.get("direction", "vz")
                if expr and direction == "vz":
                    try:
                        w = eval_expr(expr, t)
                        result += w * (1 - abs(uz))
                    except:
                        pass
        return result

    def My(t: float) -> float:
        """Moment My(t) about local y axis (bending moment)"""
        result = 0.0
        # Node moments contribute to bending moment
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "moment":
                    mx = ld.get("mx", 0.0)
                    my = ld.get("my", 0.0)
                    mz = ld.get("mz", 0.0)
                    # Project moment onto local y axis
                    # My contribution from global moments
                    result += my * uy + mx * ux + mz * uz
        # Point loads contribute based on position
        for ld in bar.loads:
            if ld.get("type") == "point":
                distance = ld.get("distance", 0.0)
                t_pos = min(distance / L, 1.0) if L > 0 else 0.0
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                # Moment contribution from Vz (shear in z direction causes moment about y)
                vz_shear = vz - (vx*ux + vy*uy + vz*uz)*uz
                # Moment = force * distance from point
                if t <= t_pos:
                    result += vz_shear * (t_pos - t) * L
                else:
                    result += vz_shear * (t - t_pos) * L
        # Distributed loads
        for ld in bar.loads:
            if ld.get("type") == "dist":
                expr = ld.get("expr")
                direction = ld.get("direction", "vz")
                if expr and direction == "vz":
                    try:
                        w = eval_expr(expr, t)
                        # Bending moment from distributed load
                        result += w * (1 - abs(uz)) * t * (1 - t) * L
                    except:
                        pass
        return result

    def Mz(t: float) -> float:
        """Moment Mz(t) about local z axis (bending moment)"""
        result = 0.0
        # Node moments contribute to bending moment
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "moment":
                    mx = ld.get("mx", 0.0)
                    my = ld.get("my", 0.0)
                    mz = ld.get("mz", 0.0)
                    # Project moment onto local z axis
                    # Mz contribution from global moments
                    result += mz * uz + mx * ux + my * uy
        # Point loads contribute based on position
        for ld in bar.loads:
            if ld.get("type") == "point":
                distance = ld.get("distance", 0.0)
                t_pos = min(distance / L, 1.0) if L > 0 else 0.0
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                # Moment contribution from Vy (shear in y direction causes moment about z)
                vy_shear = vy - (vx*ux + vy*uy + vz*uz)*uy
                # Moment = force * distance from point
                if t <= t_pos:
                    result += vy_shear * (t_pos - t) * L
                else:
                    result += vy_shear * (t - t_pos) * L
        # Distributed loads
        for ld in bar.loads:
            if ld.get("type") == "dist":
                expr = ld.get("expr")
                direction = ld.get("direction", "vy")
                if expr and direction == "vy":
                    try:
                        w = eval_expr(expr, t)
                        # Bending moment from distributed load
                        result += w * (1 - abs(uy)) * t * (1 - t) * L
                    except:
                        pass
        return result

    def T(t: float) -> float:
        """Torque T(t) about bar axis (twisting)"""
        result = 0.0
        # Node moments contribute directly to torque
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "moment":
                    mx = ld.get("mx", 0.0)
                    my = ld.get("my", 0.0)
                    mz = ld.get("mz", 0.0)
                    # Project moment onto bar axis (torque component)
                    # Torque is the component of moment about the bar axis
                    result += mx * ux + my * uy + mz * uz
        # Torque from forces perpendicular to bar axis
        for idx, node in enumerate((ni, nj)):
            for ld in node.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    # Torque from perpendicular components (cross product with bar axis)
                    tvx = vx - (vx*ux + vy*uy + vz*uz)*ux
                    tvy = vy - (vx*ux + vy*uy + vz*uz)*uy
                    tvz = vz - (vx*ux + vy*uy + vz*uz)*uz
                    # Torque = r × F (simplified for point loads at nodes)
                    result += (tvy*uz - tvz*uy) * 0.5
        # Point loads along bar
        for ld in bar.loads:
            if ld.get("type") == "point":
                vx = ld.get("vx", 0.0)
                vy = ld.get("vy", 0.0)
                vz = ld.get("vz", 0.0)
                # Torque from perpendicular components
                tvx = vx - (vx*ux + vy*uy + vz*uz)*ux
                tvy = vy - (vx*ux + vy*uy + vz*uz)*uy
                tvz = vz - (vx*ux + vy*uy + vz*uz)*uz
                # Torque contribution
                result += (tvy*uz - tvz*uy) * 0.5
        return result

    # Calculate max absolute values for display
    t_values = [i/100.0 for i in range(101)]
    
    N_values = [N(t) for t in t_values]
    Vy_values = [Vy(t) for t in t_values]
    Vz_values = [Vz(t) for t in t_values]
    My_values = [My(t) for t in t_values]
    Mz_values = [Mz(t) for t in t_values]
    T_values = [T(t) for t in t_values]
    
    # Find max absolute values with sign
    N_max = max(N_values, key=abs)
    Vy_max = max(Vy_values, key=abs)
    Vz_max = max(Vz_values, key=abs)
    My_max = max(My_values, key=abs)
    Mz_max = max(Mz_values, key=abs)
    T_max = max(T_values, key=abs)

    # Store both functions and max values
    bar.results['N_func'] = N
    bar.results['Vy_func'] = Vy
    bar.results['Vz_func'] = Vz
    bar.results['My_func'] = My
    bar.results['Mz_func'] = Mz
    bar.results['T_func'] = T
    
    bar.results['N'] = N_max
    bar.results['Vy'] = Vy_max
    bar.results['Vz'] = Vz_max
    bar.results['My'] = My_max
    bar.results['Mz'] = Mz_max
    bar.results['T'] = T_max
    
    # Keep old keys for backward compatibility
    bar.results['axial'] = N_max
    bar.results['shear'] = (Vy_max**2 + Vz_max**2)**0.5
    bar.results['moment'] = (My_max**2 + Mz_max**2)**0.5
    
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