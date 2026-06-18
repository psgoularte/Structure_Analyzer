"""
Unit tests for the structural solver.
All expected values are derived from closed-form analytical solutions.

Sign convention used throughout:
  N > 0  → tension
  Vy, Vz → local shear (method of sections, left side)
  Mz(t) = Mz(0) + ∫₀ᵗ Vy(s)·L·ds
  My(t) = My(0) + ∫₀ᵗ Vz(s)·L·ds
  T      → torsion, constant for concentrated nodal moments
"""
import math
import pytest
from src.pef_analyzer.core.node import Node
from src.pef_analyzer.core.bar import Bar
from src.pef_analyzer.core.solver import compute_bar_results


# ─── helper ───────────────────────────────────────────────────────────────────

def make(x0, y0, z0, x1, y1, z1,
         ni_loads=None, nj_loads=None, bar_loads=None):
    """Create a bar from (x0,y0,z0) to (x1,y1,z1) and run the solver."""
    n0, n1 = Node(0, x0, y0, z0), Node(1, x1, y1, z1)
    if ni_loads:
        n0.loads = ni_loads
    if nj_loads:
        n1.loads = nj_loads
    b = Bar(0, 0, 1, 1.0, 210e9)
    if bar_loads:
        b.loads = bar_loads
    compute_bar_results(b, [n0, n1])
    return b


def N(b, t):   return b.results['N_func'](t)
def Vy(b, t):  return b.results['Vy_func'](t)
def Vz(b, t):  return b.results['Vz_func'](t)
def My(b, t):  return b.results['My_func'](t)
def Mz(b, t):  return b.results['Mz_func'](t)
def T(b, t):   return b.results['T_func'](t)


# ══════════════════════════════════════════════════════════════════════════════
# 1 — Pure axial
# ══════════════════════════════════════════════════════════════════════════════

