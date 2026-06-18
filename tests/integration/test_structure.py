"""
Integration tests: build structures end-to-end through the Canvas API and
verify that validation, data storage, and solver results are all consistent.
"""
import math
import pytest
from src.pef_analyzer.core.node import Node
from src.pef_analyzer.core.bar import Bar
from src.pef_analyzer.core.solver import compute_bar_results


# ─── lightweight headless canvas ─────────────────────────────────────────────

class HeadlessCanvas:
    """Mimics Canvas API without Qt, using the real validation logic."""
    def __init__(self):
        self.nodes = []
        self.bars  = []

    def _recalculate_all_efforts(self):
        for bar in self.bars:
            compute_bar_results(bar, self.nodes)

    def _ensure_view_fit(self): pass
    def update(self): pass

    from src.pef_analyzer.gui.widgets.canvas import Canvas
    add_node             = Canvas.add_node
    add_bar              = Canvas.add_bar
    add_support          = Canvas.add_support
    add_point_load       = Canvas.add_point_load
    add_dist_load_to_bar = Canvas.add_dist_load_to_bar
    add_node_moment      = Canvas.add_node_moment
    clear_structure      = Canvas.clear_structure


@pytest.fixture
def canvas():
    return HeadlessCanvas()


# ══════════════════════════════════════════════════════════════════════════════
# Basic structure construction
# ══════════════════════════════════════════════════════════════════════════════

