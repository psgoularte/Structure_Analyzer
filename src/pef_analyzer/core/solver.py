"""
Solver para esforços internos 3D em eixos LOCAIS da barra.
Método das seções (secção à esquerda, a partir do nó i).

Sistema local:
  e1 – eixo axial (i → j)
  e2 – eixo local y  (projeção de Y global no plano ⊥ e1; fallback Z se barra vertical)
  e3 – eixo local z  (= e1 × e2)

Esforços (convenção clássica de mecânica estrutural):
  N   > 0  →  tração
  Vy, Vz   →  cortante nos eixos locais y e z
  Mz(t) = Mz(0) + ∫₀ᵗ Vy·L dt   (dMz/dx = Vy)
  My(t) = My(0) + ∫₀ᵗ Vz·L dt   (dMy/dx = Vz)
  T        →  torção: projeção dos momentos nodais no eixo axial
"""
from typing import List
from math import sqrt
from .bar import Bar
from .node import Node
from .load import eval_expr


# ── local coordinate system ────────────────────────────────────────────────

def _norm(v):
    n = sqrt(v[0]**2 + v[1]**2 + v[2]**2) or 1.0
    return (v[0]/n, v[1]/n, v[2]/n)

def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def _local_axes(ni, nj):
    """Retorna (e1, e2, e3, L) no sistema local da barra."""
    dx, dy, dz = nj.x - ni.x, nj.y - ni.y, nj.z - ni.z
    L = sqrt(dx*dx + dy*dy + dz*dz) or 1.0
    e1 = (dx/L, dy/L, dz/L)

    # e2: componente de Y global perpendicular a e1
    dot_gy = e1[1]
    if abs(dot_gy) < 0.99:
        e2 = _norm((-dot_gy*e1[0],  1.0 - dot_gy*e1[1], -dot_gy*e1[2]))
    else:                           # barra paralela a Y → referência Z
        dot_gz = e1[2]
        e2 = _norm((-dot_gz*e1[0], -dot_gz*e1[1],  1.0 - dot_gz*e1[2]))

    e3 = _cross(e1, e2)
    return e1, e2, e3, L

def _proj_force(vx, vy, vz, e1, e2, e3):
    v = (vx, vy, vz)
    return _dot(v, e1), _dot(v, e2), _dot(v, e3)   # N, Vy, Vz

def _proj_moment(mx, my, mz, e1, e2, e3):
    m = (mx, my, mz)
    return _dot(m, e1), _dot(m, e2), _dot(m, e3)   # T, My_local, Mz_local

def _dist_local(direction, e1, e2, e3):
    """Decompõe a direção de carga distribuída em (dN, dVy, dVz) locais."""
    if direction == "perpendicular":
        return 0.0, 1.0, 0.0
    dirs = {"vx": (1,0,0), "vy": (0,1,0), "vz": (0,0,1)}
    g = dirs.get(direction, (0,1,0))
    return _dot(g, e1), _dot(g, e2), _dot(g, e3)


# ── main solver ────────────────────────────────────────────────────────────

