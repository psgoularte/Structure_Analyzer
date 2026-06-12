"""
Módulo Model - Define o modelo de dados para a análise, incluindo classes para nós, barras e cargas.
"""

class Node:
    def __init__(self, id, position, constraints=None):
        self.id = id
        self.position = position
        self.constraints = constraints if constraints is not None else []

    def add_constraint(self, constraint):
        self.constraints.append(constraint)

    def __repr__(self):
        return f"Node(id={self.id}, position={self.position}, constraints={self.constraints})"


class Bar:
    def __init__(self, id, start_node, end_node, length, material):
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.length = length
        self.material = material

    def __repr__(self):
        return f"Bar(id={self.id}, start_node={self.start_node.id}, end_node={self.end_node.id}, length={self.length}, material={self.material})"


class Load:
    def __init__(self, id, magnitude, direction, application_point):
        self.id = id
        self.magnitude = magnitude
        self.direction = direction
        self.application_point = application_point

    def __repr__(self):
        return f"Load(id={self.id}, magnitude={self.magnitude}, direction={self.direction}, application_point={self.application_point})"