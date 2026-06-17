"""
Canvas - Responsável por renderizar o diagrama de forças e restrições.
Inclui pan, zoom e rotação 3D (pitch, yaw, roll), projeção 3D->2D e desenho estético de barras e apoios.
"""

from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QWidget as QtWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF
from ...core.node import Node
from ...core.bar import Bar
from ...core.solver import compute_bar_results
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


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
        self._recalculate_all_efforts()
        self._ensure_view_fit()
        self.update()
        return nid

    def add_bar(self, ni: int, nj: int, area: float = 1.0, e: float = 210e9) -> int:
        if ni < 0 or ni >= len(self.nodes):
            raise ValueError(f"Node {ni} does not exist (have {len(self.nodes)} nodes).")
        if nj < 0 or nj >= len(self.nodes):
            raise ValueError(f"Node {nj} does not exist (have {len(self.nodes)} nodes).")
        if ni == nj:
            raise ValueError("Bar must connect two different nodes.")
        n_i, n_j = self.nodes[ni], self.nodes[nj]
        L2 = (n_j.x-n_i.x)**2 + (n_j.y-n_i.y)**2 + (n_j.z-n_i.z)**2
        if L2 < 1e-12:
            raise ValueError(f"Nodes {ni} and {nj} are at the same position — bar has zero length.")
        bid = len(self.bars)
        b = Bar(bid, ni, nj, area, e)
        self.bars.append(b)
        self._recalculate_all_efforts()
        self._ensure_view_fit()
        self.update()
        return bid

    def add_support(self, node_index: int, support_type: str):
        if node_index < 0 or node_index >= len(self.nodes):
            raise ValueError(f"Node {node_index} does not exist (have {len(self.nodes)} nodes).")
        valid_types = {"none", "roller", "pinned", "fixed"}
        if support_type not in valid_types:
            raise ValueError(f"Support type '{support_type}' is not valid. Use: {sorted(valid_types)}.")
        self.nodes[node_index].support = support_type
        self._recalculate_all_efforts()
        self.update()

    def add_point_load(self, bar_index: int, vx=0.0, vy=0.0, vz=0.0, distance=0.0):
        """Add point load on a bar at specified distance from lower index node."""
        if bar_index < 0 or bar_index >= len(self.bars):
            raise ValueError(f"Bar {bar_index} does not exist (have {len(self.bars)} bars).")
        if distance < 0:
            raise ValueError(f"Distance must be ≥ 0 (got {distance}).")
        bar = self.bars[bar_index]
        ni = self.nodes[bar.node_i]
        nj = self.nodes[bar.node_j]
        import math
        L = math.sqrt((nj.x-ni.x)**2 + (nj.y-ni.y)**2 + (nj.z-ni.z)**2)
        if distance > L + 1e-9:
            raise ValueError(f"Distance {distance:.3f} m exceeds bar length {L:.3f} m.")
        bar.loads.append({"type": "point", "vx": vx, "vy": vy, "vz": vz, "distance": distance, "from_node": bar.node_i})
        self._recalculate_all_efforts()
        self.update()

    def add_dist_load_to_bar(self, bar_index: int, expr: str, direction: str = "vy"):
        if bar_index < 0 or bar_index >= len(self.bars):
            raise ValueError(f"Bar {bar_index} does not exist (have {len(self.bars)} bars).")
        from ...core.load import validate_expr
        validate_expr(expr)   # raises ValueError if invalid
        self.bars[bar_index].loads.append({"type": "dist", "expr": expr, "direction": direction})
        self._recalculate_all_efforts()
        self.update()

    def add_node_moment(self, node_index: int, mx=0.0, my=0.0, mz=0.0):
        """Add moment to a node."""
        if node_index < 0 or node_index >= len(self.nodes):
            raise ValueError(f"Node {node_index} does not exist (have {len(self.nodes)} nodes).")
        self.nodes[node_index].loads.append({"type": "moment", "mx": mx, "my": my, "mz": mz})
        self._recalculate_all_efforts()
        self.update()

    def _recalculate_all_efforts(self):
        """Recalculate efforts for all bars when any change occurs."""
        for bar in self.bars:
            compute_bar_results(bar, self.nodes)

    def clear_structure(self):
        """Clear all nodes, bars, and loads from the structure."""
        self.nodes = []
        self.bars = []
        self._ensure_view_fit()
        self.update()

    def show_effort_graphs(self):
        """Show effort distribution graphs for all bars in a dialog."""
        if not self.bars:
            print("No bars to analyze")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Effort Distribution Analysis")
        dialog.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Create tab widget for each bar
        tab_widget = QTabWidget()
        
        for bar in self.bars:
            if bar.node_i >= len(self.nodes) or bar.node_j >= len(self.nodes):
                continue
            
            ni = self.nodes[bar.node_i]
            nj = self.nodes[bar.node_j]
            
            # Create tab content
            tab_content = QtWidget()
            tab_layout = QVBoxLayout(tab_content)
            
            # Create matplotlib figure with subplots
            fig = Figure(figsize=(10, 8))
            canvas = FigureCanvas(fig)
            
            # Create 3 subplots: Axial, Shear, Moment
            ax1 = fig.add_subplot(311)
            ax2 = fig.add_subplot(312)
            ax3 = fig.add_subplot(313)
            
            # Calculate effort distribution along the bar using the functions
            t_values = np.linspace(0, 1, 100)
            
            # Get effort functions if available
            N_func = bar.results.get('N_func')
            Vy_func = bar.results.get('Vy_func')
            Vz_func = bar.results.get('Vz_func')
            My_func = bar.results.get('My_func')
            Mz_func = bar.results.get('Mz_func')
            T_func = bar.results.get('T_func')
            
            # Calculate effort values using functions
            if N_func:
                N_values = [N_func(t) for t in t_values]
            else:
                N_values = [bar.results.get('N', 0.0)] * len(t_values)
            
            if Vy_func:
                Vy_values = [Vy_func(t) for t in t_values]
            else:
                Vy_values = [bar.results.get('Vy', 0.0)] * len(t_values)
            
            if Vz_func:
                Vz_values = [Vz_func(t) for t in t_values]
            else:
                Vz_values = [bar.results.get('Vz', 0.0)] * len(t_values)
            
            if My_func:
                My_values = [My_func(t) for t in t_values]
            else:
                My_values = [bar.results.get('My', 0.0)] * len(t_values)
            
            if Mz_func:
                Mz_values = [Mz_func(t) for t in t_values]
            else:
                Mz_values = [bar.results.get('Mz', 0.0)] * len(t_values)
            
            if T_func:
                T_values = [T_func(t) for t in t_values]
            else:
                T_values = [bar.results.get('T', 0.0)] * len(t_values)
            
            # Plot Axial force N
            ax1.plot(t_values, N_values, 'r-', label='N (Axial)', linewidth=2)
            ax1.set_ylabel('Force (kN)')
            ax1.set_title(f'Bar #{bar.id} - Node {bar.node_i} to Node {bar.node_j} - Axial Force')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot Shear forces Vy, Vz
            ax2.plot(t_values, Vy_values, 'g-', label='Vy (Shear Y)', linewidth=2)
            ax2.plot(t_values, Vz_values, 'c-', label='Vz (Shear Z)', linewidth=2)
            ax2.set_ylabel('Force (kN)')
            ax2.set_title('Shear Forces')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Plot Moments My, Mz and Torque T
            ax3.plot(t_values, My_values, 'b-', label='My (Moment Y)', linewidth=2)
            ax3.plot(t_values, Mz_values, 'm-', label='Mz (Moment Z)', linewidth=2)
            ax3.plot(t_values, T_values, 'purple', label='T (Torque)', linewidth=2, linestyle='--')
            ax3.set_xlabel('Position along bar (t: 0→1)')
            ax3.set_ylabel('Moment (kN·m)')
            ax3.set_title('Moments and Torque')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            fig.tight_layout()
            
            tab_layout.addWidget(canvas)
            tab_widget.addTab(tab_content, f"Bar #{bar.id}")
        
        layout.addWidget(tab_widget)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.exec()

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
        
        # Modern dark background with subtle gradient
        bg_color = QColor("#1e1e2e")
        painter.fillRect(self.rect(), bg_color)
        
        # Draw grid for better spatial reference
        self._draw_grid(painter)
        
        # Draw coordinate axes for reference
        self._draw_coordinate_axes(painter)

        # Modern bar styling with gradient and glow effect
        for b in self.bars:
            if b.node_i < len(self.nodes) and b.node_j < len(self.nodes):
                ni = self.nodes[b.node_i]
                nj = self.nodes[b.node_j]
                p1 = self.model_to_screen(ni.x, ni.y, ni.z)
                p2 = self.model_to_screen(nj.x, nj.y, nj.z)

                # Glow effect (outer shadow)
                glow_pen = QPen(QColor("#89b4fa"))
                glow_pen.setWidth(10)
                glow_pen.setColor(QColor(137, 180, 250, 30))
                glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(glow_pen)
                painter.drawLine(p1, p2)

                # Main bar with modern color
                bar_pen = QPen(QColor("#cba6f7"))
                bar_pen.setWidth(5)
                bar_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(bar_pen)
                painter.drawLine(p1, p2)

                # Bar highlight (inner line)
                highlight_pen = QPen(QColor("#f5c2e7"))
                highlight_pen.setWidth(2)
                highlight_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(highlight_pen)
                painter.drawLine(p1, p2)

                # Draw distributed load visualization
                for ld in b.loads:
                    if ld.get("type") == "dist":
                        self._draw_dist_load_visualization(painter, p1, p2, ld)
                
                # Draw point loads along bars
                model_dx = nj.x - ni.x
                model_dy = nj.y - ni.y
                model_dz = nj.z - ni.z
                model_length = math.sqrt(model_dx**2 + model_dy**2 + model_dz**2)
                for ld in b.loads:
                    if ld.get("type") == "point":
                        distance = ld.get("distance", 0.0)
                        t = min(distance / model_length, 1.0) if model_length > 0 else 0.0
                        self._draw_point_load_on_bar(painter, p1, p2, ld, t, distance)

                # Modern result labels with background
                mid = QPointF((p1.x() + p2.x()) / 2.0, (p1.y() + p2.y()) / 2.0)
                self._draw_result_label(painter, mid, b.results, b.id)

        # Modern nodes with glow effect
        for n in self.nodes:
            p = self.model_to_screen(n.x, n.y, n.z)
            r = max(5, int(7 * (self.scale / (self.width() / self.base_model_size))))
            
            # Node glow
            glow_color = QColor("#a6e3a1")
            glow_color.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawEllipse(p, r + 4, r + 4)
            
            # Node body with gradient-like effect
            node_color = QColor("#a6e3a1")
            painter.setPen(QPen(QColor("#1e1e2e"), 2))
            painter.setBrush(node_color)
            painter.drawEllipse(p, r, r)
            
            # Node label with modern styling
            painter.setPen(QPen(QColor("#cdd6f4")))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QPointF(p.x() + r + 6, p.y() + 4), f"#{n.id}")

            # Modern support symbols
            if n.support != "none":
                self._draw_support_symbol(painter, QPointF(p.x(), p.y() + r + 2), n.support)

            # Modern load indicators
            for ld in n.loads:
                if ld.get("type") == "point":
                    vx = ld.get("vx", 0.0)
                    vy = ld.get("vy", 0.0)
                    vz = ld.get("vz", 0.0)
                    self._draw_load_indicator(painter, p, vx, vy, vz)
                elif ld.get("type") == "moment":
                    mx = ld.get("mx", 0.0)
                    my = ld.get("my", 0.0)
                    mz = ld.get("mz", 0.0)
                    self._draw_moment_indicator(painter, p, mx, my, mz, n)

        painter.end()

    def _draw_grid(self, painter):
        """Draw a subtle grid for spatial reference."""
        grid_color = QColor("#45475a")
        grid_color.setAlpha(40)
        painter.setPen(QPen(grid_color, 1))
        
        # Calculate grid spacing based on scale
        grid_spacing = 50
        if self.scale > 2:
            grid_spacing = 100
        elif self.scale < 0.5:
            grid_spacing = 25
        
        # Draw vertical lines
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())
        
        # Draw horizontal lines
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def _draw_coordinate_axes(self, painter):
        """Draw X, Y, Z coordinate axes that follow the model rotation."""
        # Use model origin (0,0,0) and apply the same rotation as the model
        axis_length = 8.0  # in model units
        
        # Get screen positions for axis endpoints
        origin = self.model_to_screen(0, 0, 0)
        x_end = self.model_to_screen(axis_length, 0, 0)
        y_end = self.model_to_screen(0, axis_length, 0)
        z_end = self.model_to_screen(0, 0, axis_length)
        
        # Draw X axis (red)
        painter.setPen(QPen(QColor("#f38ba8"), 3))
        painter.setBrush(QColor("#f38ba8"))
        painter.drawLine(origin, x_end)
        # X arrow head
        dx = x_end.x() - origin.x()
        dy = x_end.y() - origin.y()
        length = (dx*dx + dy*dy)**0.5
        if length > 0:
            ux, uy = dx/length, dy/length
            head_size = 10
            px, py = -uy * head_size * 0.5, ux * head_size * 0.5
            arrow_head = QPolygonF([
                x_end,
                QPointF(x_end.x() - ux * head_size + px, x_end.y() - uy * head_size + py),
                QPointF(x_end.x() - ux * head_size - px, x_end.y() - uy * head_size - py)
            ])
            painter.drawPolygon(arrow_head)
        # X label
        painter.setPen(QPen(QColor("#f38ba8")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QPointF(x_end.x() + 8, x_end.y() + 4), "X")
        
        # Draw Y axis (green)
        painter.setPen(QPen(QColor("#a6e3a1"), 3))
        painter.setBrush(QColor("#a6e3a1"))
        painter.drawLine(origin, y_end)
        # Y arrow head
        dx = y_end.x() - origin.x()
        dy = y_end.y() - origin.y()
        length = (dx*dx + dy*dy)**0.5
        if length > 0:
            ux, uy = dx/length, dy/length
            head_size = 10
            px, py = -uy * head_size * 0.5, ux * head_size * 0.5
            arrow_head = QPolygonF([
                y_end,
                QPointF(y_end.x() - ux * head_size + px, y_end.y() - uy * head_size + py),
                QPointF(y_end.x() - ux * head_size - px, y_end.y() - uy * head_size - py)
            ])
            painter.drawPolygon(arrow_head)
        # Y label
        painter.setPen(QPen(QColor("#a6e3a1")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QPointF(y_end.x() + 8, y_end.y() + 4), "Y")
        
        # Draw Z axis (blue)
        painter.setPen(QPen(QColor("#89b4fa"), 3))
        painter.setBrush(QColor("#89b4fa"))
        painter.drawLine(origin, z_end)
        # Z arrow head
        dx = z_end.x() - origin.x()
        dy = z_end.y() - origin.y()
        length = (dx*dx + dy*dy)**0.5
        if length > 0:
            ux, uy = dx/length, dy/length
            head_size = 10
            px, py = -uy * head_size * 0.5, ux * head_size * 0.5
            arrow_head = QPolygonF([
                z_end,
                QPointF(z_end.x() - ux * head_size + px, z_end.y() - uy * head_size + py),
                QPointF(z_end.x() - ux * head_size - px, z_end.y() - uy * head_size - py)
            ])
            painter.drawPolygon(arrow_head)
        # Z label
        painter.setPen(QPen(QColor("#89b4fa")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QPointF(z_end.x() + 8, z_end.y() + 4), "Z")
        
        # Draw origin point
        painter.setPen(QPen(QColor("#cdd6f4"), 2))
        painter.setBrush(QColor("#cdd6f4"))
        painter.drawEllipse(origin, 5, 5)

    def _draw_moment_indicator(self, painter, pos, mx, my, mz, node):
        """Draw moment indicator as double-headed straight arrows along rotation axes (mechanics standard)."""
        if (mx**2 + my**2 + mz**2)**0.5 < 0.01:
            return

        # Compute a model-space length that projects to ~55px on screen
        moment_scale = 55.0 / self.scale if self.scale > 0 else 5.0

        if abs(mx) > 0.01:
            sign = 1 if mx > 0 else -1
            end_pt = self.model_to_screen(node.x + sign * moment_scale, node.y, node.z)
            self._draw_moment_vector_arrow(painter, pos, end_pt, QColor("#f38ba8"))
            painter.setPen(QPen(QColor("#f38ba8")))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QPointF(end_pt.x() + 5, end_pt.y() - 5), f"Mx:{mx:+.1f}")

        if abs(my) > 0.01:
            sign = 1 if my > 0 else -1
            end_pt = self.model_to_screen(node.x, node.y + sign * moment_scale, node.z)
            self._draw_moment_vector_arrow(painter, pos, end_pt, QColor("#a6e3a1"))
            painter.setPen(QPen(QColor("#a6e3a1")))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QPointF(end_pt.x() + 5, end_pt.y() - 5), f"My:{my:+.1f}")

        if abs(mz) > 0.01:
            sign = 1 if mz > 0 else -1
            end_pt = self.model_to_screen(node.x, node.y, node.z + sign * moment_scale)
            self._draw_moment_vector_arrow(painter, pos, end_pt, QColor("#89b4fa"))
            painter.setPen(QPen(QColor("#89b4fa")))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QPointF(end_pt.x() + 5, end_pt.y() - 5), f"Mz:{mz:+.1f}")

    def _draw_moment_vector_arrow(self, painter, start, end, color):
        """Double-headed straight arrow — standard mechanics notation for moment vectors."""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = (dx*dx + dy*dy)**0.5
        if length < 1e-6:
            return
        ux, uy = dx / length, dy / length
        head = 10
        px, py = -uy * head * 0.5, ux * head * 0.5

        painter.setPen(QPen(color, 3))
        painter.drawLine(start, end)
        painter.setBrush(color)

        # Arrowhead at the far end
        painter.drawPolygon(QPolygonF([
            end,
            QPointF(end.x() - ux * head + px, end.y() - uy * head + py),
            QPointF(end.x() - ux * head - px, end.y() - uy * head - py),
        ]))
        # Arrowhead at the near end (double-headed = moment vector convention)
        painter.drawPolygon(QPolygonF([
            start,
            QPointF(start.x() + ux * head + px, start.y() + uy * head + py),
            QPointF(start.x() + ux * head - px, start.y() + uy * head - py),
        ]))

    def _draw_result_label(self, painter, pos, results, bar_id):
        """Draw detailed effort diagram on bar with all 3D effort types and max values."""
        # Get all 3D effort values
        N = results.get('N', 0.0)
        Vy = results.get('Vy', 0.0)
        Vz = results.get('Vz', 0.0)
        My = results.get('My', 0.0)
        Mz = results.get('Mz', 0.0)
        T = results.get('T', 0.0)
        
        # Create detailed diagram with all effort types
        lines = [
            f"━━━ BAR #{bar_id} ━━━",
            f"🔴 N:  {N:+.2f} kN",
            f"🟢 Vy: {Vy:+.2f} kN",
            f"🟢 Vz: {Vz:+.2f} kN",
            f"🔵 My: {My:+.2f} kN·m",
            f"🔵 Mz: {Mz:+.2f} kN·m",
            f"🟣 T:  {T:+.2f} kN·m"
        ]
        
        # Background for label
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        font_metrics = painter.fontMetrics()
        max_width = max(font_metrics.horizontalAdvance(line) for line in lines)
        text_height = font_metrics.height() * len(lines)
        
        # Position label above bar with offset (increased distance for better visualization)
        label_x = pos.x() - max_width / 2
        label_y = pos.y() - text_height - 90
        
        bg_rect = QRectF(label_x - 8, label_y - 8, max_width + 16, text_height + 16)
        painter.setPen(Qt.PenStyle.NoPen)
        bg_color = QColor("#1e1e2e")
        bg_color.setAlpha(240)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(bg_rect, 8, 8)
        
        # Border
        painter.setPen(QPen(QColor("#89b4fa"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bg_rect, 8, 8)
        
        # Text with color coding
        y_offset = label_y + font_metrics.height() - 2
        for i, line in enumerate(lines):
            if i == 0:  # Header
                color = QColor("#cdd6f4")
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            elif i == 1:  # N (Axial)
                color = QColor("#f38ba8")
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            elif i in [2, 3]:  # Vy, Vz (Shear)
                color = QColor("#a6e3a1")
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            elif i in [4, 5]:  # My, Mz (Moment)
                color = QColor("#89b4fa")
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            else:  # T (Torque)
                color = QColor("#cba6f7")
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
            
            painter.setPen(QPen(color))
            painter.drawText(QPointF(label_x, y_offset), line)
            y_offset += font_metrics.height()

    def _draw_effort_arrows(self, painter, p1, p2, results):
        """Draw arrows showing effort directions on the bar for all 3D effort types."""
        N = results.get('N', 0.0)
        Vy = results.get('Vy', 0.0)
        Vz = results.get('Vz', 0.0)
        My = results.get('My', 0.0)
        Mz = results.get('Mz', 0.0)
        T = results.get('T', 0.0)
        
        # Calculate bar direction and perpendicular
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = (dx*dx + dy*dy)**0.5
        if length < 1e-6:
            return
        
        # Unit vectors
        ux, uy = dx/length, dy/length
        px, py = -uy, ux  # perpendicular
        
        # Arrow positions (offset from bar center)
        mid_x = (p1.x() + p2.x()) / 2.0
        mid_y = (p1.y() + p2.y()) / 2.0
        offset = 25
        
        # Draw axial force N arrow (along bar)
        if abs(N) > 1.0:
            arrow_len = min(40, max(15, abs(N) * 0.3))
            if N > 0:  # Tension - arrows pointing outward
                # Arrow from center toward p2
                self._draw_single_arrow(painter, 
                    QPointF(mid_x, mid_y), 
                    QPointF(mid_x + ux * arrow_len, mid_y + uy * arrow_len),
                    QColor("#f38ba8"), 3)
                # Arrow from center toward p1
                self._draw_single_arrow(painter,
                    QPointF(mid_x, mid_y),
                    QPointF(mid_x - ux * arrow_len, mid_y - uy * arrow_len),
                    QColor("#f38ba8"), 3)
            else:  # Compression - arrows pointing inward
                # Arrow from p2 toward center
                self._draw_single_arrow(painter,
                    QPointF(mid_x + ux * arrow_len * 1.5, mid_y + uy * arrow_len * 1.5),
                    QPointF(mid_x, mid_y),
                    QColor("#fab387"), 3)
                # Arrow from p1 toward center
                self._draw_single_arrow(painter,
                    QPointF(mid_x - ux * arrow_len * 1.5, mid_y - uy * arrow_len * 1.5),
                    QPointF(mid_x, mid_y),
                    QColor("#fab387"), 3)
        
        # Draw shear force Vy arrow (perpendicular to bar, green)
        if abs(Vy) > 1.0:
            arrow_len = min(35, max(12, abs(Vy) * 0.25))
            shear_start = QPointF(mid_x + px * offset, mid_y + py * offset)
            shear_end = QPointF(mid_x + px * (offset + arrow_len), mid_y + py * (offset + arrow_len))
            self._draw_single_arrow(painter, shear_start, shear_end, QColor("#a6e3a1"), 2)
        
        # Draw shear force Vz arrow (perpendicular to bar, cyan, offset)
        if abs(Vz) > 1.0:
            arrow_len = min(35, max(12, abs(Vz) * 0.25))
            vz_offset = offset + 15
            shear_start = QPointF(mid_x + px * vz_offset, mid_y + py * vz_offset)
            shear_end = QPointF(mid_x + px * (vz_offset + arrow_len), mid_y + py * (vz_offset + arrow_len))
            self._draw_single_arrow(painter, shear_start, shear_end, QColor("#89dceb"), 2)
        
        # Draw moment My indicator (circular arrow, blue)
        if abs(My) > 1.0:
            moment_radius = min(20, max(10, abs(My) * 0.1))
            moment_center = QPointF(mid_x - px * offset, mid_y - py * offset)
            self._draw_moment_arrow(painter, moment_center, moment_radius, My, QColor("#89b4fa"))
        
        # Draw moment Mz indicator (circular arrow, magenta, offset)
        if abs(Mz) > 1.0:
            moment_radius = min(20, max(10, abs(Mz) * 0.1))
            mz_offset = offset + 15
            moment_center = QPointF(mid_x - px * mz_offset, mid_y - py * mz_offset)
            self._draw_moment_arrow(painter, moment_center, moment_radius, Mz, QColor("#cba6f7"))
        
        # Draw torque T indicator (circular arrow, purple, further offset)
        if abs(T) > 1.0:
            moment_radius = min(20, max(10, abs(T) * 0.1))
            t_offset = offset + 30
            moment_center = QPointF(mid_x - px * t_offset, mid_y - py * t_offset)
            self._draw_moment_arrow(painter, moment_center, moment_radius, T, QColor("#f5c2e7"))

    def _draw_single_arrow(self, painter, start, end, color, width):
        """Draw a single arrow with given start and end points."""
        painter.setPen(QPen(color, width))
        painter.setBrush(color)
        painter.drawLine(start, end)
        
        # Arrow head
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = (dx*dx + dy*dy)**0.5
        if length > 0:
            ux, uy = dx/length, dy/length
            head_size = 8
            # Perpendicular for arrow head width
            px, py = -uy * head_size * 0.5, ux * head_size * 0.5
            
            arrow_head = QPolygonF([
                end,
                QPointF(end.x() - ux * head_size + px, end.y() - uy * head_size + py),
                QPointF(end.x() - ux * head_size - px, end.y() - uy * head_size - py)
            ])
            painter.drawPolygon(arrow_head)

    def _draw_moment_arrow(self, painter, center, radius, moment, color):
        """Draw a circular arrow to represent moment."""
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw arc
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        start_angle = 0 if moment > 0 else 180
        span_angle = 270 if moment > 0 else -270
        painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))
        
        # Arrow head at end of arc
        if moment > 0:
            arrow_pos = QPointF(center.x() + radius, center.y())
            arrow_dir = QPointF(0, 1)  # clockwise
        else:
            arrow_pos = QPointF(center.x() - radius, center.y())
            arrow_dir = QPointF(0, -1)  # counter-clockwise
        
        head_size = 6
        arrow_head = QPolygonF([
            arrow_pos,
            QPointF(arrow_pos.x() - arrow_dir.x() * head_size + arrow_dir.y() * head_size * 0.5,
                    arrow_pos.y() - arrow_dir.y() * head_size - arrow_dir.x() * head_size * 0.5),
            QPointF(arrow_pos.x() - arrow_dir.x() * head_size - arrow_dir.y() * head_size * 0.5,
                    arrow_pos.y() - arrow_dir.y() * head_size + arrow_dir.x() * head_size * 0.5)
        ])
        painter.setBrush(color)
        painter.drawPolygon(arrow_head)

    def _force_screen_dir(self, vx, vy, vz):
        """Unit vector in screen space for force (vx,vy,vz), using the current 3D rotation."""
        total = (vx**2 + vy**2 + vz**2)**0.5
        if total < 1e-9:
            return 0.0, 1.0
        xr, yr, zr = self._rotate_point(vx / total, vy / total, vz / total)
        dx = xr
        dy = -(yr + zr * self.projection_scale)
        dlen = (dx**2 + dy**2)**0.5
        if dlen < 1e-9:
            return 0.0, 1.0
        return dx / dlen, dy / dlen

    def _draw_load_indicator(self, painter, pos, vx, vy, vz):
        """Draw load indicator with arrow following the 3D-rotated force direction."""
        load_text = f"({vx:.0f}, {vy:.0f}, {vz:.0f})"
        painter.setPen(QPen(QColor("#f38ba8")))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QPointF(pos.x() + 8, pos.y() + 20), load_text)

        total_load = (vx**2 + vy**2 + vz**2)**0.5
        if total_load > 0.01:
            arrow_len = 55
            dx, dy = self._force_screen_dir(vx, vy, vz)

            if total_load > 200:
                arrow_color = QColor("#f38ba8")
            elif total_load > 100:
                arrow_color = QColor("#fab387")
            else:
                arrow_color = QColor("#89b4fa")

            end_x = pos.x() + dx * arrow_len
            end_y = pos.y() + dy * arrow_len

            painter.setPen(QPen(arrow_color, 2))
            painter.setBrush(arrow_color)
            painter.drawLine(pos, QPointF(end_x, end_y))

            head_size = 8
            px = -dy * head_size * 0.5
            py = dx * head_size * 0.5
            painter.drawPolygon(QPolygonF([
                QPointF(end_x, end_y),
                QPointF(end_x - dx * head_size + px, end_y - dy * head_size + py),
                QPointF(end_x - dx * head_size - px, end_y - dy * head_size - py),
            ]))

    def _draw_dist_load_visualization(self, painter, p1, p2, load_data):
        """Draw distributed load as parallel arrows pointing in force direction, with load line."""
        expr = load_data.get("expr", "0")
        direction = load_data.get("direction", "vy")

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        if (dx*dx + dy*dy)**0.5 < 1e-6:
            return

        color = (QColor("#f38ba8") if direction == "vx" else
                 QColor("#a6e3a1") if direction == "vy" else
                 QColor("#89b4fa"))

        # Sample magnitudes for proportional scaling
        from ...core.load import eval_expr as _eval
        NUM = 9
        t_vals = [i / (NUM - 1) for i in range(NUM)]
        try:
            mags = [_eval(expr, t) for t in t_vals]
        except Exception:
            mags = [20.0] * NUM

        max_abs = max(abs(m) for m in mags)
        if max_abs < 0.01:
            return

        ARROW_MAX = 50  # pixels for the largest arrow

        # Screen-space direction of the force vector, accounting for 3D rotation
        _dir_model = {"vx": (1,0,0), "vy": (0,1,0), "vz": (0,0,1), "perpendicular": (0,1,0)}
        gvx, gvy, gvz = _dir_model.get(direction, (0,1,0))
        fsx, fsy = self._force_screen_dir(gvx, gvy, gvz)

        def tip_offset(mag):
            """Screen-space offset from bar to arrow tail.
            Zero for zero-magnitude loads so the load line traces the true function shape."""
            if abs(mag) < 0.001 * max_abs:
                return 0.0, 0.0
            scaled = ARROW_MAX * abs(mag) / max_abs
            s = 1 if mag >= 0 else -1
            # Tail is opposite to force direction: tail = bar_pos - s * force_dir * scaled
            return -s * fsx * scaled, -s * fsy * scaled

        def draw_arrow(tip_pt, base_pt):
            """Arrow from tail (tip_pt, no head) → bar (base_pt, arrowhead)."""
            dir_x = base_pt.x() - tip_pt.x()
            dir_y = base_pt.y() - tip_pt.y()
            dlen = (dir_x**2 + dir_y**2)**0.5
            if dlen < 0.5:
                return
            dir_x /= dlen
            dir_y /= dlen
            head = 8
            px, py = -dir_y * head * 0.5, dir_x * head * 0.5
            painter.setPen(QPen(color, 2))
            painter.setBrush(color)
            painter.drawLine(tip_pt, base_pt)
            painter.drawPolygon(QPolygonF([
                base_pt,
                QPointF(base_pt.x() - dir_x * head + px, base_pt.y() - dir_y * head + py),
                QPointF(base_pt.x() - dir_x * head - px, base_pt.y() - dir_y * head - py),
            ]))

        # Draw all arrows and collect tail positions for the load line
        tail_pts = []
        for i, t in enumerate(t_vals):
            bx = p1.x() + dx * t
            by = p1.y() + dy * t
            ox, oy = tip_offset(mags[i])
            tail = QPointF(bx + ox, by + oy)
            if abs(ox) + abs(oy) > 0.5:   # skip zero-load positions (tail = bar pos)
                draw_arrow(tail, QPointF(bx, by))
            tail_pts.append(tail)

        # Load line connecting all tails
        painter.setPen(QPen(color, 2))
        for k in range(len(tail_pts) - 1):
            painter.drawLine(tail_pts[k], tail_pts[k + 1])

        # Label near midpoint
        ox_mid, oy_mid = tip_offset(mags[NUM // 2])
        mid_x = (p1.x() + p2.x()) / 2.0
        mid_y = (p1.y() + p2.y()) / 2.0
        painter.setPen(QPen(color))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QPointF(mid_x + ox_mid + 8, mid_y + oy_mid - 4), f"{expr} ({direction})")

    def _draw_point_load_on_bar(self, painter, p1, p2, load_data, t, distance):
        """Draw point load at specific position along bar using global coordinate system."""
        vx = load_data.get("vx", 0.0)
        vy = load_data.get("vy", 0.0)
        vz = load_data.get("vz", 0.0)

        # Calculate bar direction in screen space
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = (dx*dx + dy*dy)**0.5
        if length < 1e-6:
            return

        # t is the normalized position (0 to 1) computed from model coordinates
        load_x = p1.x() + dx * t
        load_y = p1.y() + dy * t
        load_pos = QPointF(load_x, load_y)

        total_load = (vx**2 + vy**2 + vz**2)**0.5
        if total_load > 0.01:
            arrow_len = 55
            dir_x, dir_y = self._force_screen_dir(vx, vy, vz)

            if total_load > 200:
                arrow_color = QColor("#f38ba8")
            elif total_load > 100:
                arrow_color = QColor("#fab387")
            else:
                arrow_color = QColor("#89b4fa")

            end_x = load_x + dir_x * arrow_len
            end_y = load_y + dir_y * arrow_len

            painter.setPen(QPen(arrow_color, 2))
            painter.setBrush(arrow_color)
            painter.drawLine(load_pos, QPointF(end_x, end_y))

            head_size = 12
            perp_x = -dir_y * head_size * 0.5
            perp_y = dir_x * head_size * 0.5
            painter.drawPolygon(QPolygonF([
                QPointF(end_x, end_y),
                QPointF(end_x - dir_x * head_size + perp_x, end_y - dir_y * head_size + perp_y),
                QPointF(end_x - dir_x * head_size - perp_x, end_y - dir_y * head_size - perp_y),
            ]))
        
        # Draw distance label showing coordinate distance from node i
        dist_text = f"{distance:.1f}m"
        painter.setPen(QPen(QColor("#cdd6f4")))
        painter.setFont(QFont("Segoe UI", 7))
        text_pos = QPointF(load_x + 10, load_y - 10)
        painter.drawText(text_pos, dist_text)