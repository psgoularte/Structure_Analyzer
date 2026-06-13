"""
Módulo Controls - Elementos de interface do usuário para interação com a aplicação.
"""
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSlider, QLabel,
    QHBoxLayout, QLineEdit, QComboBox
)


class Controls(QWidget):
    # sinais enviam dicionário com parâmetros (ou valores simples)
    signal_add_node = pyqtSignal(object)
    signal_add_bar = pyqtSignal(object)
    signal_add_support = pyqtSignal(object)
    signal_add_point_load = pyqtSignal(object)
    signal_add_dist_load = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout()

        # Seção adicionar nó
        h_node = QHBoxLayout()
        self.x_input = QLineEdit("0")
        self.x_input.setPlaceholderText("x")
        self.y_input = QLineEdit("0")
        self.y_input.setPlaceholderText("y")
        self.z_input = QLineEdit("0")
        self.z_input.setPlaceholderText("z")
        self.btn_add_node = QPushButton("Add Node")
        self.btn_add_node.clicked.connect(self.on_add_node)
        h_node.addWidget(QLabel("Node x,y,z"))
        h_node.addWidget(self.x_input)
        h_node.addWidget(self.y_input)
        h_node.addWidget(self.z_input)
        h_node.addWidget(self.btn_add_node)
        outer.addLayout(h_node)

        # Seção adicionar barra
        h_bar = QHBoxLayout()
        self.i_input = QLineEdit("0"); self.i_input.setPlaceholderText("i")
        self.j_input = QLineEdit("1"); self.j_input.setPlaceholderText("j")
        self.btn_add_bar = QPushButton("Add Bar")
        self.btn_add_bar.clicked.connect(self.on_add_bar)
        h_bar.addWidget(QLabel("Bar i,j"))
        h_bar.addWidget(self.i_input)
        h_bar.addWidget(self.j_input)
        h_bar.addWidget(self.btn_add_bar)
        outer.addLayout(h_bar)

        # Seção suporte
        h_sup = QHBoxLayout()
        self.sup_node = QLineEdit("0"); self.sup_node.setPlaceholderText("node idx")
        self.sup_type = QComboBox()
        self.sup_type.addItems(["none", "roller", "pinned", "fixed"])
        self.btn_add_sup = QPushButton("Set Support")
        self.btn_add_sup.clicked.connect(self.on_add_support)
        h_sup.addWidget(QLabel("Support node"))
        h_sup.addWidget(self.sup_node)
        h_sup.addWidget(self.sup_type)
        h_sup.addWidget(self.btn_add_sup)
        outer.addLayout(h_sup)

        # Seção carga pontual
        h_load = QHBoxLayout()
        self.load_node = QLineEdit("0"); self.load_node.setPlaceholderText("node idx")
        self.load_vx = QLineEdit("0"); self.load_vx.setPlaceholderText("vx")
        self.load_vy = QLineEdit("-100"); self.load_vy.setPlaceholderText("vy")
        self.load_vz = QLineEdit("0"); self.load_vz.setPlaceholderText("vz")
        self.load_expr = QLineEdit("")  # expressão opcional
        self.btn_add_load = QPushButton("Add Point Load")
        self.btn_add_load.clicked.connect(self.on_add_point_load)
        h_load.addWidget(QLabel("PointLoad node"))
        h_load.addWidget(self.load_node)
        h_load.addWidget(self.load_vx)
        h_load.addWidget(self.load_vy)
        h_load.addWidget(self.load_vz)
        h_load.addWidget(self.load_expr)
        h_load.addWidget(self.btn_add_load)
        outer.addLayout(h_load)

        # Seção carga distribuída em barra
        h_dload = QHBoxLayout()
        self.dload_bar = QLineEdit("0"); self.dload_bar.setPlaceholderText("bar idx")
        self.dload_expr = QLineEdit("0"); self.dload_expr.setPlaceholderText("expr(t)")
        self.dload_dir = QComboBox(); self.dload_dir.addItems(["vx", "vy", "vz"])
        self.btn_add_dload = QPushButton("Add Dist Load")
        self.btn_add_dload.clicked.connect(self.on_add_dist_load)
        h_dload.addWidget(QLabel("DistLoad bar"))
        h_dload.addWidget(self.dload_bar)
        h_dload.addWidget(self.dload_expr)
        h_dload.addWidget(self.dload_dir)
        h_dload.addWidget(self.btn_add_dload)
        outer.addLayout(h_dload)

        # visualização mínima
        self.setLayout(outer)

    def _safe_float(self, lineedit, default=0.0):
        try:
            return float(lineedit.text())
        except Exception:
            return default

    def _safe_int(self, lineedit, default=0):
        try:
            return int(lineedit.text())
        except Exception:
            return default

    def on_add_node(self):
        x = self._safe_float(self.x_input, 0.0)
        y = self._safe_float(self.y_input, 0.0)
        z = self._safe_float(self.z_input, 0.0)
        self.signal_add_node.emit({"x": x, "y": y, "z": z})

    def on_add_bar(self):
        i = self._safe_int(self.i_input, 0)
        j = self._safe_int(self.j_input, 0)
        self.signal_add_bar.emit({"i": i, "j": j})

    def on_add_support(self):
        node = self._safe_int(self.sup_node, 0)
        st = self.sup_type.currentText()
        self.signal_add_support.emit({"node": node, "type": st})

    def on_add_point_load(self):
        node = self._safe_int(self.load_node, 0)
        vx = self._safe_float(self.load_vx, 0.0)
        vy = self._safe_float(self.load_vy, 0.0)
        vz = self._safe_float(self.load_vz, 0.0)
        expr = self.load_expr.text().strip() or None
        self.signal_add_point_load.emit({"node": node, "vx": vx, "vy": vy, "vz": vz, "expr": expr})

    def on_add_dist_load(self):
        bar = self._safe_int(self.dload_bar, 0)
        expr = self.dload_expr.text().strip() or "0"
        direction = self.dload_dir.currentText()
        self.signal_add_dist_load.emit({"bar": bar, "expr": expr, "direction": direction})