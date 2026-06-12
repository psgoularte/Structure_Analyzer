import unittest
from src.pef_analyzer.io.project_io import load_project, save_project

class TestIOFunctions(unittest.TestCase):

    def setUp(self):
        self.test_project_data = {
            'nodes': [],
            'bars': [],
            'loads': []
        }
        self.test_file_path = 'test_project.json'

    def test_save_project(self):
        save_project(self.test_file_path, self.test_project_data)
        with open(self.test_file_path, 'r') as f:
            data = f.read()
        self.assertIn('nodes', data)
        self.assertIn('bars', data)
        self.assertIn('loads', data)

    def test_load_project(self):
        save_project(self.test_file_path, self.test_project_data)
        loaded_data = load_project(self.test_file_path)
        self.assertEqual(loaded_data['nodes'], self.test_project_data['nodes'])
        self.assertEqual(loaded_data['bars'], self.test_project_data['bars'])
        self.assertEqual(loaded_data['loads'], self.test_project_data['loads'])

    def tearDown(self):
        import os
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

if __name__ == '__main__':
    unittest.main()