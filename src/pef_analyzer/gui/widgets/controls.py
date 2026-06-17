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
    signal_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Create scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # RightToLeft on the scroll area moves the vertical scrollbar to the left side,
        # keeping it out of the way of the content on the right.
        scroll.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main container widget — reset direction so text/widgets stay left-to-right
        container = QWidget()
        container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(48, 16, 16, 16)
        
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

        # Single row: [Bar: input] --- gap --- [Vx] [Vy] [Vz] --- gap --- [dist]
        input_row = QHBoxLayout()
        input_row.setSpacing(4)

        self.load_bar = QLineEdit("0")
        self.load_bar.setPlaceholderText("Ex: 0")
        self.load_bar.setMaximumWidth(45)

        self.load_vx = QLineEdit("0")
        self.load_vx.setPlaceholderText("Vx")
        self.load_vx.setMaximumWidth(45)

        self.load_vy = QLineEdit("0")
        self.load_vy.setPlaceholderText("Vy")
        self.load_vy.setMaximumWidth(45)

        self.load_vz = QLineEdit("0")
        self.load_vz.setPlaceholderText("Vz")
        self.load_vz.setMaximumWidth(45)

        self.load_distance = QLineEdit("0")
        self.load_distance.setPlaceholderText("d")
        self.load_distance.setMaximumWidth(45)

        input_row.addWidget(QLabel("Bar:"))
        input_row.addWidget(self.load_bar)
        input_row.addSpacing(14)
        input_row.addWidget(self.load_vx)
        input_row.addWidget(self.load_vy)
        input_row.addWidget(self.load_vz)
        input_row.addSpacing(14)
        input_row.addWidget(self.load_distance)
        input_row.addStretch()

        self.btn_add_load = QPushButton("Add Load")
        self.btn_add_load.setProperty("class", "primary")
        self.btn_add_load.clicked.connect(self.on_add_point_load)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_load)

        layout.addLayout(input_row)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group
    
    def create_node_moment_section(self):
        group = QGroupBox("Node Moment")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Single row: [Node: input] --- gap --- [Mx] [My] [Mz]
        input_row = QHBoxLayout()
        input_row.setSpacing(4)

        self.moment_node = QLineEdit("0")
        self.moment_node.setPlaceholderText("Ex: 0")
        self.moment_node.setMaximumWidth(45)

        self.moment_mx = QLineEdit("0")
        self.moment_mx.setPlaceholderText("Mx")
        self.moment_mx.setMaximumWidth(45)

        self.moment_my = QLineEdit("0")
        self.moment_my.setPlaceholderText("My")
        self.moment_my.setMaximumWidth(45)

        self.moment_mz = QLineEdit("0")
        self.moment_mz.setPlaceholderText("Mz")
        self.moment_mz.setMaximumWidth(45)

        input_row.addWidget(QLabel("Node:"))
        input_row.addWidget(self.moment_node)
        input_row.addSpacing(14)
        input_row.addWidget(self.moment_mx)
        input_row.addWidget(self.moment_my)
        input_row.addWidget(self.moment_mz)
        input_row.addStretch()

        self.btn_add_moment = QPushButton("Add Moment")
        self.btn_add_moment.setProperty("class", "primary")
        self.btn_add_moment.clicked.connect(self.on_add_node_moment)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_add_moment)

        layout.addLayout(input_row)
        layout.addLayout(button_layout)
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

    def _mark_err(self, *fields):
        for f in fields:
            f.setStyleSheet("border: 2px solid #f38ba8; border-radius: 4px;")

    def _mark_ok(self, *fields):
        for f in fields:
            f.setStyleSheet("")

    def _try_float(self, field):
        """Return (value, True) or (0.0, False) and highlight field red on failure."""
        text = field.text().strip()
        if not text:
            self._mark_err(field)
            return 0.0, False
        try:
            v = float(text)
            self._mark_ok(field)
            return v, True
        except ValueError:
            self._mark_err(field)
            return 0.0, False

    def _try_int(self, field):
        text = field.text().strip()
        if not text:
            self._mark_err(field)
            return 0, False
        try:
            v = int(text)
            self._mark_ok(field)
            return v, True
        except ValueError:
            self._mark_err(field)
            return 0, False

    def _try_expr(self, field):
        from ...core.load import validate_expr
        expr = field.text().strip()
        try:
            valid = validate_expr(expr)
            self._mark_ok(field)
            return valid, True
        except ValueError as e:
            self._mark_err(field)
            return "0", False

    def on_add_node(self):
        x, ox = self._try_float(self.x_input)
        y, oy = self._try_float(self.y_input)
        z, oz = self._try_float(self.z_input)
        if not (ox and oy and oz):
            self.signal_error.emit("Node: X, Y and Z must be valid numbers.")
            return
        self.signal_add_node.emit({"x": x, "y": y, "z": z})

    def on_add_bar(self):
        i, oi = self._try_int(self.i_input)
        j, oj = self._try_int(self.j_input)
        if not (oi and oj):
            self.signal_error.emit("Bar: Node i and j must be valid integers.")
            return
        if i == j:
            self._mark_err(self.i_input, self.j_input)
            self.signal_error.emit("Bar: Node i and j must be different.")
            return
        self._mark_ok(self.i_input, self.j_input)
        self.signal_add_bar.emit({"i": i, "j": j})

    def on_add_support(self):
        node, ok = self._try_int(self.sup_node)
        if not ok:
            self.signal_error.emit("Support: Node must be a valid integer.")
            return
        st = self.sup_type.currentText()
        self.signal_add_support.emit({"node": node, "type": st})

    def on_add_point_load(self):
        bar, ob  = self._try_int(self.load_bar)
        vx,  ovx = self._try_float(self.load_vx)
        vy,  ovy = self._try_float(self.load_vy)
        vz,  ovz = self._try_float(self.load_vz)
        dist,od  = self._try_float(self.load_distance)
        if not (ob and ovx and ovy and ovz and od):
            self.signal_error.emit("Point Load: All fields must be valid numbers.")
            return
        if dist < 0:
            self._mark_err(self.load_distance)
            self.signal_error.emit("Point Load: Distance must be ≥ 0.")
            return
        self._mark_ok(self.load_distance)
        self.signal_add_point_load.emit({"bar": bar, "vx": vx, "vy": vy, "vz": vz, "distance": dist})

    def on_add_dist_load(self):
        bar, ob = self._try_int(self.dload_bar)
        expr, oe = self._try_expr(self.dload_expr)
        if not ob:
            self.signal_error.emit("Dist Load: Bar must be a valid integer.")
            return
        if not oe:
            self.signal_error.emit("Dist Load: Expression is invalid. Use 't' as variable and standard math functions.")
            return
        direction = self.dload_dir.currentText()
        self.signal_add_dist_load.emit({"bar": bar, "expr": expr, "direction": direction})

    def on_add_node_moment(self):
        node, on_ = self._try_int(self.moment_node)
        mx,   omx = self._try_float(self.moment_mx)
        my,   omy = self._try_float(self.moment_my)
        mz,   omz = self._try_float(self.moment_mz)
        if not (on_ and omx and omy and omz):
            self.signal_error.emit("Moment: All fields must be valid numbers.")
            return
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