"""
Módulo MainWindow - Interface gráfica principal do PEF Analyzer.

Implementa a janela principal com canvas para visualização da estrutura,
diagramas de esforços e área para exibição das equações simbólicas.
"""

from __future__ import annotations
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QSplitter, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QInputDialog, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import sympy as sp

from ..core.domain.node import Node
from ..core.domain.element import Element
from ..core.domain.support import Support, SupportType
from ..core.domain.load import PointLoad, DistributedLoad, LoadDirection
from ..core.solver.analyzer import Analyzer, AnalysisResult


class StructureCanvas(FigureCanvas):
    """
    Canvas Matplotlib para visualização da estrutura.
    """
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Configurações do gráfico
        self.axes.set_aspect('equal')
        self.axes.grid(True, alpha=0.3)
        self.axes.set_xlabel('X (m)')
        self.axes.set_ylabel('Y (m)')
        self.axes.set_title('Geometria da Estrutura')
        
    def clear(self):
        """Limpa o canvas."""
        self.axes.clear()
        self.axes.set_aspect('equal')
        self.axes.grid(True, alpha=0.3)
        self.axes.set_xlabel('X (m)')
        self.axes.set_ylabel('Y (m)')
        self.draw()
    
    def draw_structure(
        self,
        nodes: List[Node],
        elements: List[Element],
        show_loads: bool = True
    ):
        """
        Desenha a estrutura com nós, elementos e cargas.
        
        Args:
            nodes: Lista de nós da estrutura.
            elements: Lista de elementos da estrutura.
            show_loads: Se True, desenha as cargas aplicadas.
        """
        self.clear()
        
        # Desenha elementos
        for elem in elements:
            x_coords = [elem.node_i.x, elem.node_f.x]
            y_coords = [elem.node_i.y, elem.node_f.y]
            self.axes.plot(x_coords, y_coords, 'b-', linewidth=3)
            
            # Adiciona rótulo no meio do elemento
            mid_x = (elem.node_i.x + elem.node_f.x) / 2
            mid_y = (elem.node_i.y + elem.node_f.y) / 2
            self.axes.annotate(
                elem.id,
                (mid_x, mid_y),
                fontsize=8,
                ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7)
            )
        
        # Desenha nós
        for node in nodes:
            # Cor do nó depende se tem apoio
            if node.support:
                if node.support.support_type == SupportType.FIXED:
                    color = 'red'
                    marker = 's'
                elif node.support.support_type == SupportType.PINNED:
                    color = 'orange'
                    marker = '^'
                else:  # ROLLER
                    color = 'green'
                    marker = 'o'
            else:
                color = 'blue'
                marker = 'o'
            
            self.axes.plot(
                node.x, node.y,
                marker=marker,
                markersize=12,
                color=color,
                markeredgecolor='black',
                markeredgewidth=1
            )
            
            # Rótulo do nó
            self.axes.annotate(
                node.id,
                (node.x, node.y),
                textcoords="offset points",
                xytext=(0, 15),
                ha='center',
                fontsize=9,
                fontweight='bold'
            )
            
            # Desenha símbolo do apoio
            if node.support:
                self._draw_support_symbol(node)
            
            # Desenha cargas nodais
            if show_loads and node.loads:
                self._draw_nodal_loads(node)
        
        # Desenha cargas distribuídas nos elementos
        if show_loads:
            for elem in elements:
                # Cargas pontuais em elementos
                for load in elem.point_loads:
                    self._draw_element_point_load(elem, load)
                # Cargas distribuídas
                for load in elem.loads:
                    self._draw_distributed_load(elem, load)
        
        # Ajusta limites
        if nodes:
            x_coords = [n.x for n in nodes]
            y_coords = [n.y for n in nodes]
            margin = 0.1 * max(max(x_coords) - min(x_coords), 
                              max(y_coords) - min(y_coords)) if len(nodes) > 1 else 1
            self.axes.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
            self.axes.set_ylim(min(y_coords) - margin, max(y_coords) + margin)
        
        self.draw()
    
    def _draw_support_symbol(self, node: Node):
        """Desenha o símbolo do tipo de apoio."""
        if not node.support:
            return
        
        size = 0.15
        x, y = node.x, node.y
        
        if node.support.support_type == SupportType.FIXED:
            # Engaste - triângulo preenchido
            triangle = plt.Polygon([
                [x - size, y - size],
                [x + size, y - size],
                [x, y]
            ], fill=True, facecolor='gray', edgecolor='black')
            self.axes.add_patch(triangle)
            
        elif node.support.support_type == SupportType.PINNED:
            # Apoio fixo - triângulo
            triangle = plt.Polygon([
                [x - size, y - size],
                [x + size, y - size],
                [x, y]
            ], fill=False, edgecolor='black', linewidth=2)
            self.axes.add_patch(triangle)
            # Hachura
            for i in range(-3, 4):
                self.axes.plot(
                    [x - size + i*size/3, x - size + (i+1)*size/3],
                    [y - size, y - size - size/3],
                    'k-', linewidth=0.5
                )
                
        elif node.support.support_type == SupportType.ROLLER:
            # Apoio móvel - círculos
            for dx in [-size/2, 0, size/2]:
                circle = plt.Circle((x + dx, y - size*0.7), size/4, 
                                  fill=False, edgecolor='black')
                self.axes.add_patch(circle)
            # Base
            self.axes.plot([x - size, x + size], [y - size, y - size], 'k-', linewidth=2)
    
    def _draw_nodal_loads(self, node: Node):
        """Desenha vetores de carga nos nós com magnitude normalizada."""
        for load in node.loads:
            if load.magnitude == 0:
                continue

            scale = 0.35
            fx_norm = load.fx / load.magnitude * scale
            fy_norm = load.fy / load.magnitude * scale
            
            self.axes.arrow(
                node.x, node.y,
                fx_norm, fy_norm,
                head_width=0.12, head_length=0.14,
                fc='red', ec='darkred', linewidth=2.5,
                length_includes_head=True
            )

            perp_x = -fy_norm
            perp_y = fx_norm
            norm_perp = (perp_x**2 + perp_y**2) ** 0.5
            if norm_perp != 0:
                perp_x /= norm_perp
                perp_y /= norm_perp
            offset = 0.15
            label_x = node.x + fx_norm * 1.4 + perp_x * offset
            label_y = node.y + fy_norm * 1.4 + perp_y * offset
            
            self.axes.text(
                label_x, label_y,
                f'{load.magnitude:.1f}',
                fontsize=9, color='red', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.95),
                clip_on=False
            )
    
    def _draw_element_point_load(self, element: Element, load: PointLoad):
        """Desenha vetores de carga pontual em um elemento."""
        if load.position is None or load.magnitude == 0:
            return
        
        cos_a = element.cos_angle
        sin_a = element.sin_angle
        pos_ratio = load.position / element.length
        global_x = element.node_i.x + pos_ratio * (element.node_f.x - element.node_i.x)
        global_y = element.node_i.y + pos_ratio * (element.node_f.y - element.node_i.y)
        
        magnitude = load.magnitude
        scale = 0.5
        fx_norm = load.fx / magnitude * scale
        fy_norm = load.fy / magnitude * scale
        
        self.axes.arrow(
            global_x, global_y,
            fx_norm, fy_norm,
            head_width=0.13, head_length=0.14,
            fc='orange', ec='darkorange', linewidth=2.5,
            length_includes_head=True
        )
        
        perp_x = -fy_norm
        perp_y = fx_norm
        norm_perp = (perp_x**2 + perp_y**2) ** 0.5
        if norm_perp != 0:
            perp_x /= norm_perp
            perp_y /= norm_perp
        offset = 0.17
        label_x = global_x + fx_norm * 1.45 + perp_x * offset
        label_y = global_y + fy_norm * 1.45 + perp_y * offset
        self.axes.text(
            label_x, label_y,
            f'{load.magnitude:.1f}',
            fontsize=9, color='darkorange', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.95),
            clip_on=False
        )
    
    def _draw_distributed_load(self, element: Element, load: DistributedLoad):
        """Desenha representação da carga distribuída com múltiplos vetores."""
        import numpy as np
        
        a = load.start_position
        b = load.end_position if load.end_position is not None else element.length
        num_vectors = 8
        x_positions = np.linspace(a, b, num_vectors)
        cos_a = element.cos_angle
        sin_a = element.sin_angle
        x_sym = element.local_symbol
        
        for x_pos in x_positions:
            if load.is_sympy:
                try:
                    w_val = float(load.w_function.subs(x_sym, x_pos))
                except:
                    w_val = float(load.w_function) if isinstance(load.w_function, (int, float)) else 0.0
            else:
                w_val = float(load.w_function) if isinstance(load.w_function, (int, float)) else 0.0
            
            global_x = element.node_i.x + x_pos * cos_a
            global_y = element.node_i.y + x_pos * sin_a
            
            if load.direction == LoadDirection.LOCAL_NORMAL:
                vec_x = -sin_a
                vec_y = cos_a
            elif load.direction == LoadDirection.LOCAL_TANGENTIAL:
                vec_x = cos_a
                vec_y = sin_a
            elif load.direction == LoadDirection.GLOBAL_X:
                vec_x = 1.0
                vec_y = 0.0
            elif load.direction == LoadDirection.GLOBAL_Y:
                vec_x = 0.0
                vec_y = 1.0
            else:
                vec_x = -sin_a
                vec_y = cos_a
            
            max_load = 20.0
            scale = abs(w_val) / max_load * 0.75
            scale = min(scale, 1.0)
            vec_x *= scale * (1 if w_val >= 0 else -1)
            vec_y *= scale * (1 if w_val >= 0 else -1)
            
            if load.direction == LoadDirection.LOCAL_NORMAL:
                color = 'purple'
                edge_color = 'darkviolet'
            elif load.direction == LoadDirection.LOCAL_TANGENTIAL:
                color = 'green'
                edge_color = 'darkgreen'
            elif load.direction == LoadDirection.GLOBAL_X:
                color = 'blue'
                edge_color = 'darkblue'
            elif load.direction == LoadDirection.GLOBAL_Y:
                color = 'red'
                edge_color = 'darkred'
            else:
                color = 'purple'
                edge_color = 'darkviolet'
            
            self.axes.arrow(
                global_x, global_y,
                vec_x, vec_y,
                head_width=0.10, head_length=0.10,
                fc=color, ec=edge_color, linewidth=2, alpha=0.9,
                length_includes_head=True
            )
        
        if load.direction == LoadDirection.LOCAL_NORMAL:
            bar_start_x = element.node_i.x + a * cos_a
            bar_start_y = element.node_i.y + a * sin_a
            bar_end_x = element.node_i.x + b * cos_a
            bar_end_y = element.node_i.y + b * sin_a
            
            bar_offset = 0.45
            offset_x = -sin_a * bar_offset
            offset_y = cos_a * bar_offset
            
            self.axes.plot(
                [bar_start_x + offset_x, bar_end_x + offset_x],
                [bar_start_y + offset_y, bar_end_y + offset_y],
                color, linewidth=3, linestyle='--', alpha=0.6
            )


