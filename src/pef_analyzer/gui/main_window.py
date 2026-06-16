"""
Módulo da janela principal da aplicação.
Descrição curta aqui...
"""

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSplitter, QFrame
from PyQt6.QtCore import Qt
from .widgets.canvas import Canvas
from .widgets.controls import Controls


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PEF Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main horizontal layout with splitter
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        
        # Controls panel (left sidebar)
        self.controls = Controls()
        self.controls.setFixedWidth(320)
        
        # Canvas panel (main area)
        self.canvas = Canvas()
        
        # Add panels to splitter
        self.splitter.addWidget(self.controls)
        self.splitter.addWidget(self.canvas)
        
        # Set initial sizes (controls: 350px, canvas: rest)
        self.splitter.setSizes([350, 850])
        
        # Add splitter to main layout
        self.layout.addWidget(self.splitter)

        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #45475a;")

        # conectar sinais
        self.controls.signal_add_node.connect(self.handle_add_node)
        self.controls.signal_add_bar.connect(self.handle_add_bar)
        self.controls.signal_add_support.connect(self.handle_add_support)
        self.controls.signal_add_point_load.connect(self.handle_add_point_load)
        self.controls.signal_add_dist_load.connect(self.handle_add_dist_load)
        self.controls.signal_add_node_moment.connect(self.handle_add_node_moment)
        self.controls.signal_clear.connect(self.handle_clear)
        self.controls.signal_analyze.connect(self.handle_analyze)

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
        bar = params.get("bar", 0)
        self.canvas.add_point_load(bar, params.get("vx", 0.0), params.get("vy", 0.0), params.get("vz", 0.0), params.get("distance", 0.0))
        print(f"Point load added to bar {bar} at distance {params.get('distance', 0.0)}")

    def handle_add_dist_load(self, params):
        bar = params.get("bar", 0)
        expr = params.get("expr", "0")
        direction = params.get("direction", "vy")
        self.canvas.add_dist_load_to_bar(bar, expr, direction)
        print(f"Dist load added to bar {bar}: {expr} ({direction})")

    def handle_add_node_moment(self, params):
        node = params.get("node", 0)
        mx = params.get("mx", 0.0)
        my = params.get("my", 0.0)
        mz = params.get("mz", 0.0)
        self.canvas.add_node_moment(node, mx, my, mz)
        print(f"Node moment added to node {node}: Mx={mx}, My={my}, Mz={mz}")

    def handle_clear(self):
        self.canvas.clear_structure()
        print("Structure cleared")

    def handle_analyze(self):
        self.canvas.show_effort_graphs()
        print("Analyzing effort distribution along bars")

    def update_canvas(self):
        self.canvas.draw()