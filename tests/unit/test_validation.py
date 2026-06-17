"""
Unit tests for input validation: load expressions, canvas add_* guards, and
the controls field-level helpers (_try_float / _try_int / _try_expr).
"""
import pytest
from src.pef_analyzer.core.load import validate_expr, eval_expr
from src.pef_analyzer.core.node import Node
from src.pef_analyzer.core.bar import Bar
from src.pef_analyzer.core.solver import compute_bar_results


# ─── helpers ──────────────────────────────────────────────────────────────────

def _two_node_canvas():
    """Return a Canvas-like object (just nodes + bars lists) with two valid nodes."""
    from src.pef_analyzer.gui.widgets.canvas import Canvas
    class FakeCanvas:
        def __init__(self):
            self.nodes = [Node(0, 0, 0, 0), Node(1, 10, 0, 0)]
            self.bars = []
        def _recalculate_all_efforts(self): pass
        def _ensure_view_fit(self): pass
        def update(self): pass
        # delegate to real Canvas methods — these become bound methods on instances
        add_bar              = Canvas.add_bar
        add_support          = Canvas.add_support
        add_point_load       = Canvas.add_point_load
        add_dist_load_to_bar = Canvas.add_dist_load_to_bar
        add_node_moment      = Canvas.add_node_moment
    return FakeCanvas()


# ══════════════════════════════════════════════════════════════════════════════
# validate_expr
# ══════════════════════════════════════════════════════════════════════════════

class TestValidateExpr:
    # ── valid expressions ──────────────────────────────────────────────────────

    def test_constant(self):
        assert validate_expr("10") == "10"

    def test_linear_in_t(self):
        assert validate_expr("10*t") == "10*t"

    def test_quadratic(self):
        assert validate_expr("5*t**2 + 3*t - 1") == "5*t**2 + 3*t - 1"

    def test_math_functions_allowed(self):
        assert validate_expr("sin(t)") == "sin(t)"
        assert validate_expr("cos(pi*t)") == "cos(pi*t)"
        assert validate_expr("sqrt(t+0.001)") == "sqrt(t+0.001)"
        assert validate_expr("exp(-t)") == "exp(-t)"
        assert validate_expr("log(t+1)") == "log(t+1)"

    def test_negative_constant(self):
        assert validate_expr("-50") == "-50"

    def test_float_literal(self):
        assert validate_expr("3.14") == "3.14"

    def test_whitespace_stripped(self):
        assert validate_expr("  10*t  ") == "10*t"

    def test_combined(self):
        assert validate_expr("100*(1-t)") == "100*(1-t)"

    # ── invalid expressions ────────────────────────────────────────────────────

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_expr("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_expr("   ")

    def test_import_raises(self):
        with pytest.raises(ValueError):
            validate_expr("import os")

    def test_undefined_variable_raises(self):
        with pytest.raises(ValueError):
            validate_expr("x + 1")

    def test_syntax_error_raises(self):
        with pytest.raises(ValueError):
            validate_expr("10 + * t")

    def test_incomplete_expression_raises(self):
        with pytest.raises(ValueError):
            validate_expr("10 +")

    def test_builtins_blocked(self):
        with pytest.raises(ValueError):
            validate_expr("__import__('os')")

    def test_open_blocked(self):
        with pytest.raises(ValueError):
            validate_expr("open('/etc/passwd')")

    def test_eval_blocked(self):
        with pytest.raises(ValueError):
            validate_expr("eval('1+1')")


# ══════════════════════════════════════════════════════════════════════════════
# eval_expr  (runtime safe-eval, silently returns 0.0 on error)
# ══════════════════════════════════════════════════════════════════════════════

class TestEvalExpr:
    def test_constant(self):
        assert eval_expr("10", 0.5) == pytest.approx(10.0)

    def test_linear_at_mid(self):
        assert eval_expr("10*t", 0.5) == pytest.approx(5.0)

    def test_linear_at_start(self):
        assert eval_expr("10*t", 0.0) == pytest.approx(0.0)

    def test_linear_at_end(self):
        assert eval_expr("10*t", 1.0) == pytest.approx(10.0)

    def test_negative(self):
        assert eval_expr("-5", 0.5) == pytest.approx(-5.0)

    def test_math_sin(self):
        import math
        assert eval_expr("sin(pi*t)", 0.5) == pytest.approx(math.sin(math.pi * 0.5))

    def test_bad_expr_returns_zero(self):
        assert eval_expr("not_a_var", 0.5) == 0.0

    def test_syntax_error_returns_zero(self):
        assert eval_expr("10 +", 0.5) == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Canvas.add_bar validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCanvasAddBar:
    def setup_method(self):
        self.c = _two_node_canvas()

    def test_valid_bar(self):
        bid = self.c.add_bar(0, 1)
        assert bid == 0
        assert len(self.c.bars) == 1

    def test_node_i_out_of_range(self):
        with pytest.raises(ValueError, match="Node 5"):
            self.c.add_bar(5, 1)

    def test_node_j_out_of_range(self):
        with pytest.raises(ValueError, match="Node 99"):
            self.c.add_bar(0, 99)

    def test_negative_node_index(self):
        with pytest.raises(ValueError):
            self.c.add_bar(-1, 1)

    def test_same_node_raises(self):
        with pytest.raises(ValueError, match="different"):
            self.c.add_bar(0, 0)

    def test_zero_length_bar_raises(self):
        self.c.nodes.append(Node(2, 0, 0, 0))   # same position as node 0
        with pytest.raises(ValueError, match="zero length"):
            self.c.add_bar(0, 2)

    def test_no_nodes_raises(self):
        self.c.nodes = []
        with pytest.raises(ValueError):
            self.c.add_bar(0, 1)


# ══════════════════════════════════════════════════════════════════════════════
# Canvas.add_support validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCanvasAddSupport:
    def setup_method(self):
        self.c = _two_node_canvas()

    def test_valid_support_types(self):
        for st in ("none", "roller", "pinned", "fixed"):
            self.c.add_support(0, st)
            assert self.c.nodes[0].support == st

    def test_node_out_of_range(self):
        with pytest.raises(ValueError, match="Node 10"):
            self.c.add_support(10, "fixed")

    def test_invalid_support_type(self):
        with pytest.raises(ValueError, match="not valid"):
            self.c.add_support(0, "spring")

    def test_negative_node_raises(self):
        with pytest.raises(ValueError):
            self.c.add_support(-1, "fixed")


# ══════════════════════════════════════════════════════════════════════════════
# Canvas.add_point_load validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCanvasAddPointLoad:
    def setup_method(self):
        self.c = _two_node_canvas()
        self.c.add_bar(0, 1)   # bar 0, length = 10 m

    def test_valid_load_at_midspan(self):
        self.c.add_point_load(0, vy=-100, distance=5.0)
        assert len(self.c.bars[0].loads) == 1

    def test_valid_load_at_node_i(self):
        self.c.add_point_load(0, vy=-50, distance=0.0)
        assert len(self.c.bars[0].loads) == 1

    def test_valid_load_at_node_j(self):
        self.c.add_point_load(0, vy=-50, distance=10.0)
        assert len(self.c.bars[0].loads) == 1

    def test_bar_out_of_range(self):
        with pytest.raises(ValueError, match="Bar 5"):
            self.c.add_point_load(5, vy=-100)

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="≥ 0"):
            self.c.add_point_load(0, vy=-100, distance=-1.0)

    def test_distance_exceeds_bar_length(self):
        with pytest.raises(ValueError, match="exceeds bar length"):
            self.c.add_point_load(0, vy=-100, distance=15.0)

    def test_distance_just_at_limit_ok(self):
        self.c.add_point_load(0, vy=-100, distance=10.0)  # exactly at end
        assert len(self.c.bars[0].loads) == 1

    def test_no_bars_raises(self):
        fresh = _two_node_canvas()   # no bar added yet
        with pytest.raises(ValueError, match="Bar 0"):
            fresh.add_point_load(0, vy=-100)


