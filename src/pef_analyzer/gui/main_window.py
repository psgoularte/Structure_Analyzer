"""
Módulo da janela principal da aplicação.
Descrição curta aqui...
"""

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSplitter, QFrame, QStatusBar
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

        # Status bar for error feedback
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #f38ba8; font-size: 12px; padding: 0 8px;")
        self.setStatusBar(self.status_bar)
        self.controls.signal_error.connect(self._show_error)

    def _show_error(self, msg: str):
        self.status_bar.showMessage(f"  {msg}", 6000)

    def _clear_error(self):
        self.status_bar.clearMessage()

    def handle_add_node(self, params):
        try:
            nid = self.canvas.add_node(params.get("x", 0.0), params.get("y", 0.0), params.get("z", 0.0))
            self._clear_error()
            print(f"Node added #{nid}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_add_bar(self, params):
        try:
            bid = self.canvas.add_bar(params.get("i", 0), params.get("j", 0))
            self._clear_error()
            print(f"Bar added #{bid}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_add_support(self, params):
        try:
            self.canvas.add_support(params.get("node", 0), params.get("type", "none"))
            self._clear_error()
            print(f"Support set for node {params.get('node')}: {params.get('type')}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_add_point_load(self, params):
        try:
            self.canvas.add_point_load(params.get("bar", 0), params.get("vx", 0.0), params.get("vy", 0.0), params.get("vz", 0.0), params.get("distance", 0.0))
            self._clear_error()
            print(f"Point load added to bar {params.get('bar')}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_add_dist_load(self, params):
        try:
            self.canvas.add_dist_load_to_bar(params.get("bar", 0), params.get("expr", "0"), params.get("direction", "vy"))
            self._clear_error()
            print(f"Dist load added to bar {params.get('bar')}: {params.get('expr')}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_add_node_moment(self, params):
        try:
            self.canvas.add_node_moment(params.get("node", 0), params.get("mx", 0.0), params.get("my", 0.0), params.get("mz", 0.0))
            self._clear_error()
            print(f"Moment added to node {params.get('node')}")
        except ValueError as e:
            self._show_error(str(e))

    def handle_clear(self):
        self.canvas.clear_structure()
        self._clear_error()
        print("Structure cleared")

    def handle_analyze(self):
        self.canvas.show_effort_graphs()
        print("Analyzing effort distribution along bars")

    def update_canvas(self):
        self.canvas.draw()