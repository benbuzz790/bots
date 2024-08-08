import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
import tests.lazy_functions as lazy_functions

class TestLazyDecorator(unittest.TestCase):
    def setUp(self):
        # Reset lazy functions before each test
        lazy_functions.reset_lazy_functions()
        # Re-import the functions after reset
        from lazy_functions import (
            calculate_average,
            transform_data,
            build_octree,
            find_shortest_path,
            optimize_resource_allocation,
            OctreeNode
        )
        self.calculate_average = calculate_average
        self.transform_data = transform_data
        self.build_octree = build_octree
        self.find_shortest_path = find_shortest_path
        self.optimize_resource_allocation = optimize_resource_allocation
        self.OctreeNode = OctreeNode

    def test_calculate_average(self):
        result = self.calculate_average([1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertAlmostEqual(result, 3.0, places=6)

    def test_transform_data(self):
        input_data = [1, 2, 3, 4, 5]
        result = self.transform_data(input_data)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(input_data))
        self.assertNotEqual(result, input_data)
        self.assertTrue(all(isinstance(x, int) for x in result))

    def test_build_octree(self):
        points = [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (7.0, 8.0, 9.0)]
        result = self.build_octree(points, max_depth=3)
        self.assertIsInstance(result, self.OctreeNode)
        self.assertTrue(hasattr(result, 'children'))
        self.assertTrue(hasattr(result, 'points'))

    def test_find_shortest_path(self):
        graph = {
            'A': {'B': 4, 'C': 2},
            'B': {'D': 3},
            'C': {'D': 1, 'E': 5},
            'D': {'E': 2},
            'E': {}
        }
        result = self.find_shortest_path(graph, 'A', 'E')
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], 'A')
        self.assertEqual(result[-1], 'E')
        self.assertIn(result, [['A', 'C', 'D', 'E'], ['A', 'B', 'D', 'E']])

    def test_optimize_resource_allocation(self):
        resources = {'CPU': 8, 'RAM': 32, 'GPU': 2}
        tasks = [
            {'id': 'Task1', 'requirements': {'CPU': 2, 'RAM': 8}},
            {'id': 'Task2', 'requirements': {'CPU': 1, 'RAM': 4, 'GPU': 1}},
            {'id': 'Task3', 'requirements': {'CPU': 4, 'RAM': 16}}
        ]
        result = self.optimize_resource_allocation(resources, tasks)
        self.assertIsInstance(result, dict)
        self.assertTrue(all(isinstance(v, list) for v in result.values()))
        self.assertTrue(all(task['id'] in [item for sublist in result.values() for item in sublist] for task in tasks))

    def test_analyze_time_series(self):
        data = [10.0, 12.0, 15.0, 14.0, 16.0, 18.0, 17.0, 20.0, 21.0, 22.0]
        timestamps = list(range(0, 100, 10))
        result = self.analyze_time_series(data, timestamps)
        self.assertIsInstance(result, dict)
        self.assertTrue(any(key in result for key in ['trend', 'seasonality', 'forecast', 'anomalies']))

if __name__ == '__main__':
    unittest.main()