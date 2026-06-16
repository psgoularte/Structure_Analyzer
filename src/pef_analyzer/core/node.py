"""
Node model (3D coordinates, suportes e cargas nodais).
Coordinates are in meters (m).
"""
from typing import List, Dict, Any


class Node:
    def __init__(self, nid: int, x: float, y: float, z: float = 0.0):
        self.id = nid
        self.x = float(x)  # x coordinate in meters
        self.y = float(y)  # y coordinate in meters
        self.z = float(z)  # z coordinate in meters
        # suportes: 'none', 'roller', 'pinned', 'fixed' — representação simples
        self.support = 'none'
        # cargas nodais (lista de dicts): {'type':'point','vx':..., 'vy':..., 'vz':..., 'func': optional str}
        self.loads: List[Dict[str, Any]] = []

    def as_tuple(self):
        return (self.x, self.y, self.z)