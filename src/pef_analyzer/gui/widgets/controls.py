"""
Módulo Controls - Elementos de interface do usuário para interação com a aplicação.
Remodelado com abas e layouts em grade para melhor usabilidade (UX).
"""
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSlider, QLabel,
    QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFrame,
    QScrollArea, QSizePolicy, QTabWidget, QGridLayout
)


class Controls(QWidget):
    # Sinais enviam dicionário com parâmetros (mantidos idênticos para compatibilidade)
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
        # Layout principal vertical do painel de controle
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Criar o Widget de Abas (Tabs) para organizar o fluxo de modelagem
        self.tabs = QTabWidget()

        #TAB 1: GEOMETRIA (Nós e Barras)
        geom_tab = QWidget()
        geom_layout = QVBoxLayout(geom_tab)
        geom_layout.setSpacing(12)
        geom_layout.setContentsMargins(4, 8, 4, 4)
        geom_layout.addWidget(self.create_node_section())
        geom_layout.addWidget(self.create_bar_section())
        geom_layout.addStretch()  # Empurra o conteúdo para o topo
        self.tabs.addTab(geom_tab, "Geometria")

        # TAB 2: RESTRIÇÕES (Apoios e Vínculos)
        rest_tab = QWidget()
        rest_layout = QVBoxLayout(rest_tab)
        rest_layout.setSpacing(12)
        rest_layout.setContentsMargins(4, 8, 4, 4)
        rest_layout.addWidget(self.create_support_section())
        rest_layout.addStretch()
        self.tabs.addTab(rest_tab, "Restrições")

        #TAB 3: CARGAS (Pontuais, Distribuídas e Momentos) com ScrollArea dedicado
        loads_scroll = QScrollArea()
        loads_scroll.setWidgetResizable(True)
        loads_scroll.setFrameShape(QFrame.Shape.NoFrame)
        loads_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        loads_container = QWidget()
        loads_layout = QVBoxLayout(loads_container)
        loads_layout.setSpacing(12)
        loads_layout.setContentsMargins(4, 8, 4, 4)
        loads_layout.addWidget(self.create_point_load_section())
        loads_layout.addWidget(self.create_dist_load_section())
        loads_layout.addWidget(self.create_node_moment_section())
        loads_layout.addStretch()

        loads_scroll.setWidget(loads_container)
        self.tabs.addTab(loads_scroll, "Cargas")

        # Adiciona o bloco de abas ao layout principal
        main_layout.addWidget(self.tabs)

        # SEÇÃO DE AÇÕES (Fixa permanentemente no rodapé)
        actions_group = self.create_clear_section()
        main_layout.addWidget(actions_group)

        self.setLayout(main_layout)

    def create_node_section(self):
        group = QGroupBox("Add Node")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.x_input = QLineEdit("0")
        self.x_input.setPlaceholderText("0.0")
        self.y_input = QLineEdit("0")
        self.y_input.setPlaceholderText("0.0")
        self.z_input = QLineEdit("0")
        self.z_input.setPlaceholderText("0.0")
        
        grid.addWidget(QLabel("X (m):"), 0, 0)
        grid.addWidget(self.x_input, 0, 1)
        grid.addWidget(QLabel("Y (m):"), 0, 2)
        grid.addWidget(self.y_input, 0, 3)
        grid.addWidget(QLabel("Z (m):"), 1, 0)
        grid.addWidget(self.z_input, 1, 1)
        
        self.btn_add_node = QPushButton("Add Node")
        self.btn_add_node.setProperty("class", "primary")
        self.btn_add_node.clicked.connect(self.on_add_node)
        
        layout.addLayout(grid)
        layout.addWidget(self.btn_add_node, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group

    def create_bar_section(self):
        group = QGroupBox("Add Bar")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.i_input = QLineEdit("0")
        self.i_input.setPlaceholderText("0")
        self.j_input = QLineEdit("1")
        self.j_input.setPlaceholderText("1")
        
        grid.addWidget(QLabel("Node i (Início):"), 0, 0)
        grid.addWidget(self.i_input, 0, 1)
        grid.addWidget(QLabel("Node j (Fim):"), 0, 2)
        grid.addWidget(self.j_input, 0, 3)
        
        self.btn_add_bar = QPushButton("Add Bar")
        self.btn_add_bar.setProperty("class", "primary")
        self.btn_add_bar.clicked.connect(self.on_add_bar)
        
        layout.addLayout(grid)
        layout.addWidget(self.btn_add_bar, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group

    def create_support_section(self):
        group = QGroupBox("Set Support")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.sup_node = QLineEdit("0")
        self.sup_node.setPlaceholderText("0")
        self.sup_type = QComboBox()
        self.sup_type.addItems(["none", "roller", "pinned", "fixed"])
        
        grid.addWidget(QLabel("Node ID:"), 0, 0)
        grid.addWidget(self.sup_node, 0, 1)
        grid.addWidget(QLabel("Support Type:"), 0, 2)
        grid.addWidget(self.sup_type, 0, 3)
        
        self.btn_add_sup = QPushButton("Apply Support")
        self.btn_add_sup.setProperty("class", "primary")
        self.btn_add_sup.clicked.connect(self.on_add_support)
        
        layout.addLayout(grid)
        layout.addWidget(self.btn_add_sup, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group

    def create_point_load_section(self):
        group = QGroupBox("Point Load")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()

        grid = QGridLayout()
        grid.setSpacing(8)

        self.load_bar = QLineEdit("0")
        self.load_distance = QLineEdit("0")
        self.load_vx = QLineEdit("0")
        self.load_vy = QLineEdit("0")
        self.load_vz = QLineEdit("0")

        grid.addWidget(QLabel("Bar ID:"), 0, 0)
        grid.addWidget(self.load_bar, 0, 1)
        grid.addWidget(QLabel("Dist. (m):"), 0, 2)
        grid.addWidget(self.load_distance, 0, 3)

        grid.addWidget(QLabel("Vx (kN):"), 1, 0)
        grid.addWidget(self.load_vx, 1, 1)
        grid.addWidget(QLabel("Vy (kN):"), 1, 2)
        grid.addWidget(self.load_vy, 1, 3)
        grid.addWidget(QLabel("Vz (kN):"), 2, 0)
        grid.addWidget(self.load_vz, 2, 1)

        self.btn_add_load = QPushButton("Add Point Load")
        self.btn_add_load.setProperty("class", "primary")
        self.btn_add_load.clicked.connect(self.on_add_point_load)

        layout.addLayout(grid)
        layout.addWidget(self.btn_add_load, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group
    
    def create_node_moment_section(self):
        group = QGroupBox("Node Moment")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()

        grid = QGridLayout()
        grid.setSpacing(8)

        self.moment_node = QLineEdit("0")
        self.moment_mx = QLineEdit("0")
        self.moment_my = QLineEdit("0")
        self.moment_mz = QLineEdit("0")

        grid.addWidget(QLabel("Node ID:"), 0, 0)
        grid.addWidget(self.moment_node, 0, 1)

        grid.addWidget(QLabel("Mx (kN·m):"), 1, 0)
        grid.addWidget(self.moment_mx, 1, 1)
        grid.addWidget(QLabel("My (kN·m):"), 1, 2)
        grid.addWidget(self.moment_my, 1, 3)
        grid.addWidget(QLabel("Mz (kN·m):"), 2, 0)
        grid.addWidget(self.moment_mz, 2, 1)

        self.btn_add_moment = QPushButton("Add Moment")
        self.btn_add_moment.setProperty("class", "primary")
        self.btn_add_moment.clicked.connect(self.on_add_node_moment)

        layout.addLayout(grid)
        layout.addWidget(self.btn_add_moment, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group

    def create_dist_load_section(self):
        group = QGroupBox("Distributed Load")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        self.dload_bar = QLineEdit("0")
        self.dload_dir = QComboBox()
        self.dload_dir.addItems(["vx", "vy", "vz", "perpendicular"])
        self.dload_expr = QLineEdit("0")
        
        grid.addWidget(QLabel("Bar ID:"), 0, 0)
        grid.addWidget(self.dload_bar, 0, 1)
        grid.addWidget(QLabel("Direction:"), 0, 2)
        grid.addWidget(self.dload_dir, 0, 3)
        
        grid.addWidget(QLabel("Expression:"), 1, 0)
        grid.addWidget(self.dload_expr, 1, 1, 1, 3)  # Expande a caixa pelas colunas restantes
        
        self.btn_add_dload = QPushButton("Add Dist Load")
        self.btn_add_dload.setProperty("class", "primary")
        self.btn_add_dload.clicked.connect(self.on_add_dist_load)
        
        layout.addLayout(grid)
        layout.addWidget(self.btn_add_dload, alignment=Qt.AlignmentFlag.AlignRight)
        group.setLayout(layout)
        return group

    def create_clear_section(self):
        group = QGroupBox("Actions")
        group.setProperty("class", "section-title")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        self.btn_analyze = QPushButton("Analyze Structure")
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

    # ── MÉTODOS AUXILIARES E DE VALIDAÇÃO (MANTIDOS 100% INTACTOS) ──────────
    def _safe_float(self, lineedit, default=0.0):
        try: return float(lineedit.text())
        except Exception: return default

    def _safe_int(self, lineedit, default=0):
        try: return int(lineedit.text())
        except Exception: return default

    def _mark_err(self, *fields):
        for f in fields: f.setStyleSheet("border: 2px solid #f38ba8; border-radius: 4px;")

    def _mark_ok(self, *fields):
        for f in fields: f.setStyleSheet("")

    def _try_float(self, field):
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

    def on_clear(self): self.signal_clear.emit()
    def on_analyze(self): self.signal_analyze.emit()