# ══════════════════════════════════════════════════════════════════════════════
# Canvas.add_dist_load_to_bar validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCanvasAddDistLoad:
    def setup_method(self):
        self.c = _two_node_canvas()
        self.c.add_bar(0, 1)

    def test_valid_constant(self):
        self.c.add_dist_load_to_bar(0, "10", "vy")
        assert len(self.c.bars[0].loads) == 1

    def test_valid_function_of_t(self):
        self.c.add_dist_load_to_bar(0, "10*t", "vy")
        assert len(self.c.bars[0].loads) == 1

    def test_bar_out_of_range(self):
        with pytest.raises(ValueError, match="Bar 3"):
            self.c.add_dist_load_to_bar(3, "10", "vy")

    def test_invalid_expression(self):
        with pytest.raises(ValueError):
            self.c.add_dist_load_to_bar(0, "import os", "vy")

    def test_empty_expression(self):
        with pytest.raises(ValueError, match="empty"):
            self.c.add_dist_load_to_bar(0, "", "vy")

    def test_unknown_variable(self):
        with pytest.raises(ValueError):
            self.c.add_dist_load_to_bar(0, "x + 1", "vy")


# ══════════════════════════════════════════════════════════════════════════════
# Canvas.add_node_moment validation
# ══════════════════════════════════════════════════════════════════════════════

class TestCanvasAddNodeMoment:
    def setup_method(self):
        self.c = _two_node_canvas()

    def test_valid_moment(self):
        self.c.add_node_moment(0, mx=10, my=0, mz=0)
        assert len(self.c.nodes[0].loads) == 1

    def test_node_out_of_range(self):
        with pytest.raises(ValueError, match="Node 7"):
            self.c.add_node_moment(7, mx=10)

    def test_negative_node_raises(self):
        with pytest.raises(ValueError):
            self.c.add_node_moment(-1, mx=10)