class TestAxial:
    def test_tension_single_node_force(self):
        # Pulling force +x at node i → bar is in compression from the left-method perspective
        # Force vx=+50 at i: ni_N=50, N=-50 (left end pushes right → compression)
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":50,"vy":0,"vz":0}])
        assert N(b, 0.5) == pytest.approx(-50, abs=0.1)

    def test_compression_pair(self):
        # Symmetric tension pair: -50 at i, +50 at j → N = +50 (tension)
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":-50,"vy":0,"vz":0}],
                 nj_loads=[{"type":"point","vx":50,"vy":0,"vz":0}])
        assert N(b, 0.5) == pytest.approx(50, abs=0.1)

    def test_N_constant_along_bar_no_distributed(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":30,"vy":0,"vz":0}])
        assert N(b, 0.0) == pytest.approx(N(b, 0.5), abs=0.01)
        assert N(b, 0.5) == pytest.approx(N(b, 1.0), abs=0.01)

    def test_zero_load_gives_zero_N(self):
        b = make(0,0,0, 10,0,0)
        assert N(b, 0.5) == pytest.approx(0.0, abs=1e-9)

    def test_angled_bar_N_from_axial_component(self):
        # Bar at 45° in XY; force vy=100 at i → axial component = 100 * sin(45°)
        b = make(0,0,0, 10,10,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}])
        expected_N = -100 * math.sin(math.radians(45))
        assert N(b, 0.5) == pytest.approx(expected_N, abs=0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 2 — Shear Vy and bending Mz (horizontal bar, transverse vy loads)
# ══════════════════════════════════════════════════════════════════════════════

class TestShearAndBendingMz:
    """
    Simply supported beam pattern: reaction Ra at node i, load applied by the
    user.  Solver does NOT compute reactions; tests supply Ra as a node load.
    """

    def test_simply_supported_uniform_load(self):
        # w = 10 kN/m, L = 10 m, Ra = Rb = 50 kN
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":50,"vz":0}],
                 bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        assert Vy(b, 0.0) == pytest.approx(-50, abs=0.1)
        assert Vy(b, 0.5) == pytest.approx(0,   abs=0.1)
        assert Vy(b, 1.0) == pytest.approx(50,  abs=0.1)
        assert Mz(b, 0.0) == pytest.approx(0,    abs=0.1)
        assert Mz(b, 0.5) == pytest.approx(-125, abs=0.5)  # wL²/8 = 10·100/8 = 125
        assert Mz(b, 1.0) == pytest.approx(0,    abs=1.0)

    def test_midspan_concentrated_load(self):
        # P=100 kN at midspan; Ra=100 at i
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}],
                 bar_loads=[{"type":"point","vx":0,"vy":-100,"vz":0,"distance":5.0}])
        assert Vy(b, 0.25) == pytest.approx(-100, abs=0.1)
        assert Vy(b, 0.75) == pytest.approx(0,    abs=0.1)
        # Mz peak at midspan = P·L/4 = 100·10/4 = 250... wait
        # With Ra=100 at i, load -100 at d=5: reaction at j = 0. Mz at t=0.5:
        # = integral of Vy * L * dt from 0 to 0.5 = (-100)*5*1 = -500 kN·m
        assert Mz(b, 0.5) == pytest.approx(-500, abs=0.5)
        assert Mz(b, 1.0) == pytest.approx(-500, abs=0.5)  # no more load to the right

    def test_two_point_loads(self):
        # P1=60 at d=3, P2=40 at d=7, Ra=100 at i
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}],
                 bar_loads=[
                     {"type":"point","vx":0,"vy":-60,"vz":0,"distance":3.0},
                     {"type":"point","vx":0,"vy":-40,"vz":0,"distance":7.0},
                 ])
        assert Vy(b, 0.2)  == pytest.approx(-100, abs=0.1)
        assert Vy(b, 0.5)  == pytest.approx(-40,  abs=0.1)
        assert Vy(b, 0.8)  == pytest.approx(0,    abs=0.1)
        assert Mz(b, 0.3)  == pytest.approx(-300, abs=0.5)
        assert Mz(b, 0.7)  == pytest.approx(-460, abs=0.5)

    def test_triangular_load(self):
        # w(t) = -10*t kN/m, L=10 m, total load=50 kN
        # Ra for simply supported (by moment about j): Ra=50/3 ≈ 16.667 kN
        Ra = 50.0 / 3.0
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":Ra,"vz":0}],
                 bar_loads=[{"type":"dist","expr":"-10*t","direction":"vy"}])
        assert Vy(b, 0.0) == pytest.approx(-Ra,     abs=0.3)
        assert Vy(b, 1.0) == pytest.approx(50 - Ra, abs=0.5)
        # Mz max at t where Vy=0: Ra = 50*t² → t* = sqrt(Ra/50)
        t_star = math.sqrt(Ra / 50)
        mz_expected = -(Ra * t_star - 50 * t_star**3 / 3) * 10
        assert Mz(b, t_star) == pytest.approx(mz_expected, abs=2.0)

    def test_uniform_load_no_reaction_gives_linear_shear(self):
        # Without node reaction: Vy grows proportionally to distributed load
        b = make(0,0,0, 10,0,0,
                 bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        # Vy(t) = -(0 - 10*t*10) = 100t
        assert Vy(b, 0.0) == pytest.approx(0,    abs=0.1)
        assert Vy(b, 0.5) == pytest.approx(100*0.5, abs=0.5)
        assert Vy(b, 1.0) == pytest.approx(100,  abs=0.5)

    def test_mz_zero_everywhere_for_pure_axial(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":50,"vy":0,"vz":0}])
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert Mz(b, t) == pytest.approx(0, abs=1e-6)

    def test_mz_zero_at_both_ends_for_simply_supported(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":50,"vz":0}],
                 bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        assert Mz(b, 0.0) == pytest.approx(0, abs=0.01)
        assert Mz(b, 1.0) == pytest.approx(0, abs=1.5)

    def test_nodal_moment_at_i_shifts_mz_baseline(self):
        # Apply a bending moment Mz=200 kN·m at node i (global Z axis)
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"moment","mx":0,"my":0,"mz":200}])
        # Mz(0) = -ni_Mz = -200
        assert Mz(b, 0.0) == pytest.approx(-200, abs=0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 3 — Shear Vz and bending My
# ══════════════════════════════════════════════════════════════════════════════

class TestShearAndBendingMy:
    def test_uniform_vz_load(self):
        # Same as Vy test but in local z direction
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":0,"vz":40}],
                 bar_loads=[{"type":"dist","expr":"-8","direction":"vz"}])
        assert Vz(b, 0.0) == pytest.approx(-40, abs=0.1)
        assert Vz(b, 0.5) == pytest.approx(0,   abs=0.3)
        assert Vz(b, 1.0) == pytest.approx(40,  abs=0.3)
        # My(0.5) = -(40*0.5 - 4*0.25)*10 = -(20 - 1)*10 ... let's compute:
        # My(t) = integral of Vz*L*dt = integral of -(40-80s)*10*ds from 0 to t
        #       = -10*(40t - 40t^2)
        # My(0.5) = -10*(20 - 10) = -100
        assert My(b, 0.5) == pytest.approx(-100, abs=1.0)

    def test_my_zero_for_pure_vy_load(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":50,"vz":0}],
                 bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert My(b, t) == pytest.approx(0, abs=1e-6)


# ══════════════════════════════════════════════════════════════════════════════
# 4 — Torsion T
# ══════════════════════════════════════════════════════════════════════════════

class TestTorsion:
    def test_mx_at_node_i_horizontal_bar(self):
        # Bar along X; Mx at node i → T = -Mx constant
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"moment","mx":30,"my":0,"mz":0}])
        for t in [0.0, 0.25, 0.5, 0.75]:
            assert T(b, t) == pytest.approx(-30, abs=0.01)

    def test_mx_at_node_j_appears_at_end(self):
        # Mx at j → T = 0 for t < 1, jumps at t = 1
        b = make(0,0,0, 10,0,0,
                 nj_loads=[{"type":"moment","mx":15,"my":0,"mz":0}])
        assert T(b, 0.5) == pytest.approx(0, abs=0.01)
        assert T(b, 1.0) == pytest.approx(-15, abs=0.01)
        assert abs(b.results['T']) == pytest.approx(15, abs=0.01)

    def test_mz_on_x_bar_gives_zero_torsion(self):
        # Mz (bending moment) on bar aligned with X → no torsion
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"moment","mx":0,"my":0,"mz":50}])
        assert T(b, 0.5) == pytest.approx(0, abs=1e-9)

    def test_my_on_x_bar_gives_zero_torsion(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"moment","mx":0,"my":50,"mz":0}])
        assert T(b, 0.5) == pytest.approx(0, abs=1e-9)

    def test_mx_on_y_aligned_bar_gives_zero_torsion(self):
        # Bar along Y; Mx = global X moment → perpendicular to bar axis → no T
        b = make(0,0,0, 0,10,0,
                 ni_loads=[{"type":"moment","mx":30,"my":0,"mz":0}])
        assert T(b, 0.5) == pytest.approx(0, abs=1e-9)

    def test_my_on_y_bar_gives_torsion(self):
        # Bar along Y; My = global Y moment → aligned with bar → T = -My
        b = make(0,0,0, 0,10,0,
                 ni_loads=[{"type":"moment","mx":0,"my":25,"mz":0}])
        assert T(b, 0.5) == pytest.approx(-25, abs=0.01)

    def test_zero_moment_zero_torsion(self):
        b = make(0,0,0, 10,0,0)
        assert T(b, 0.5) == pytest.approx(0, abs=1e-9)


