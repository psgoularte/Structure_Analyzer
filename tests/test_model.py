import unittest
from src.pef_analyzer.core.node import Node
from src.pef_analyzer.core.bar import Bar
from src.pef_analyzer.core.load import Load

class TestModel(unittest.TestCase):

    def setUp(self):
        self.node = Node(position=(0, 0), constraints={'x': True, 'y': False})
        self.bar = Bar(length=5.0, material='Steel')
        self.load = Load(force=10.0, direction=(1, 0))

    def test_node_creation(self):
        self.assertEqual(self.node.position, (0, 0))
        self.assertEqual(self.node.constraints, {'x': True, 'y': False})

    def test_bar_creation(self):
        self.assertEqual(self.bar.length, 5.0)
        self.assertEqual(self.bar.material, 'Steel')

    def test_load_creation(self):
        self.assertEqual(self.load.force, 10.0)
        self.assertEqual(self.load.direction, (1, 0))

if __name__ == '__main__':
    unittest.main()