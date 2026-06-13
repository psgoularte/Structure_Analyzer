"""
Módulo da janela principal da aplicação.
Descrição curta aqui...
"""

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from .widgets.canvas import Canvas
from .widgets.controls import Controls


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PEF Analyzer")
        self.setGeometry(100, 100, 1000, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.canvas = Canvas()
        self.controls = Controls()

        self.layout.addWidget(self.controls)
        self.layout.addWidget(self.canvas)

        # conectar sinais
        self.controls.signal_add_node.connect(self.handle_add_node)
        self.controls.signal_add_bar.connect(self.handle_add_bar)
        self.controls.signal_add_support.connect(self.handle_add_support)
        self.controls.signal_add_point_load.connect(self.handle_add_point_load)
        self.controls.signal_add_dist_load.connect(self.handle_add_dist_load)

    def handle_add_node(self, params):
        nid = self.canvas.add_node(params.get("x", 0.0), params.get("y", 0.0), params.get("z", 0.0))
        print(f"Node added #{nid}")

    def handle_add_bar(self, params):
        i = params.get("i", 0)
        j = params.get("j", 0)
        bid = self.canvas.add_bar(i, j)
        print(f"Bar added #{bid}")

    def handle_add_support(self, params):
        node = params.get("node", 0)
        st = params.get("type", "none")
        self.canvas.add_support(node, st)
        print(f"Support set for node {node}: {st}")

    def handle_add_point_load(self, params):
        node = params.get("node", 0)
        self.canvas.add_point_load(node, params.get("vx", 0.0), params.get("vy", 0.0), params.get("vz", 0.0), params.get("expr"))
        print(f"Point load added to node {node}")

    def handle_add_dist_load(self, params):
        bar = params.get("bar", 0)
        expr = params.get("expr", "0")
        direction = params.get("direction", "vy")
        self.canvas.add_dist_load_to_bar(bar, expr, direction)
        print(f"Dist load added to bar {bar}: {expr} ({direction})")

    def update_canvas(self):
        self.canvas.draw()