# ══════════════════════════════════════════════════════════════════════════════
# 5 — Local coordinate system (non-horizontal bars)
# ══════════════════════════════════════════════════════════════════════════════

class TestLocalAxes:
    def test_vertical_bar_global_vy_is_local_N(self):
        # Bar from (0,0,0) to (0,10,0) — e1 = Y; global vy=100 → N=-100
        b = make(0,0,0, 0,10,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}])
        assert N(b, 0.5) == pytest.approx(-100, abs=0.5)
        assert Vy(b, 0.5) == pytest.approx(0, abs=0.5)
        assert Vz(b, 0.5) == pytest.approx(0, abs=0.5)

    def test_45deg_bar_force_split_equally(self):
        # Bar at 45° in XY; vertical force Fy=100 at i
        # e1 = (1/√2, 1/√2, 0), e2 ≈ (−1/√2, 1/√2, 0)... let's check Gram-Schmidt
        # dot(Fy, e1) = 100*(1/√2) = 70.71 → ni_N = 70.71, N = -70.71
        # dot(Fy, e2) ≈ 100*(1/√2) = 70.71 → ni_Vy ≈ 70.71, Vy ≈ -70.71
        b = make(0,0,0, 10,10,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}])
        s2 = 100 / math.sqrt(2)
        assert N(b, 0.5)  == pytest.approx(-s2, abs=1.0)
        assert Vy(b, 0.5) == pytest.approx(-s2, abs=1.0)

    def test_bar_parallel_to_z(self):
        # Bar from (0,0,0) to (0,0,10); e1=Z; global vz=80 at i → N=-80
        b = make(0,0,0, 0,0,10,
                 ni_loads=[{"type":"point","vx":0,"vy":0,"vz":80}])
        assert N(b, 0.5) == pytest.approx(-80, abs=0.5)

    def test_perpendicular_direction_uses_local_e2(self):
        # For a horizontal bar (e1=X), "perpendicular"=e2=Y
        # This should behave identically to direction="vy"
        Ra = 50.0
        b_perp = make(0,0,0, 10,0,0,
                      ni_loads=[{"type":"point","vx":0,"vy":Ra,"vz":0}],
                      bar_loads=[{"type":"dist","expr":"-10","direction":"perpendicular"}])
        b_vy   = make(0,0,0, 10,0,0,
                      ni_loads=[{"type":"point","vx":0,"vy":Ra,"vz":0}],
                      bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert Vy(b_perp, t) == pytest.approx(Vy(b_vy, t), abs=0.5)
            assert Mz(b_perp, t) == pytest.approx(Mz(b_vy, t), abs=1.0)


# ══════════════════════════════════════════════════════════════════════════════
# 6 — Combined loads
# ══════════════════════════════════════════════════════════════════════════════

class TestCombinedLoads:
    def test_axial_plus_transverse_decoupled(self):
        # N and Vy should be independent for a horizontal bar
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":50,"vy":100,"vz":0}])
        assert N(b, 0.5)  == pytest.approx(-50,  abs=0.1)
        assert Vy(b, 0.5) == pytest.approx(-100, abs=0.1)
        assert Vz(b, 0.5) == pytest.approx(0,    abs=0.1)

    def test_multiple_point_loads_accumulate(self):
        # Two loads at different positions along bar
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":150,"vz":0}],
                 bar_loads=[
                     {"type":"point","vx":0,"vy":-100,"vz":0,"distance":4.0},
                     {"type":"point","vx":0,"vy":-50, "vz":0,"distance":8.0},
                 ])
        assert Vy(b, 0.3) == pytest.approx(-150, abs=0.1)  # before both loads
        assert Vy(b, 0.5) == pytest.approx(-50,  abs=0.1)  # after first load
        assert Vy(b, 0.9) == pytest.approx(0,    abs=0.1)  # after both loads

    def test_dist_plus_point_load(self):
        # Uniform dist -10 kN/m + point -50 at midspan; Ra=100 at i
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":100,"vz":0}],
                 bar_loads=[
                     {"type":"dist","expr":"-10","direction":"vy"},
                     {"type":"point","vx":0,"vy":-50,"vz":0,"distance":5.0},
                 ])
        # Vy(0) = -100
        assert Vy(b, 0.0) == pytest.approx(-100, abs=0.1)
        # Vy just after d=5m (at t=0.501, 0.01m past the point load): ≈ 0
        # At t=0.501: dist integral=-10*5.01=-50.1, so Vy=-(100-50.1-50)=0.1
        assert Vy(b, 0.501) == pytest.approx(0, abs=0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 7 — Results dict populated correctly
# ══════════════════════════════════════════════════════════════════════════════

class TestResultsDict:
    def test_all_keys_present(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":50,"vz":0}])
        for key in ("N","Vy","Vz","My","Mz","T",
                    "N_func","Vy_func","Vz_func","My_func","Mz_func","T_func",
                    "axial","shear","moment"):
            assert key in b.results, f"Missing key: {key}"

    def test_max_values_match_function_max(self):
        b = make(0,0,0, 10,0,0,
                 ni_loads=[{"type":"point","vx":0,"vy":80,"vz":0}],
                 bar_loads=[{"type":"dist","expr":"-10","direction":"vy"}])
        ts = [i/100 for i in range(101)]
        vy_max = max(abs(b.results['Vy_func'](t)) for t in ts)
        assert abs(b.results['Vy']) == pytest.approx(vy_max, abs=0.5)

    def test_empty_bar_zero_results(self):
        b = make(0,0,0, 10,0,0)
        assert b.results['N']  == pytest.approx(0, abs=1e-9)
        assert b.results['Vy'] == pytest.approx(0, abs=1e-9)
        assert b.results['T']  == pytest.approx(0, abs=1e-9)