class DiagramsCanvas(FigureCanvas):
    """
    Canvas Matplotlib para os diagramas de esforços internos.
    """
    
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def clear(self):
        """Limpa todos os subplots."""
        self.fig.clear()
        self.draw()
    
    def _find_zeros(self, func: sp.Expr, x: sp.Symbol, x_min: float, x_max: float) -> list:
        """
        Encontra os zeros de uma função no intervalo [x_min, x_max].
        
        Args:
            func: Expressão SymPy
            x: Símbolo da variável
            x_min: Valor mínimo do intervalo
            x_max: Valor máximo do intervalo
            
        Returns:
            Lista de valores x onde a função é zero
        """
        try:
            zeros = sp.solve(func, x)
            valid_zeros = []
            for z in zeros:
                try:
                    z_val = float(z)
                    if x_min <= z_val <= x_max:
                        valid_zeros.append(z_val)
                except (TypeError, ValueError):
                    pass
            return sorted(valid_zeros)
        except Exception:
            return []
    
    def _add_critical_points(self, ax, x_vals: list, y_vals: list, x: sp.Symbol, 
                            func: sp.Expr, L: float, label: str = ''):
        """
        Adiciona marcadores e anotações dos pontos críticos (máx, mín, zeros).
        
        Args:
            ax: Eixo matplotlib
            x_vals: Lista de valores x
            y_vals: Lista de valores y correspondentes
            x: Símbolo SymPy
            func: Função simbólica
            L: Comprimento do elemento
            label: Prefixo do label (ex: 'N', 'V', 'M')
        """
        if not y_vals or len(y_vals) < 2:
            return
        
        # Valores inicial e final
        y_inicio = y_vals[0]
        y_final = y_vals[-1]
        
        # Máximo e mínimo
        y_max = max(y_vals)
        y_min = min(y_vals)
        idx_max = y_vals.index(y_max)
        idx_min = y_vals.index(y_min)
        x_max = x_vals[idx_max]
        x_min = x_vals[idx_min]
        
        # Encontra zeros (cruzamentos com eixo x)
        zeros = self._find_zeros(func, x, 0, L)
        
        # Marca máximo
        if y_max != 0:
            ax.plot(x_max, y_max, 'r^', markersize=8)
            ax.annotate(f'Máx: {y_max:.2f}@{x_max:.2f}m',
                       xy=(x_max, y_max),
                       xytext=(10, 15), textcoords='offset points',
                       fontsize=8, bbox=dict(boxstyle='round,pad=0.4', 
                       facecolor='yellow', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Marca mínimo
        if y_min != 0 and y_min != y_max:
            ax.plot(x_min, y_min, 'rv', markersize=8)
            ax.annotate(f'Mín: {y_min:.2f}@{x_min:.2f}m',
                       xy=(x_min, y_min),
                       xytext=(10, -20), textcoords='offset points',
                       fontsize=8, bbox=dict(boxstyle='round,pad=0.4', 
                       facecolor='cyan', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # Marca valores inicial e final
        ax.plot(0, y_inicio, 'go', markersize=6)
        if abs(y_inicio) > 0.01:
            ax.annotate(f'{y_inicio:.2f}', xy=(0, y_inicio),
                       xytext=(2, 5), textcoords='offset points',
                       fontsize=7, color='green', fontweight='bold')
        
        ax.plot(L, y_final, 'bo', markersize=6)
        if abs(y_final) > 0.01:
            ax.annotate(f'{y_final:.2f}', xy=(L, y_final),
                       xytext=(-20, 5), textcoords='offset points',
                       fontsize=7, color='blue', fontweight='bold')
        
        # Marca zeros (cruzamentos com eixo x)
        for z_val in zeros:
            ax.plot(z_val, 0, 'ks', markersize=6)
            ax.annotate(f'Zero@{z_val:.2f}m',
                       xy=(z_val, 0),
                       xytext=(0, -25), textcoords='offset points',
                       fontsize=7, bbox=dict(boxstyle='round,pad=0.3', 
                       facecolor='lightgray', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', lw=0.5))
    
    def draw_diagrams(
        self,
        result: AnalysisResult,
        elements: List[Element],
        element_id: Optional[str] = None
    ):
        """
        Desenha os diagramas de esforços internos com pontos críticos marcados.
        
        Args:
            result: Resultado da análise estrutural.
            elements: Lista de elementos (para obter comprimentos reais).
            element_id: ID do elemento específico (None = todos).
        """
        self.clear()
        
        elements_to_plot = [element_id] if element_id else list(result.internal_forces.keys())
        num_elements = len(elements_to_plot)
        
        if num_elements == 0:
            return
        
        # Cria subplots para N, V e M
        gs = self.fig.add_gridspec(3, num_elements, hspace=0.8, wspace=0.4)
        
        for col, elem_id in enumerate(elements_to_plot):
            if elem_id not in result.internal_forces:
                continue
            
            # Encontra o elemento para obter o comprimento real
            elem = next((e for e in elements if e.id == elem_id), None)
            if elem is None:
                continue
                
            forces = result.internal_forces[elem_id]
            x = forces.x
            L = elem.length  # Usa o comprimento real do elemento
            
            # Posições para avaliação - de 0 a L
            x_vals = [i * L / 50 for i in range(51)]
            
            # Avalia funções
            N_vals = [float(forces.N.subs(x, xv)) for xv in x_vals]
            V_vals = [float(forces.V.subs(x, xv)) for xv in x_vals]
            M_vals = [float(forces.M.subs(x, xv)) for xv in x_vals]
            
            # Esforço Normal
            ax_n = self.fig.add_subplot(gs[0, col])
            ax_n.fill_between(x_vals, 0, N_vals, alpha=0.28, color='blue')
            ax_n.plot(x_vals, N_vals, 'b-', linewidth=2.2)
            ax_n.axhline(y=0, color='k', linewidth=0.8)
            ax_n.set_xlim(0, L)
            ax_n.set_title(f'N(x) - {elem_id}', fontsize=10)
            ax_n.set_ylabel('N (kN)', fontsize=9)
            ax_n.grid(True, alpha=0.35, linestyle='--')
            ax_n.tick_params(axis='both', labelsize=8)
            self._add_critical_points(ax_n, x_vals, N_vals, x, forces.N, L, 'N')
            
            # Esforço Cortante
            ax_v = self.fig.add_subplot(gs[1, col])
            ax_v.fill_between(x_vals, 0, V_vals, alpha=0.28, color='green')
            ax_v.plot(x_vals, V_vals, 'g-', linewidth=2.2)
            ax_v.axhline(y=0, color='k', linewidth=0.8)
            ax_v.set_xlim(0, L)
            ax_v.set_title(f'V(x) - {elem_id}', fontsize=10)
            ax_v.set_ylabel('V (kN)', fontsize=9)
            ax_v.grid(True, alpha=0.35, linestyle='--')
            ax_v.tick_params(axis='both', labelsize=8)
            self._add_critical_points(ax_v, x_vals, V_vals, x, forces.V, L, 'V')
            
            # Momento Fletor
            ax_m = self.fig.add_subplot(gs[2, col])
            ax_m.fill_between(x_vals, 0, M_vals, alpha=0.28, color='red')
            ax_m.plot(x_vals, M_vals, 'r-', linewidth=2.2)
            ax_m.axhline(y=0, color='k', linewidth=0.8)
            ax_m.set_xlim(0, L)
            ax_m.set_title(f'M(x) - {elem_id}', fontsize=10)
            ax_m.set_ylabel('M (kN·m)', fontsize=9)
            ax_m.set_xlabel(f'x (m) - Eixo da barra {elem_id}', fontsize=9)
            ax_m.grid(True, alpha=0.35, linestyle='--')
            ax_m.tick_params(axis='both', labelsize=8)
            self._add_critical_points(ax_m, x_vals, M_vals, x, forces.M, L, 'M')
        
        self.fig.tight_layout(pad=2.2)
        self.draw()


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação PEF Analyzer.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PEF Analyzer - Análise de Estruturas")
        self.setMinimumSize(1400, 900)
        
        # Dados da estrutura
        self.nodes: List[Node] = []
        self.elements: List[Element] = []
        self.analysis_result: Optional[AnalysisResult] = None
        self._load_entries: list[tuple] = []
        
        self._setup_ui()
        self._setup_menu()
    
    def _setup_ui(self):
        """Configura a interface do usuário."""
        # Widget central com splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Painel esquerdo - Controles e dados
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Painel direito - Visualização
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Proporções do splitter
        main_splitter.setSizes([400, 1000])
    
    def _create_left_panel(self) -> QWidget:
        """Cria o painel esquerdo com controles."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Grupo: Nós
        nodes_group = QGroupBox("Nós")
        nodes_layout = QVBoxLayout(nodes_group)
        
        self.nodes_table = QTableWidget(0, 4)
        self.nodes_table.setHorizontalHeaderLabels(['ID', 'X (m)', 'Y (m)', 'Apoio'])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        nodes_layout.addWidget(self.nodes_table)
        
        nodes_buttons = QHBoxLayout()
        btn_add_node = QPushButton("Adicionar Nó")
        btn_add_node.clicked.connect(self._add_node)
        btn_remove_node = QPushButton("Remover")
        btn_remove_node.clicked.connect(self._remove_node)
        nodes_buttons.addWidget(btn_add_node)
        nodes_buttons.addWidget(btn_remove_node)
        nodes_layout.addLayout(nodes_buttons)
        
        layout.addWidget(nodes_group)
        
        # Grupo: Elementos
        elements_group = QGroupBox("Elementos")
        elements_layout = QVBoxLayout(elements_group)
        
        self.elements_table = QTableWidget(0, 4)
        self.elements_table.setHorizontalHeaderLabels(['ID', 'Nó I', 'Nó F', 'Tipo'])
        self.elements_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        elements_layout.addWidget(self.elements_table)
        
        elem_buttons = QHBoxLayout()
        btn_add_elem = QPushButton("Adicionar Elemento")
        btn_add_elem.clicked.connect(self._add_element)
        btn_remove_elem = QPushButton("Remover")
        btn_remove_elem.clicked.connect(self._remove_element)
        elem_buttons.addWidget(btn_add_elem)
        elem_buttons.addWidget(btn_remove_elem)
        elements_layout.addLayout(elem_buttons)
        
        layout.addWidget(elements_group)
        
        # Grupo: Cargas
        loads_group = QGroupBox("Cargas")
        loads_layout = QVBoxLayout(loads_group)
        
        self.loads_table = QTableWidget(0, 5)
        self.loads_table.setHorizontalHeaderLabels(['Tipo', 'Local', 'Fx (kN)', 'Fy (kN)', 'w (kN/m)'])
        self.loads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        loads_layout.addWidget(self.loads_table)
        
        loads_buttons = QHBoxLayout()
        btn_add_point_load = QPushButton("Carga Nodal")
        btn_add_point_load.clicked.connect(self._add_point_load)
        btn_add_elem_load = QPushButton("Carga em Elemento")
        btn_add_elem_load.clicked.connect(self._add_element_point_load)
        btn_add_dist_load = QPushButton("Carga Distribuída")
        btn_add_dist_load.clicked.connect(self._add_distributed_load)
        btn_remove_load = QPushButton("Remover")
        btn_remove_load.clicked.connect(self._remove_load)
        loads_buttons.addWidget(btn_add_point_load)
        loads_buttons.addWidget(btn_add_elem_load)
        loads_buttons.addWidget(btn_add_dist_load)
        loads_buttons.addWidget(btn_remove_load)
        loads_layout.addLayout(loads_buttons)
        
        layout.addWidget(loads_group)
        
        # Botão Analisar
        btn_analyze = QPushButton("ANALISAR ESTRUTURA")
        btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_analyze.clicked.connect(self._run_analysis)
        layout.addWidget(btn_analyze)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Cria o painel direito com visualização."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Canvas da estrutura
        structure_label = QLabel("Visualização da Estrutura")
        structure_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(structure_label)
        
        self.structure_canvas = StructureCanvas(self, width=8, height=5)
        layout.addWidget(self.structure_canvas)
        
        # Toolbar do matplotlib
        toolbar = NavigationToolbar(self.structure_canvas, self)
        layout.addWidget(toolbar)
        
        # Canvas dos diagramas
        diagrams_label = QLabel("Diagramas de Esforços Internos")
        diagrams_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(diagrams_label)
        
        self.diagrams_canvas = DiagramsCanvas(self, width=10, height=6)
        layout.addWidget(self.diagrams_canvas)
        
        # Área de equações
        equations_group = QGroupBox("Equações Analíticas (SymPy)")
        equations_layout = QVBoxLayout(equations_group)
        
        self.equations_text = QTextEdit()
        self.equations_text.setReadOnly(True)
        self.equations_text.setFont(QFont("Consolas", 10))
        equations_layout.addWidget(self.equations_text)
        
        layout.addWidget(equations_group)
        
        return panel
    
    def _setup_menu(self):
        """Configura a barra de menus."""
        menubar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menubar.addMenu('Arquivo')
        
        new_action = QAction('Novo', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Exemplos
        examples_menu = menubar.addMenu('Exemplos')
        
        beam_simple_action = QAction('Viga Simples', self)
        beam_simple_action.triggered.connect(self._load_simple_beam_example)
        examples_menu.addAction(beam_simple_action)
        
        cantilever_action = QAction('Viga em Balanço', self)
        cantilever_action.triggered.connect(self._load_cantilever_example)
        examples_menu.addAction(cantilever_action)
    
    def _add_node(self):
        """Adiciona um novo nó."""
        # Diálogo para entrada de dados
        x, ok1 = QInputDialog.getDouble(self, "Nó", "Coordenada X (m):", 0, -1000, 1000, 3)
        if not ok1:
            return
        y, ok2 = QInputDialog.getDouble(self, "Nó", "Coordenada Y (m):", 0, -1000, 1000, 3)
        if not ok2:
            return
        
        # Tipo de apoio
        support_types = ['Nenhum', 'Roller (1º gênero)', 'Pinned (2º gênero)', 'Fixed (3º gênero)']
        support_idx, ok3 = QInputDialog.getItem(
            self, "Apoio", "Tipo de vínculo:", support_types, 0, False
        )
        if not ok3:
            return
        
        # Cria o nó
        node_id = f"N{len(self.nodes)}"
        node = Node(x=x, y=y, id=node_id)
        
        # Adiciona apoio se necessário
        if support_idx == 'Roller (1º gênero)':
            node.set_support(Support(SupportType.ROLLER))
        elif support_idx == 'Pinned (2º gênero)':
            node.set_support(Support(SupportType.PINNED))
        elif support_idx == 'Fixed (3º gênero)':
            node.set_support(Support(SupportType.FIXED))
        
        self.nodes.append(node)
        self._update_nodes_table()
        self._update_structure_view()
    
    def _remove_node(self):
        """Remove o nó selecionado."""
        row = self.nodes_table.currentRow()
        if row >= 0 and row < len(self.nodes):
            self.nodes.pop(row)
            self._update_nodes_table()
            self._update_structure_view()
    
    def _add_element(self):
        """Adiciona um novo elemento."""
        if len(self.nodes) < 2:
            QMessageBox.warning(self, "Erro", "É necessário pelo menos 2 nós.")
            return
        
        # Lista de nós para seleção
        node_ids = [n.id for n in self.nodes]
        
        node_i_id, ok1 = QInputDialog.getItem(
            self, "Elemento", "Nó inicial:", node_ids, 0, False
        )
        if not ok1:
            return
        
        node_f_id, ok2 = QInputDialog.getItem(
            self, "Elemento", "Nó final:", node_ids, 0, False
        )
        if not ok2:
            return
        
        if node_i_id == node_f_id:
            QMessageBox.warning(self, "Erro", "Nós inicial e final devem ser diferentes.")
            return
        
        node_i = next(n for n in self.nodes if n.id == node_i_id)
        node_f = next(n for n in self.nodes if n.id == node_f_id)
        
        elem_id = f"E{len(self.elements)}"
        element = Element(node_i=node_i, node_f=node_f, id=elem_id)
        self.elements.append(element)
        
        self._update_elements_table()
        self._update_structure_view()
    
    def _remove_element(self):
        """Remove o elemento selecionado."""
        row = self.elements_table.currentRow()
        if row >= 0 and row < len(self.elements):
            self.elements.pop(row)
            self._update_elements_table()
            self._update_structure_view()
    
    def _add_point_load(self):
        """Adiciona carga pontual nodal."""
        if not self.nodes:
            QMessageBox.warning(self, "Erro", "Não há nós disponíveis.")
            return
        
        node_ids = [n.id for n in self.nodes]
        node_id, ok = QInputDialog.getItem(
            self, "Carga Pontual", "Nó:", node_ids, 0, False
        )
        if not ok:
            return
        
        fx, ok1 = QInputDialog.getDouble(self, "Carga", "Componente Fx (kN):", 0, -10000, 10000, 3)
        if not ok1:
            return
        
        fy, ok2 = QInputDialog.getDouble(self, "Carga", "Componente Fy (kN):", -10, -10000, 10000, 3)
        if not ok2:
            return
        
        node = next(n for n in self.nodes if n.id == node_id)
        node.add_load(PointLoad(fx=fx, fy=fy))
        
        self._update_loads_table()
        self._update_structure_view()
        QMessageBox.information(self, "Sucesso", f"Carga adicionada ao nó {node_id}")
    
    def _add_element_point_load(self):
        """Adiciona carga pontual em um elemento (não nodal)."""
        if not self.elements:
            QMessageBox.warning(self, "Erro", "Não há elementos disponíveis.")
            return
        
        elem_ids = [e.id for e in self.elements]
        elem_id, ok = QInputDialog.getItem(
            self, "Carga em Elemento", "Elemento:", elem_ids, 0, False
        )
        if not ok:
            return
        
        element = next(e for e in self.elements if e.id == elem_id)
        
        position, ok1 = QInputDialog.getDouble(
            self, "Carga em Elemento", f"Posição no elemento (0 a {element.length:.2f} m):", 
            element.length / 2, 0, element.length, 3
        )
        if not ok1:
            return
        
        fy, ok2 = QInputDialog.getDouble(
            self, "Carga", "Componente Fy (kN):", -10, -10000, 10000, 3
        )
        if not ok2:
            return
        
        fx, ok3 = QInputDialog.getDouble(
            self, "Carga", "Componente Fx (kN):", 0, -10000, 10000, 3
        )
        if not ok3:
            return
        
        element.add_point_load(PointLoad(fx=fx, fy=fy, position=position))
        
        self._update_loads_table()
        self._update_structure_view()
        QMessageBox.information(self, "Sucesso", f"Carga adicionada ao elemento {elem_id} na posição {position:.2f}m")

    
    def _add_distributed_load(self):
        """Adiciona carga distribuída a um elemento com direção configurável."""
        if not self.elements:
            QMessageBox.warning(self, "Erro", "Não há elementos disponíveis.")
            return
        
        elem_ids = [e.id for e in self.elements]
        elem_id, ok = QInputDialog.getItem(
            self, "Carga Distribuída", "Elemento:", elem_ids, 0, False
        )
        if not ok:
            return
        
        directions = ['LOCAL_NORMAL', 'LOCAL_TANGENTIAL', 'GLOBAL_X', 'GLOBAL_Y']
        direction, ok_dir = QInputDialog.getItem(
            self, "Direção", "Direção da carga:", directions, 0, False
        )
        if not ok_dir:
            return
        
        w_val, ok1 = QInputDialog.getDouble(
            self, "Carga", "Carga uniforme w (kN/m):", -10, -10000, 10000, 3
        )
        if not ok1:
            return
        
        element = next(e for e in self.elements if e.id == elem_id)
        load_dir = LoadDirection[direction]
        element.add_load(DistributedLoad(w_function=w_val, direction=load_dir))
        
        self._update_loads_table()
        self._update_structure_view()
        QMessageBox.information(self, "Sucesso", 
            f"Carga distribuída adicionada ao elemento {elem_id}\nDireção: {direction}")
    
    def _remove_load(self):
        """Remove a carga selecionada."""
        row = self.loads_table.currentRow()
        if row < 0 or row >= len(self._load_entries):
            QMessageBox.warning(self, "Erro", "Selecione uma carga para remover.")
            return
        
        load_type, source, load_obj, position = self._load_entries[row]
        if load_type == 'Nodal':
            node = source
            if load_obj in node.loads:
                node.loads.remove(load_obj)
        elif load_type == 'Elemento':
            element = source
            if load_obj in element.point_loads:
                element.point_loads.remove(load_obj)
        elif load_type == 'Distribuída':
            element = source
            if load_obj in element.loads:
                element.loads.remove(load_obj)
        
        self.analysis_result = None
        self._update_loads_table()
        self._update_structure_view()
        self.diagrams_canvas.clear()
        self.equations_text.clear()
        QMessageBox.information(self, "Remoção", "Carga removida com sucesso.")
    
    def _update_loads_table(self):
        """Atualiza a tabela de cargas."""
        all_loads = []
        self._load_entries = []
        
        # Cargas nodais
        for node in self.nodes:
            for load in node.loads:
                entry = ('Nodal', node, load, None)
                all_loads.append((entry, node.id, load.fx, load.fy, None))
                self._load_entries.append(entry)
        
        # Cargas em elementos
        for elem in self.elements:
            for load in elem.point_loads:
                if load.position is not None:
                    entry = ('Elemento', elem, load, load.position)
                    all_loads.append((entry, f'{elem.id} @ {load.position:.2f}m', load.fx, load.fy, None))
                    self._load_entries.append(entry)
            for load in elem.loads:
                try:
                    w_val = float(load.w_function) if isinstance(load.w_function, (int, float)) else str(load.w_function)
                except Exception:
                    w_val = str(load.w_function)
                entry = ('Distribuída', elem, load, None)
                all_loads.append((entry, elem.id, None, None, w_val))
                self._load_entries.append(entry)
        
        # Atualiza tabela
        self.loads_table.setRowCount(len(all_loads))
        for i, (entry, local, fx, fy, w) in enumerate(all_loads):
            self.loads_table.setItem(i, 0, QTableWidgetItem(entry[0]))
            self.loads_table.setItem(i, 1, QTableWidgetItem(str(local)))
            self.loads_table.setItem(i, 2, QTableWidgetItem(f"{fx:.2f}" if fx is not None else "—"))
            self.loads_table.setItem(i, 3, QTableWidgetItem(f"{fy:.2f}" if fy is not None else "—"))
            self.loads_table.setItem(i, 4, QTableWidgetItem(str(w) if w is not None else "—"))

    
    def _update_nodes_table(self):
        """Atualiza a tabela de nós."""
        self.nodes_table.setRowCount(len(self.nodes))
        for i, node in enumerate(self.nodes):
            self.nodes_table.setItem(i, 0, QTableWidgetItem(node.id))
            self.nodes_table.setItem(i, 1, QTableWidgetItem(f"{node.x:.3f}"))
            self.nodes_table.setItem(i, 2, QTableWidgetItem(f"{node.y:.3f}"))
            support_str = ""
            if node.support:
                support_str = node.support.support_type.name
            self.nodes_table.setItem(i, 3, QTableWidgetItem(support_str))
    
    def _update_elements_table(self):
        """Atualiza a tabela de elementos."""
        self.elements_table.setRowCount(len(self.elements))
        for i, elem in enumerate(self.elements):
            self.elements_table.setItem(i, 0, QTableWidgetItem(elem.id))
            self.elements_table.setItem(i, 1, QTableWidgetItem(elem.node_i.id))
            self.elements_table.setItem(i, 2, QTableWidgetItem(elem.node_f.id))
            self.elements_table.setItem(i, 3, QTableWidgetItem(elem.element_type.name))
    
    def _update_structure_view(self):
        """Atualiza a visualização da estrutura."""
        self.structure_canvas.draw_structure(self.nodes, self.elements)
    
    def _run_analysis(self):
        """Executa a análise estrutural."""
        if not self.nodes or not self.elements:
            QMessageBox.warning(self, "Erro", "Defina pelo menos um nó e um elemento.")
            return
        
        try:
            analyzer = Analyzer(nodes=self.nodes, elements=self.elements)
            self.analysis_result = analyzer.analyze()
            
            # Atualiza diagramas passando a lista de elementos
            self.diagrams_canvas.draw_diagrams(self.analysis_result, self.elements)
            
            # Atualiza visualização da estrutura (para mostrar cargas)
            self._update_structure_view()
            
            # Atualiza equações
            self._update_equations_display()
            
            QMessageBox.information(self, "Análise Concluída", 
                f"Grau de hiperestaticidade: {self.analysis_result.degree_of_indeterminacy}\n"
                f"Isostática: {'Sim' if self.analysis_result.isostatic else 'Não'}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro na Análise", str(e))
    
    def _update_equations_display(self):
        """Atualiza a exibição das equações simbólicas."""
        if not self.analysis_result:
            self.equations_text.setText("Nenhuma análise realizada.")
            return
        
        text = "=== REAÇÕES DE APOIO ===\n\n"
        for node_id, reactions in self.analysis_result.reactions.items():
            text += f"Nó {node_id}:\n"
            for comp, value in reactions.items():
                if value is not None:
                    text += f"  {comp} = {value:.4f} kN\n"
                else:
                    text += f"  {comp} = Indeterminado\n"
            text += "\n"
        
        text += "\n=== ESFORÇOS INTERNOS (Funções Simbólicas) ===\n\n"
        if not self.analysis_result.internal_forces:
            text += "Nenhum esforço interno calculado.\n"
        else:
            for elem_id, forces in self.analysis_result.internal_forces.items():
                text += f"Elemento {elem_id}:\n"
                text += f"  N(x) = {str(sp.simplify(forces.N))}\n"
                text += f"  V(x) = {str(sp.simplify(forces.V))}\n"
                text += f"  M(x) = {str(sp.simplify(forces.M))}\n"
                text += "\n"
        
        self.equations_text.setText(text)
    
    def _new_project(self):
        """Limpa todos os dados para novo projeto."""
        self.nodes.clear()
        self.elements.clear()
        self.analysis_result = None
        self._update_nodes_table()
        self._update_elements_table()
        self._update_loads_table()
        self.structure_canvas.clear()
        self.diagrams_canvas.clear()
        self.equations_text.clear()
    
    def _load_simple_beam_example(self):
        """Carrega exemplo de viga simples."""
        self._new_project()
        
        # Viga simples apoiada: 0m e 6m, carga no meio
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.PINNED))
        
        n2 = Node(x=6, y=0, id="B")
        n2.set_support(Support(SupportType.ROLLER))
        
        self.nodes = [n1, n2]
        
        beam = Element(node_i=n1, node_f=n2, id="Viga")
        
        # Carga distribuída uniforme
        beam.add_load(DistributedLoad(w_function=-10.0))
        
        self.elements = [beam]
        
        self._update_nodes_table()
        self._update_elements_table()
        self._update_loads_table()
        self._update_structure_view()
    
    def _load_cantilever_example(self):
        """Carrega exemplo de viga em balanço."""
        self._new_project()
        
        # Engaste em A, carga na ponta
        n1 = Node(x=0, y=0, id="A")
        n1.set_support(Support(SupportType.FIXED))
        
        n2 = Node(x=4, y=0, id="B")
        
        self.nodes = [n1, n2]
        
        beam = Element(node_i=n1, node_f=n2, id="Balanço")
        
        # Carga pontual na ponta
        n2.add_load(PointLoad(fy=-20.0))
        
        self.elements = [beam]
        
        self._update_nodes_table()
        self._update_elements_table()
        self._update_loads_table()
        self._update_structure_view()
