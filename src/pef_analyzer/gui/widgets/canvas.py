"""
Canvas - Responsável por renderizar o diagrama de forças e restrições.
Inclui pan, zoom e rotação 3D (pitch, yaw, roll), projeção 3D->2D e desenho estético de barras e apoios.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF
from pef_analyzer.core.node import Node
from pef_analyzer.core.bar import Bar
from pef_analyzer.core.solver import compute_bar_results
import math


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)

        # modelo
        self.nodes = []  # list[Node]
        self.bars = []   # list[Bar]

        # visual / transform
        self.base_model_size = 20.0
        self.scale = 1.0
        self.projection_scale = 0.6
        self.pan_x = 0.0
        self.pan_y = 0.0

        # 3-axis rotation angles (graus): pitch = rot X, yaw = rot Y, roll = rot Z
        self.angle_x = 10.0
        self.angle_y = -20.0
        self.angle_z = 0.0

        self._last_mouse_pos = None
        self._mouse_button = None

    # criação via API
    def add_node(self, x: float, y: float, z: float = 0.0) -> int:
        nid = len(self.nodes)
        n = Node(nid, x, y, z)
        self.nodes.append(n)
        self._ensure_view_fit()
        self.update()
        return nid

    def add_bar(self, ni: int, nj: int, area: float = 1.0, e: float = 210e9) -> int:
        bid = len(self.bars)
        b = Bar(bid, ni, nj, area, e)
        self.bars.append(b)
        compute_bar_results(b, self.nodes)
        self._ensure_view_fit()
        self.update()
        return bid

    def add_support(self, node_index: int, support_type: str):
        if 0 <= node_index < len(self.nodes):
            self.nodes[node_index].support = support_type
            self.update()

    def add_point_load(self, node_index: int, vx=0.0, vy=0.0, vz=0.0, expr=None):
        if 0 <= node_index < len(self.nodes):
            self.nodes[node_index].loads.append({"type": "point", "vx": vx, "vy": vy, "vz": vz, "expr": expr})
            for bar in self.bars:
                if bar.node_i == node_index or bar.node_j == node_index:
                    compute_bar_results(bar, self.nodes)
            self.update()

    def add_dist_load_to_bar(self, bar_index: int, expr: str, direction: str = "vy"):
        if 0 <= bar_index < len(self.bars):
            self.bars[bar_index].loads.append({"type": "dist", "expr": expr, "direction": direction})
            compute_bar_results(self.bars[bar_index], self.nodes)
            self.update()

    # view helpers
    def _ensure_view_fit(self):
        w, h = max(1, self.width()), max(1, self.height())
        factor = 1.3
        self.scale = min(w, h) / (self.base_model_size * factor)
        self._center_view()

    def _center_view(self):
        self._cx = self.width() / 2.0
        self._cy = self.height() / 2.0

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._ensure_view_fit()
        self.update()

    # 3D rotation utilities
    def _rotate_point(self, x: float, y: float, z: float):
        # convert degrees to radians
        ax = math.radians(self.angle_x)
        ay = math.radians(self.angle_y)
        az = math.radians(self.angle_z)

        # rotation matrices Rx (pitch), Ry (yaw), Rz (roll)
        # apply in order R = Rz * Ry * Rx (first Rx, then Ry, then Rz)
        # Rx
        cx = math.cos(ax); sx = math.sin(ax)
        x1 = x
        y1 = cx * y - sx * z
        z1 = sx * y + cx * z

        # Ry
        cy = math.cos(ay); sy = math.sin(ay)
        x2 = cy * x1 + sy * z1
        y2 = y1
        z2 = -sy * x1 + cy * z1

        # Rz
        cz = math.cos(az); sz = math.sin(az)
        xr = cz * x2 - sz * y2
        yr = sz * x2 + cz * y2
        zr = z2
        return xr, yr, zr

    def model_to_screen(self, x: float, y: float, z: float) -> QPointF:
        xr, yr, zr = self._rotate_point(x, y, z)
        sx = xr * self.scale
        sy = yr * self.scale
        sy = sy + zr * self.scale * self.projection_scale
        tx = self._cx + sx + self.pan_x
        ty = self._cy - sy + self.pan_y
        return QPointF(tx, ty)

    # interação: pan (left), rotate XY/Z (right), rotate Y (middle), zoom wheel
    def mousePressEvent(self, ev):
        self._last_mouse_pos = ev.position()
        self._mouse_button = ev.button()

    def mouseMoveEvent(self, ev):
        if self._last_mouse_pos is None:
            self._last_mouse_pos = ev.position()
            return
        cur = ev.position()
        dx = cur.x() - self._last_mouse_pos.x()
        dy = cur.y() - self._last_mouse_pos.y()

        if self._mouse_button == Qt.MouseButton.LeftButton:
            self.pan_x += dx
            self.pan_y += dy
            self.update()
        elif self._mouse_button == Qt.MouseButton.RightButton:
            # horizontal -> roll (z), vertical -> pitch (x)
            self.angle_z += dx * 0.4
            self.angle_x += dy * 0.35
            self.angle_x = max(-89.0, min(89.0, self.angle_x))
            self.update()
        elif self._mouse_button == Qt.MouseButton.MiddleButton:
            # middle drag rotates yaw (around Y)
            self.angle_y += dx * 0.4
            self.update()

        self._last_mouse_pos = cur

    def mouseReleaseEvent(self, ev):
        self._last_mouse_pos = None
        self._mouse_button = None

    def wheelEvent(self, ev):
        delta = ev.angleDelta().y() / 120.0
        if abs(delta) < 1e-6:
            return
        factor = 1.12 ** delta
        cursor = ev.position()
        old_scale = self.scale
        self.scale = max(0.02, min(500.0, self.scale * factor))
        mx = (cursor.x() - self._cx - self.pan_x) / old_scale
        my = (self._cy - cursor.y() + self.pan_y) / old_scale
        nx = mx * self.scale
        ny = my * self.scale
        self.pan_x += ((mx * old_scale) - nx)
        self.pan_y += ((-my * old_scale) + ny)
        self.update()

    # desenho de símbolo de suporte com estilo clássico
    def _draw_support_symbol(self, painter: QPainter, screen_p: QPointF, support_type: str):
        # base size adapts with scale
        base = max(12, int(12 * (self.scale / (self.width() / self.base_model_size))))
        x = screen_p.x()
        y = screen_p.y()

        painter.save()
        painter.setPen(QPen(QColor("#3b3b3b")))
        painter.setBrush(QColor("#ffffff"))

        if support_type == "roller":
            # base line
            painter.drawLine(QPointF(x - base, y + base/2), QPointF(x + base, y + base/2))
            # three small rollers (circles) centered under base
            spacing = base * 0.4
            r = max(3, base * 0.18)
            cx = x - spacing
            for _ in range(3):
                painter.setBrush(QColor("#9ca3af"))
                painter.drawEllipse(QPointF(cx, y + base/2 + r + 1), r, r)
                cx += spacing
        elif support_type == "pinned":
            # triangle supported on line
            p1 = QPointF(x - base, y + base/2)
            p2 = QPointF(x + base, y + base/2)
            p3 = QPointF(x, y - base/4)
            poly = QPolygonF([p1, p2, p3])
            painter.setBrush(QColor("#9ca3af"))
            painter.drawPolygon(poly)
            painter.setPen(QPen(QColor("#3b3b3b")))
            painter.drawLine(QPointF(x - base, y + base/2 + 1), QPointF(x + base, y + base/2 + 1))
        elif support_type == "fixed":
            # rectangle flush with ground and short hatch lines
            rect_left = x - base
            rect_top = y - base/2
            rect_w = base * 2
            rect_h = base * 0.6
            # draw filled block (use QRectF to accept floats)
            painter.setBrush(QColor("#6b7280"))
            painter.drawRect(QRectF(rect_left, rect_top, rect_w, rect_h))
            # hatch lines
            painter.setPen(QPen(QColor("#2b2b2b"), 1))
            step = max(3, int(base / 5))
            lx = rect_left + 3
            while lx < rect_left + rect_w - 2:
                painter.drawLine(QPointF(lx, rect_top + rect_h - 2), QPointF(lx + step/2, rect_top + 2))
                lx += step
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f3f6f9"))

        # barra shadow + corpo (cinza)
        shadow_pen = QPen(QColor("#222831"))
        shadow_pen.setWidth(8)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        bar_pen = QPen(QColor("#9ca3af"))
        bar_pen.setWidth(6)
        bar_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        for b in self.bars:
            if b.node_i < len(self.nodes) and b.node_j < len(self.nodes):
                ni = self.nodes[b.node_i]
                nj = self.nodes[b.node_j]
                p1 = self.model_to_screen(ni.x, ni.y, ni.z)
                p2 = self.model_to_screen(nj.x, nj.y, nj.z)

                offset = QPointF(2.0, 3.0)
                painter.setPen(shadow_pen)
                painter.drawLine(p1 + offset, p2 + offset)

                painter.setPen(bar_pen)
                painter.drawLine(p1, p2)

                mid = QPointF((p1.x() + p2.x()) / 2.0, (p1.y() + p2.y()) / 2.0)
                painter.setFont(QFont("Sans", 8))
                painter.setPen(QPen(QColor("#0f172a")))
                txt = f"N={b.results['axial']:.1f} V={b.results['shear']:.1f} M={b.results['moment']:.1f}"
                painter.drawText(QPointF(mid.x() + 8, mid.y() - 8), txt)

        # desenha nós, apoios e cargas
        for n in self.nodes:
            p = self.model_to_screen(n.x, n.y, n.z)
            painter.setPen(QPen(QColor("#0f172a")))
            painter.setBrush(QColor("#10b981"))
            r = max(4, int(6 * (self.scale / (self.width() / self.base_model_size))))
            painter.drawEllipse(p, r, r)
            painter.setPen(QPen(QColor("#0f172a")))
            painter.drawText(QPointF(p.x() + 8, p.y() - 8), f"#{n.id}")

            # suportes: desenha o símbolo apropriado
            if n.support != "none":
                self._draw_support_symbol(painter, QPointF(p.x(), p.y() + r), n.support)

            # cargas nodais
            for ld in n.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    painter.setPen(QPen(QColor("#ef4444")))
                    painter.drawText(QPointF(p.x() + 8, p.y() + 18), f"{vx:.1f},{vy:.1f},{vz:.1f}")
                    arrow_len = max(8, min(40, 6 * self.scale))
                    painter.drawLine(p, QPointF(p.x(), p.y() - arrow_len))

        painter.end()