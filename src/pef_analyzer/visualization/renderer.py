"""
Módulo Renderer - Responsável por desenhar a estrutura e visualizar forças no canvas.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtCore import Qt

class Renderer:
    def __init__(self, canvas: QGraphicsView):
        self.canvas = canvas
        self.scene = QGraphicsScene()
        self.canvas.setScene(self.scene)

    def draw_structure(self, nodes, bars):
        self.scene.clear()
        self.draw_nodes(nodes)
        self.draw_bars(bars)

    def draw_nodes(self, nodes):
        for node in nodes:
            x, y = node.position
            self.scene.addEllipse(x - 5, y - 5, 10, 10, QPen(Qt.GlobalColor.black), QColor(Qt.GlobalColor.blue))

    def draw_bars(self, bars):
        for bar in bars:
            start_node = bar.start_node
            end_node = bar.end_node
            self.scene.addLine(start_node.position[0], start_node.position[1],
                               end_node.position[0], end_node.position[1],
                               QPen(QColor(0, 0, 0), 2))

    def visualize_forces(self, forces):
        for force in forces:
            x, y = force.position
            self.scene.addLine(x, y, x + force.magnitude * 10, y, QPen(QColor(255, 0, 0), 2))
            self.scene.addText(f"{force.magnitude} N").setPos(x + force.magnitude * 10, y)

    def clear(self):
        self.scene.clear()