def compute_bar_results(bar: Bar, nodes: List[Node]):
    ni = nodes[bar.node_i]
    nj = nodes[bar.node_j]
    e1, e2, e3, L = _local_axes(ni, nj)

    # Resultante das cargas do nó i projetadas no sistema local
    ni_N, ni_Vy, ni_Vz = 0.0, 0.0, 0.0
    ni_T, ni_My, ni_Mz = 0.0, 0.0, 0.0
    for ld in ni.loads:
        if ld.get("type") == "point":
            fn, fvy, fvz = _proj_force(ld.get("vx",0), ld.get("vy",0), ld.get("vz",0), e1, e2, e3)
            ni_N += fn; ni_Vy += fvy; ni_Vz += fvz
        elif ld.get("type") == "moment":
            mt, my_, mz_ = _proj_moment(ld.get("mx",0), ld.get("my",0), ld.get("mz",0), e1, e2, e3)
            ni_T += mt; ni_My += my_; ni_Mz += mz_

    # Torção aplicada ao nó j: o método das seções (secção à esquerda) não inclui nj para t < 1,
    # mas o nó j transmite torção constante para toda a barra (equilibrado pela reação em i).
    # Colectamos separadamente para calcular o salto em t=1.
    nj_T = 0.0
    for ld in nj.loads:
        if ld.get("type") == "moment":
            mt, _, _ = _proj_moment(ld.get("mx",0), ld.get("my",0), ld.get("mz",0), e1, e2, e3)
            nj_T += mt

    # Cargas pontuais ao longo da barra: (t_norm, N_local, Vy_local, Vz_local)
    bar_pts = []
    for ld in bar.loads:
        if ld.get("type") == "point":
            d = ld.get("distance", 0.0)
            tp = min(d / L, 1.0) if L > 0 else 0.0
            fn, fvy, fvz = _proj_force(ld.get("vx",0), ld.get("vy",0), ld.get("vz",0), e1, e2, e3)
            bar_pts.append((tp, fn, fvy, fvz))

    # Cargas distribuídas: (expr, dN, dVy, dVz)
    dist_lds = []
    for ld in bar.loads:
        if ld.get("type") == "dist":
            dn, dvy, dvz = _dist_local(ld.get("direction","vy"), e1, e2, e3)
            dist_lds.append((ld.get("expr","0"), dn, dvy, dvz))

    def _dist_integral(t, dn, dvy, dvz, expr):
        """Integral numérica de carga distribuída de 0 a t·L (resultado em kN)."""
        if t <= 0:
            return 0.0, 0.0, 0.0
        N_STEPS = 30
        dt = t / N_STEPS
        sn = svy = svz = 0.0
        for k in range(N_STEPS):
            t_mid = (k + 0.5) * dt
            try:
                w = eval_expr(expr, t_mid)
            except Exception:
                w = 0.0
            sn  += w * dn  * dt * L
            svy += w * dvy * dt * L
            svz += w * dvz * dt * L
        return sn, svy, svz

    # ── esforços pelo método das seções (secção à esquerda) ──────────────

    def N(t):
        total = ni_N
        for tp, fn, fvy, fvz in bar_pts:
            if tp <= t:
                total += fn
        for expr, dn, dvy, dvz in dist_lds:
            sn, _, _ = _dist_integral(t, dn, dvy, dvz, expr)
            total += sn
        return -total  # esforço interno = –somatório do lado esquerdo (tração positiva)

    def Vy(t):
        total = ni_Vy
        for tp, fn, fvy, fvz in bar_pts:
            if tp <= t:
                total += fvy
        for expr, dn, dvy, dvz in dist_lds:
            _, svy, _ = _dist_integral(t, dn, dvy, dvz, expr)
            total += svy
        return -total

    def Vz(t):
        total = ni_Vz
        for tp, fn, fvy, fvz in bar_pts:
            if tp <= t:
                total += fvz
        for expr, dn, dvy, dvz in dist_lds:
            _, _, svz = _dist_integral(t, dn, dvy, dvz, expr)
            total += svz
        return -total

    def T(t):
        """Torção: momentos nos dois nós projetados no eixo axial.
        ni_T entra para t > 0; nj_T entra apenas em t = 1 (está à direita das secções internas)."""
        total = ni_T
        if t >= 1.0:
            total += nj_T
        return -total

    # Pré-computar arrays para integração trapezoidal de My e Mz
    NS = 101
    ts = [k / (NS - 1) for k in range(NS)]
    N_arr  = [N(t)  for t in ts]
    Vy_arr = [Vy(t) for t in ts]
    Vz_arr = [Vz(t) for t in ts]
    T_arr  = [T(t)  for t in ts]

    # My e Mz: integração da parte CONTÍNUA (sem cargas concentradas pontuais)
    # via regra dos trapézios, acrescida de contribuições de rampa EXATAS para
    # cada carga concentrada. Isso elimina o erro de ~½·F·dt·L que a regra dos
    # trapézios introduz ao cruzar a descontinuidade em Vy/Vz.
    def _Vy_smooth(t):
        """Vy sem as cargas pontuais da barra (parte contínua, integrável sem erro)."""
        total = ni_Vy
        for expr, dn, dvy, dvz in dist_lds:
            _, svy, _ = _dist_integral(t, dn, dvy, dvz, expr)
            total += svy
        return -total

    def _Vz_smooth(t):
        total = ni_Vz
        for expr, dn, dvy, dvz in dist_lds:
            _, _, svz = _dist_integral(t, dn, dvy, dvz, expr)
            total += svz
        return -total

    Vy_s = [_Vy_smooth(t) for t in ts]
    Vz_s = [_Vz_smooth(t) for t in ts]

    My_arr = [-ni_My]
    Mz_arr = [-ni_Mz]
    for k in range(1, NS):
        dt = ts[k] - ts[k-1]
        My_arr.append(My_arr[-1] + 0.5 * (Vz_s[k-1] + Vz_s[k]) * dt * L)
        Mz_arr.append(Mz_arr[-1] + 0.5 * (Vy_s[k-1] + Vy_s[k]) * dt * L)

    # Adicionar contribuição exata de momento das cargas concentradas:
    # Mz += (−Vy_local) × (t − tp) × L  para t > tp  (rampa linear exata)
    for tp, fn, fvy, fvz in bar_pts:
        for k, t in enumerate(ts):
            if t > tp:
                Mz_arr[k] += (-fvy) * (t - tp) * L
                My_arr[k] += (-fvz) * (t - tp) * L

    def _interp(arr, t):
        i = min(int(t * (NS - 1)), NS - 2)
        frac = t * (NS - 1) - i
        return arr[i] + frac * (arr[i+1] - arr[i])

    def My(t): return _interp(My_arr, t)
    def Mz(t): return _interp(Mz_arr, t)

    N_max  = max(N_arr,  key=abs)
    Vy_max = max(Vy_arr, key=abs)
    Vz_max = max(Vz_arr, key=abs)
    My_max = max(My_arr, key=abs)
    Mz_max = max(Mz_arr, key=abs)
    T_max  = max(T_arr,  key=abs)

    bar.results.update({
        'N_func': N, 'Vy_func': Vy, 'Vz_func': Vz,
        'My_func': My, 'Mz_func': Mz, 'T_func': T,
        'N': N_max, 'Vy': Vy_max, 'Vz': Vz_max,
        'My': My_max, 'Mz': Mz_max, 'T': T_max,
        'axial': N_max,
        'shear': (Vy_max**2 + Vz_max**2)**0.5,
        'moment': (My_max**2 + Mz_max**2)**0.5,
    })
    return bar.results


class Solver:
    def __init__(self, nodes, bars, loads):
        self.nodes = nodes
        self.bars = bars
        self.loads = loads

    def analyze_structure(self): pass

    def get_results(self):
        return {"nodes": self.nodes, "bars": self.bars, "loads": self.loads}
