"""
Representação de carga. Para cargas definidas por função, 'expr' é uma expressão em python em termos de t (posição normalizada 0..1).
Ex: '100 * t' ou '50' (constante). Avaliação feita em ambiente restrito com math.
"""
from typing import Optional, Dict, Any
import math

_SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}


def eval_expr(expr: str, t: float) -> float:
    # avalia expressão simples em ambiente controlado
    try:
        val = eval(expr, {"__builtins__": {}}, {**_SAFE_MATH, "t": t})
        return float(val)
    except Exception:
        return 0.0


def make_point_load(vx=0.0, vy=0.0, vz=0.0, expr: Optional[str] = None) -> Dict[str, Any]:
    return {"type": "point", "vx": float(vx), "vy": float(vy), "vz": float(vz), "expr": expr}


def make_dist_load(expr: str, direction: str = "vy") -> Dict[str, Any]:
    # expr é função de t (0..1)
    return {"type": "dist", "expr": expr, "direction": direction}


class Load:
    def __init__(self, magnitude, direction, position):
        self.magnitude = magnitude
        self.direction = direction
        self.position = position

    def __repr__(self):
        return f"Load(magnitude={self.magnitude}, direction={self.direction}, position={self.position})"

    def apply_load(self):
        # Logic to apply the load to the structure
        pass

    def get_load_info(self):
        return {
            "magnitude": self.magnitude,
            "direction": self.direction,
            "position": self.position
        }