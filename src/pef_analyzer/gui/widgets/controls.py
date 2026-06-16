"""
Módulo Controls - Elementos de interface do usuário para interação com a aplicação.
"""
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSlider, QLabel,
    QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFrame,
    QScrollArea, QSizePolicy
)


class Controls(QWidget):
    # sinais enviam dicionário com parâmetros (ou valores simples)
    signal_add_node = pyqtSignal(object)
    signal_add_bar = pyqtSignal(object)
    signal_add_support = pyqtSignal(object)
    signal_add_point_load = pyqtSignal(object)
    signal_add_dist_load = pyqtSignal(object)
    signal_add_node_moment = pyqtSignal(object)
    signal_clear = pyqtSignal()
    signal_analyze = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Create scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Main container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(16, 16, 16, 16)
        
        # Add Node Section
        node_group = self.create_node_section()
        container_layout.addWidget(node_group)
        
        # Add Bar Section
        bar_group = self.create_bar_section()
        container_layout.addWidget(bar_group)
        
        # Support Section
        support_group = self.create_support_section()
        container_layout.addWidget(support_group)
        
        # Point Load Section
        point_load_group = self.create_point_load_section()
        container_layout.addWidget(point_load_group)
        
        # Distributed Load Section
        dist_load_group = self.create_dist_load_section()
        container_layout.addWidget(dist_load_group)
        
        # Node Moment Section
        moment_group = self.create_node_moment_section()
        container_layout.addWidget(moment_group)
        
        # Clear Section
        clear_group = self.create_clear_section()
        container_layout.addWidget(clear_group)
        
        # Add stretch to push everything to top
        container_layout.addStretch()
        
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def create_node_section(self):
        group = QGroupBox("Add Node")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Coordinates input row
        coord_layout = QHBoxLayout()
        coord_layout.setSpacing(6)
        
        self.x_input = QLineEdit("0")
        self.x_input.setPlaceholderText("Ex: 0.0")
        self.x_input.setMaximumWidth(60)
        
        self.y_input = QLineEdit("0")
        self.y_input.setPlaceholderText("Ex: 0.0")
        self.y_input.setMaximumWidth(60)
        
        self.z_input = QLineEdit("0")
        self.z_input.setPlaceholderText("Ex: 0.0")
        self.z_input.setMaximumWidth(60)
        
        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.x_input)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.y_input)
        coord_layout.addWidget(QLabel("Z:"))
        coord_layout.addWidget(self.z_input)
        
        self.btn_add_node = QPushButton("Add Node")
        self.btn_add_node.setProperty("class", "primary")
        self.btn_add_node.clicked.connect(self.on_add_node)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_node)
        
        layout.addLayout(coord_layout)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def create_bar_section(self):
        group = QGroupBox("Add Bar")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Bar input row
        bar_layout = QHBoxLayout()
        bar_layout.setSpacing(6)
        
        self.i_input = QLineEdit("0")
        self.i_input.setPlaceholderText("Ex: 0")
        self.i_input.setMaximumWidth(50)
        
        self.j_input = QLineEdit("1")
        self.j_input.setPlaceholderText("Ex: 1")
        self.j_input.setMaximumWidth(50)
        
        bar_layout.addWidget(QLabel("Node i:"))
        bar_layout.addWidget(self.i_input)
        bar_layout.addWidget(QLabel("j:"))
        bar_layout.addWidget(self.j_input)
        
        self.btn_add_bar = QPushButton("Add Bar")
        self.btn_add_bar.setProperty("class", "primary")
        self.btn_add_bar.clicked.connect(self.on_add_bar)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_bar)
        
        layout.addLayout(bar_layout)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def create_support_section(self):
        group = QGroupBox("Set Support")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Support input row
        support_layout = QHBoxLayout()
        support_layout.setSpacing(6)
        
        self.sup_node = QLineEdit("0")
        self.sup_node.setPlaceholderText("Ex: 0")
        self.sup_node.setMaximumWidth(50)
        
        self.sup_type = QComboBox()
        self.sup_type.addItems(["none", "roller", "pinned", "fixed"])
        
        support_layout.addWidget(QLabel("Node:"))
        support_layout.addWidget(self.sup_node)
        support_layout.addWidget(QLabel("Type:"))
        support_layout.addWidget(self.sup_type)
        
        self.btn_add_sup = QPushButton("Apply")
        self.btn_add_sup.setProperty("class", "primary")
        self.btn_add_sup.clicked.connect(self.on_add_support)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_sup)
        
        layout.addLayout(support_layout)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def create_point_load_section(self):
        group = QGroupBox("Point Load")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Load input row
        load_layout = QHBoxLayout()
        load_layout.setSpacing(6)
        
        self.load_bar = QLineEdit("0")
        self.load_bar.setPlaceholderText("Ex: 0")
        self.load_bar.setMaximumWidth(45)
        
        self.load_vx = QLineEdit("0")
        self.load_vx.setPlaceholderText("Ex: 0.0")
        self.load_vx.setMaximumWidth(45)
        
        self.load_vy = QLineEdit("0")
        self.load_vy.setPlaceholderText("Ex: -100.0")
        self.load_vy.setMaximumWidth(45)
        
        self.load_vz = QLineEdit("0")
        self.load_vz.setPlaceholderText("Ex: 0.0")
        self.load_vz.setMaximumWidth(45)
        
        load_layout.addWidget(QLabel("Bar:"))
        load_layout.addWidget(self.load_bar)
        load_layout.addWidget(self.load_vx)
        load_layout.addWidget(self.load_vy)
        load_layout.addWidget(self.load_vz)
        
        # Distance row for loads along bars
        dist_layout = QHBoxLayout()
        dist_layout.setSpacing(6)
        
        self.load_distance = QLineEdit("0")
        self.load_distance.setPlaceholderText("Ex: 0.0")
        self.load_distance.setMaximumWidth(60)
        
        dist_layout.addWidget(QLabel("Distance:"))
        dist_layout.addWidget(self.load_distance)
        dist_layout.addWidget(QLabel("(from node i to j)"))
        
        self.btn_add_load = QPushButton("Add Load")
        self.btn_add_load.setProperty("class", "primary")
        self.btn_add_load.clicked.connect(self.on_add_point_load)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_load)
        
        layout.addLayout(load_layout)
        layout.addLayout(dist_layout)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group
    
    def create_node_moment_section(self):
        group = QGroupBox("Node Moment")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Node input
        node_layout = QHBoxLayout()
        node_layout.setSpacing(6)
        
        self.moment_node = QLineEdit("0")
        self.moment_node.setPlaceholderText("Ex: 0")
        self.moment_node.setMaximumWidth(45)
        
        node_layout.addWidget(QLabel("Node:"))
        node_layout.addWidget(self.moment_node)
        
        # Moment components
        moment_comp_layout = QHBoxLayout()
        moment_comp_layout.setSpacing(6)
        
        self.moment_mx = QLineEdit("0")
        self.moment_mx.setPlaceholderText("Mx")
        self.moment_mx.setMaximumWidth(45)
        
        self.moment_my = QLineEdit("0")
        self.moment_my.setPlaceholderText("My")
        self.moment_my.setMaximumWidth(45)
        
        self.moment_mz = QLineEdit("0")
        self.moment_mz.setPlaceholderText("Mz")
        self.moment_mz.setMaximumWidth(45)
        
        moment_comp_layout.addWidget(QLabel("Mx:"))
        moment_comp_layout.addWidget(self.moment_mx)
        moment_comp_layout.addWidget(QLabel("My:"))
        moment_comp_layout.addWidget(self.moment_my)
        moment_comp_layout.addWidget(QLabel("Mz:"))
        moment_comp_layout.addWidget(self.moment_mz)
        
        self.btn_add_moment = QPushButton("Add Moment")
        self.btn_add_moment.setProperty("class", "primary")
        self.btn_add_moment.clicked.connect(self.on_add_node_moment)
        
        moment_button_layout = QHBoxLayout()
        moment_button_layout.addStretch()
        moment_button_layout.addWidget(self.btn_add_moment)
        
        layout.addLayout(node_layout)
        layout.addLayout(moment_comp_layout)
        layout.addLayout(moment_button_layout)
        group.setLayout(layout)
        return group

    def create_dist_load_section(self):
        group = QGroupBox("Distributed Load")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Dist load input row
        dload_layout = QHBoxLayout()
        dload_layout.setSpacing(6)
        
        self.dload_bar = QLineEdit("0")
        self.dload_bar.setPlaceholderText("Ex: 0")
        self.dload_bar.setMaximumWidth(45)
        
        self.dload_dir = QComboBox()
        self.dload_dir.addItems(["vx", "vy", "vz", "perpendicular"])
        self.dload_dir.setMaximumWidth(100)
        
        dload_layout.addWidget(QLabel("Bar:"))
        dload_layout.addWidget(self.dload_bar)
        dload_layout.addWidget(QLabel("Dir:"))
        dload_layout.addWidget(self.dload_dir)
        
        # Expression row
        expr_layout = QHBoxLayout()
        expr_layout.setSpacing(6)
        self.dload_expr = QLineEdit("0")
        self.dload_expr.setPlaceholderText("Ex: 10*t")
        expr_layout.addWidget(QLabel("Expr:"))
        expr_layout.addWidget(self.dload_expr)
        
        self.btn_add_dload = QPushButton("Add Load")
        self.btn_add_dload.setProperty("class", "primary")
        self.btn_add_dload.clicked.connect(self.on_add_dist_load)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_dload)
        
        layout.addLayout(dload_layout)
        layout.addLayout(expr_layout)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

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
        bar = self._safe_int(self.load_bar, 0)
        vx = self._safe_float(self.load_vx, 0.0)
        vy = self._safe_float(self.load_vy, 0.0)
        vz = self._safe_float(self.load_vz, 0.0)
        distance = self._safe_float(self.load_distance, 0.0)
        self.signal_add_point_load.emit({"bar": bar, "vx": vx, "vy": vy, "vz": vz, "distance": distance})

    def on_add_dist_load(self):
        bar = self._safe_int(self.dload_bar, 0)
        expr = self.dload_expr.text().strip() or "0"
        direction = self.dload_dir.currentText()
        self.signal_add_dist_load.emit({"bar": bar, "expr": expr, "direction": direction})

    def on_add_node_moment(self):
        node = self._safe_int(self.moment_node, 0)
        mx = self._safe_float(self.moment_mx, 0.0)
        my = self._safe_float(self.moment_my, 0.0)
        mz = self._safe_float(self.moment_mz, 0.0)
        self.signal_add_node_moment.emit({"node": node, "mx": mx, "my": my, "mz": mz})

    def create_clear_section(self):
        group = QGroupBox("Actions")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.setProperty("class", "primary")
        self.btn_analyze.clicked.connect(self.on_analyze)
        
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setProperty("class", "danger")
        self.btn_clear.clicked.connect(self.on_clear)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_analyze)
        button_layout.addWidget(self.btn_clear)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def on_clear(self):
        self.signal_clear.emit()

    def on_analyze(self):
        self.signal_analyze.emit()