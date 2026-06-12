"""
Node model (3D coordinates, suportes e cargas nodais).
"""
from typing import List, Dict, Any


class Node:
    def __init__(self, nid: int, x: float, y: float, z: float = 0.0):
        self.id = nid
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        # suportes: 'none', 'roller', 'pinned', 'fixed' — representação simples
        self.support = 'none'
        # cargas nodais (lista de dicts): {'type':'point','vx':..., 'vy':..., 'vz':..., 'func': optional str}
        self.loads: List[Dict[str, Any]] = []

    def as_tuple(self):
        return (self.x, self.y, self.z)