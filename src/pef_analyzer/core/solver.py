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
import numpy as np


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
    def __init__(self, nodes, bars):
        self.nodes = nodes
        self.bars = bars
        self.ndof = len(nodes) * 6  # 6 graus de liberdade por nó
        self.K = np.zeros((self.ndof, self.ndof))
        self.F = np.zeros(self.ndof)
        self.U = np.zeros(self.ndof)
        self.reactions = np.zeros(self.ndof)

    def _local_stiffness(self, bar, L):
        """Monta a matriz de rigidez 12x12 local da barra 3D."""
        E, G, A = bar.e, bar.g, bar.area
        Iy, Iz, J = bar.iy, bar.iz, bar.j
        k = np.zeros((12, 12))
        
        # Axial
        k[0,0] = k[6,6] = E*A/L
        k[0,6] = k[6,0] = -E*A/L
        
        # Torção
        k[3,3] = k[9,9] = G*J/L
        k[3,9] = k[9,3] = -G*J/L
        
        # Flexão Z (Gera cortante Y)
        k[1,1] = k[7,7] = 12*E*Iz/L**3
        k[1,7] = k[7,1] = -12*E*Iz/L**3
        k[1,5] = k[5,1] = k[1,11] = k[11,1] = 6*E*Iz/L**2
        k[7,5] = k[5,7] = k[7,11] = k[11,7] = -6*E*Iz/L**2
        k[5,5] = k[11,11] = 4*E*Iz/L
        k[5,11] = k[11,5] = 2*E*Iz/L
        
        # Flexão Y (Gera cortante Z)
        k[2,2] = k[8,8] = 12*E*Iy/L**3
        k[2,8] = k[8,2] = -12*E*Iy/L**3
        k[2,4] = k[4,2] = k[2,10] = k[10,2] = -6*E*Iy/L**2
        k[8,4] = k[4,8] = k[8,10] = k[10,8] = 6*E*Iy/L**2
        k[4,4] = k[10,10] = 4*E*Iy/L
        k[4,10] = k[10,4] = 2*E*Iy/L
        
        return k

    def _transformation_matrix(self, ni, nj):
        """Monta a matriz de transformação 12x12 usando os vetores diretores."""
        e1, e2, e3, L = _local_axes(ni, nj)
        
        # Matriz de rotação 3x3
        R = np.array([
            [e1[0], e1[1], e1[2]],
            [e2[0], e2[1], e2[2]],
            [e3[0], e3[1], e3[2]]
        ])
        
        # Expandindo para 12x12
        T = np.zeros((12, 12))
        T[0:3, 0:3] = R
        T[3:6, 3:6] = R
        T[6:9, 6:9] = R
        T[9:12, 9:12] = R
        return T, L
    
    def _equivalent_nodal_forces(self, bar, L, T):
        """Calcula as forças nodais equivalentes convertendo de coordenadas Globais para Locais."""
        f_local = np.zeros(12)
        R = T[0:3, 0:3] # Extrai a matriz de rotação 3x3 (Global -> Local)
        
        for ld in bar.loads:
            if ld.get("type") == "point":
                d = ld.get("distance", 0.0)
                a = max(0.0, min(d, L))
                b = L - a
                
                # A carga do usuário é Global. Convertendo para eixos Locais da barra:
                f_global = np.array([ld.get("vx", 0), ld.get("vy", 0), ld.get("vz", 0)])
                f_loc = R @ f_global
                vx, vy, vz = f_loc[0], f_loc[1], f_loc[2]
                
                if L > 0:
                    # Direção X local (Força Axial)
                    f_local[0] += vx * (b/L)
                    f_local[6] += vx * (a/L)
                    
                    # Direção Y local (Gera Cortante Y e Flexão Z)
                    f_local[1] += vy * (b**2)*(3*a + b)/(L**3)
                    f_local[5] += vy * a * (b**2)/(L**2)
                    f_local[7] += vy * (a**2)*(a + 3*b)/(L**3)
                    f_local[11] -= vy * (a**2)*b/(L**2)
                    
                    # Direção Z local (Gera Cortante Z e Flexão Y)
                    f_local[2] += vz * (b**2)*(3*a + b)/(L**3)
                    f_local[4] -= vz * a * (b**2)/(L**2)
                    f_local[8] += vz * (a**2)*(a + 3*b)/(L**3)
                    f_local[10] += vz * (a**2)*b/(L**2)

            elif ld.get("type") == "dist":
                from .load import eval_expr
                expr = ld.get("expr", "0")
                direction = ld.get("direction", "vy")
                
                try:
                    w_mag = eval_expr(expr, 0.5)
                except Exception:
                    w_mag = 0.0
                
                # Mapeando direção e projetando para Local
                dirs = {"vx": (1,0,0), "vy": (0,1,0), "vz": (0,0,1)}
                if direction == "perpendicular":
                    w_loc = np.array([0, w_mag, 0]) # Aplica direto no eixo Y local
                else:
                    g_vec = np.array(dirs.get(direction, (0,1,0))) * w_mag
                    w_loc = R @ g_vec # Projeta vetor global para eixos da barra
                
                wx, wy, wz = w_loc[0], w_loc[1], w_loc[2]
                
                if L > 0:
                    # Distribuição Axial
                    f_local[0] += wx * L / 2
                    f_local[6] += wx * L / 2
                    
                    # Distribuição Transversal Y
                    f_local[1] += wy * L / 2
                    f_local[5] += wy * L**2 / 12
                    f_local[7] += wy * L / 2
                    f_local[11] -= wy * L**2 / 12
                    
                    # Distribuição Transversal Z
                    f_local[2] += wz * L / 2
                    f_local[4] -= wz * L**2 / 12
                    f_local[8] += wz * L / 2
                    f_local[10] += wz * L**2 / 12

        return T.T @ f_local

    def assemble_system(self):
        """Costura as matrizes locais na matriz global e monta o vetor de forças nodais."""
        self.K.fill(0.0)
        self.F.fill(0.0)
        
        # 1. Montagem da Matriz de Rigidez Global (K) e Forças Equivalentes
        for bar in self.bars:
            ni = self.nodes[bar.node_i]
            nj = self.nodes[bar.node_j]
            
            T, L = self._transformation_matrix(ni, nj)
            k_local = self._local_stiffness(bar, L)
            k_glob = T.T @ k_local @ T
            
            # --- MUDANÇA: Calculando forças na barra e jogando para os nós ---
            f_enf = self._equivalent_nodal_forces(bar, L, T)
            
            dof_i = [bar.node_i * 6 + d for d in range(6)]
            dof_j = [bar.node_j * 6 + d for d in range(6)]
            dofs = dof_i + dof_j
            
            for r in range(12):
                self.F[dofs[r]] += f_enf[r]  # Adiciona ao vetor de forças globais
                for c in range(12):
                    self.K[dofs[r], dofs[c]] += k_glob[r, c]

        # 2. Montagem do Vetor de Forças Externas (F) apenas para cargas diretamente nos nós
        for n in self.nodes:
            idx = n.id * 6
            for ld in n.loads:
                if ld.get("type") == "point" and not ld.get("is_reaction", False):
                    self.F[idx] += ld.get("vx", 0)
                    self.F[idx+1] += ld.get("vy", 0)
                    self.F[idx+2] += ld.get("vz", 0)
                elif ld.get("type") == "moment" and not ld.get("is_reaction", False):
                    self.F[idx+3] += ld.get("mx", 0)
                    self.F[idx+4] += ld.get("my", 0)
                    self.F[idx+5] += ld.get("mz", 0)

    def apply_boundaries_and_solve(self):
        """Aplica os apoios, resolve o sistema e calcula as reações."""
        K_mod = self.K.copy()
        F_mod = self.F.copy()
        
        # 1. Identificar nós ativos (que possuem pelo menos uma barra conectada)
        active_nodes = set()
        for bar in self.bars:
            active_nodes.add(bar.node_i)
            active_nodes.add(bar.node_j)

        # Mapeando os travamentos dos apoios
        fixed_dofs = []
        for n in self.nodes:
            idx = n.id * 6
            
            # --- BLINDAGEM: Nó sem barra conectada ---
            # Trava o nó inteiro na matriz para evitar "Singular Matrix" (divisão por zero)
            if n.id not in active_nodes:
                fixed_dofs.extend([idx, idx+1, idx+2, idx+3, idx+4, idx+5])
                continue
                
            if n.support == "fixed":
                fixed_dofs.extend([idx, idx+1, idx+2, idx+3, idx+4, idx+5])
            elif n.support == "pinned":
                fixed_dofs.extend([idx, idx+1, idx+2, idx+3, idx+4]) 
            elif n.support == "roller":
                fixed_dofs.extend([idx+1, idx+2, idx+3, idx+4])

        # Modificando a matriz para forçar deslocamento zero nos apoios
        for dof in fixed_dofs:
            K_mod[dof, :] = 0.0
            K_mod[:, dof] = 0.0
            K_mod[dof, dof] = 1.0
            F_mod[dof] = 0.0
            
        # ... O resto do método continua igual para baixo (Resolvendo o sistema e as reações) ...
        try:
            self.U = np.linalg.solve(K_mod, F_mod)
        except np.linalg.LinAlgError:
            print("ERRO CRÍTICO: Estrutura instável (Matriz Singular). A estrutura é um mecanismo.")
            return

        self.reactions = (self.K @ self.U) - self.F

        for n in self.nodes:
            idx = n.id * 6
            rx, ry, rz = self.reactions[idx], self.reactions[idx+1], self.reactions[idx+2]
            rmx, rmy, rmz = self.reactions[idx+3], self.reactions[idx+4], self.reactions[idx+5]
            
            if abs(rx) > 1e-6 or abs(ry) > 1e-6 or abs(rz) > 1e-6:
                n.loads.append({"type": "point", "vx": rx, "vy": ry, "vz": rz, "is_reaction": True})
            if abs(rmx) > 1e-6 or abs(rmy) > 1e-6 or abs(rmz) > 1e-6:
                n.loads.append({"type": "moment", "mx": rmx, "my": rmy, "mz": rmz, "is_reaction": True})

    def analyze_structure(self):
        """Função principal que orquestra a análise."""
        # Limpa reações anteriores caso o usuário analise duas vezes
        for n in self.nodes:
            n.loads = [ld for ld in n.loads if not ld.get("is_reaction", False)]
            
        self.assemble_system()
        self.apply_boundaries_and_solve()
        
        # Agora que as reações foram aplicadas nos nós, chama o seu método de seções perfeito
        for bar in self.bars:
            compute_bar_results(bar, self.nodes)