class TestStructureConstruction:
    def test_add_single_node(self, canvas):
        nid = canvas.add_node(0, 0, 0)
        assert nid == 0
        assert len(canvas.nodes) == 1
        assert canvas.nodes[0].x == 0

    def test_add_multiple_nodes(self, canvas):
        for i in range(5):
            canvas.add_node(float(i), 0, 0)
        assert len(canvas.nodes) == 5

    def test_add_bar_after_nodes(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_node(10, 0, 0)
        bid = canvas.add_bar(0, 1)
        assert bid == 0
        assert len(canvas.bars) == 1

    def test_add_bar_before_nodes_raises(self, canvas):
        with pytest.raises(ValueError):
            canvas.add_bar(0, 1)

    def test_clear_resets_everything(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_node(5, 0, 0)
        canvas.add_bar(0, 1)
        canvas.clear_structure()
        assert canvas.nodes == []
        assert canvas.bars == []

    def test_bar_ids_are_sequential(self, canvas):
        for i in range(4):
            canvas.add_node(float(i*5), 0, 0)
        for i in range(3):
            bid = canvas.add_bar(i, i+1)
            assert bid == i

    def test_node_3d_coordinates_stored(self, canvas):
        canvas.add_node(1.5, -2.0, 3.7)
        n = canvas.nodes[0]
        assert n.x == pytest.approx(1.5)
        assert n.y == pytest.approx(-2.0)
        assert n.z == pytest.approx(3.7)


# ══════════════════════════════════════════════════════════════════════════════
# Support assignment
# ══════════════════════════════════════════════════════════════════════════════

class TestSupportAssignment:
    def test_default_support_is_none(self, canvas):
        canvas.add_node(0, 0, 0)
        assert canvas.nodes[0].support == "none"

    def test_assign_fixed(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_support(0, "fixed")
        assert canvas.nodes[0].support == "fixed"

    def test_overwrite_support(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_support(0, "pinned")
        canvas.add_support(0, "fixed")
        assert canvas.nodes[0].support == "fixed"

    def test_invalid_support_type_rejected(self, canvas):
        canvas.add_node(0, 0, 0)
        with pytest.raises(ValueError, match="not valid"):
            canvas.add_support(0, "hinge")


# ══════════════════════════════════════════════════════════════════════════════
# Load assignment
# ══════════════════════════════════════════════════════════════════════════════

class TestLoadAssignment:
    @pytest.fixture(autouse=True)
    def setup(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_node(10, 0, 0)
        canvas.add_bar(0, 1)
        self.c = canvas

    def test_point_load_stored_correctly(self):
        self.c.add_point_load(0, vx=10, vy=-50, vz=5, distance=3.0)
        ld = self.c.bars[0].loads[0]
        assert ld["type"]     == "point"
        assert ld["vy"]       == pytest.approx(-50)
        assert ld["distance"] == pytest.approx(3.0)

    def test_dist_load_stored_correctly(self):
        self.c.add_dist_load_to_bar(0, "10*t", "vy")
        ld = self.c.bars[0].loads[0]
        assert ld["type"]      == "dist"
        assert ld["expr"]      == "10*t"
        assert ld["direction"] == "vy"

    def test_multiple_loads_accumulate(self):
        self.c.add_point_load(0, vy=-100, distance=5.0)
        self.c.add_dist_load_to_bar(0, "-10", "vy")
        assert len(self.c.bars[0].loads) == 2

    def test_node_moment_stored(self):
        self.c.add_node_moment(0, mx=20, my=0, mz=0)
        ld = self.c.nodes[0].loads[0]
        assert ld["type"] == "moment"
        assert ld["mx"]   == pytest.approx(20)

    def test_distance_exactly_zero_ok(self):
        self.c.add_point_load(0, vy=-100, distance=0.0)
        assert len(self.c.bars[0].loads) == 1

    def test_distance_exactly_bar_length_ok(self):
        self.c.add_point_load(0, vy=-100, distance=10.0)
        assert len(self.c.bars[0].loads) == 1


# ══════════════════════════════════════════════════════════════════════════════
# End-to-end calculation results
# ══════════════════════════════════════════════════════════════════════════════

class TestEndToEndCalculations:
    def _build(self):
        c = HeadlessCanvas()
        c.add_node(0, 0, 0)
        c.add_node(10, 0, 0)
        c.add_bar(0, 1)
        return c

    def test_simply_supported_beam_mz_peak(self):
        c = self._build()
        # reaction vy=50 at node i, uniform load -10 kN/m downward
        c.nodes[0].loads = [{"type": "point", "vx": 0, "vy": 50, "vz": 0}]
        c.add_dist_load_to_bar(0, "-10", "vy")
        c._recalculate_all_efforts()
        bar = c.bars[0]
        # wL²/8 = 10·100/8 = 125 kN·m
        assert abs(bar.results['Mz_func'](0.5)) == pytest.approx(125, abs=1.0)

    def test_results_update_after_adding_load(self):
        c = self._build()
        c._recalculate_all_efforts()
        vy_before = c.bars[0].results.get('Vy', 0.0)
        c.nodes[0].loads.append({"type": "point", "vx": 0, "vy": 100, "vz": 0})
        c._recalculate_all_efforts()
        vy_after = c.bars[0].results['Vy_func'](0.5)
        assert abs(vy_after) > abs(vy_before)

    def test_clear_resets_solver_results(self):
        c = self._build()
        c.nodes[0].loads = [{"type": "point", "vx": 0, "vy": 50, "vz": 0}]
        c._recalculate_all_efforts()
        assert c.bars[0].results.get('Vy', 0) != 0
        c.clear_structure()
        assert c.bars == []

    def test_multi_bar_structure(self):
        """Two-bar continuous beam; each bar solved independently."""
        c = HeadlessCanvas()
        c.add_node(0,  0, 0)
        c.add_node(5,  0, 0)
        c.add_node(10, 0, 0)
        c.add_bar(0, 1)
        c.add_bar(1, 2)
        # Load bar 0 only
        c.nodes[0].loads = [{"type": "point", "vx": 0, "vy": 50, "vz": 0}]
        c.add_dist_load_to_bar(0, "-10", "vy")
        c._recalculate_all_efforts()
        # Bar 0 should have non-zero shear
        assert abs(c.bars[0].results['Vy_func'](0.5)) > 1.0
        # Bar 1 has no loads at all
        assert c.bars[1].results['Vy_func'](0.5) == pytest.approx(0, abs=0.1)

    def test_torsion_end_to_end(self):
        c = self._build()
        c.add_node_moment(0, mx=30, my=0, mz=0)
        c._recalculate_all_efforts()
        bar = c.bars[0]
        assert bar.results['T_func'](0.5) == pytest.approx(-30, abs=0.1)
        assert abs(bar.results['T'])       == pytest.approx(30,  abs=0.1)

    def test_3d_bar_effort_decomposition(self):
        """Diagonal bar: a global Vy load projects into both N and Vy locally."""
        c = HeadlessCanvas()
        c.add_node(0, 0, 0)
        c.add_node(10, 10, 0)   # 45° bar
        c.add_bar(0, 1)
        c.nodes[0].loads = [{"type": "point", "vx": 0, "vy": 100, "vz": 0}]
        c._recalculate_all_efforts()
        bar = c.bars[0]
        s2 = 100 / math.sqrt(2)
        assert abs(bar.results['N_func'](0.5))  == pytest.approx(s2, abs=1.0)
        assert abs(bar.results['Vy_func'](0.5)) == pytest.approx(s2, abs=1.0)


# ══════════════════════════════════════════════════════════════════════════════
# Validation error propagation (no Qt needed)
# ══════════════════════════════════════════════════════════════════════════════

class TestValidationErrors:
    @pytest.fixture(autouse=True)
    def setup(self, canvas):
        canvas.add_node(0, 0, 0)
        canvas.add_node(10, 0, 0)
        self.c = canvas

    def test_bar_with_nonexistent_node_raises(self):
        with pytest.raises(ValueError):
            self.c.add_bar(0, 5)

    def test_bar_same_node_raises(self):
        with pytest.raises(ValueError, match="different"):
            self.c.add_bar(1, 1)

    def test_point_load_on_missing_bar_raises(self):
        with pytest.raises(ValueError, match="Bar 0"):
            self.c.add_point_load(0, vy=-100)

    def test_dist_load_on_missing_bar_raises(self):
        with pytest.raises(ValueError, match="Bar 0"):
            self.c.add_dist_load_to_bar(0, "10", "vy")

    def test_moment_on_missing_node_raises(self):
        with pytest.raises(ValueError, match="Node 9"):
            self.c.add_node_moment(9, mx=10)

    def test_negative_distance_on_existing_bar_raises(self):
        self.c.add_bar(0, 1)
        with pytest.raises(ValueError, match="≥ 0"):
            self.c.add_point_load(0, vy=-100, distance=-1.0)

    def test_distance_beyond_bar_length_raises(self):
        self.c.add_bar(0, 1)
        with pytest.raises(ValueError, match="exceeds bar length"):
            self.c.add_point_load(0, vy=-100, distance=20.0)

    def test_invalid_expr_on_bar_raises(self):
        self.c.add_bar(0, 1)
        with pytest.raises(ValueError):
            self.c.add_dist_load_to_bar(0, "x + 1", "vy")

    def test_zero_length_bar_raises(self):
        self.c.add_node(0, 0, 0)   # node 2 at same pos as node 0
        with pytest.raises(ValueError, match="zero length"):
            self.c.add_bar(0, 2)
