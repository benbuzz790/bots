
import unittest
import numpy as np
from fea_solver import FEASolver, Material, create_truss_element, create_beam_element

class TestFEASolver(unittest.TestCase):
    def setUp(self):
        self.nodes = np.array([[0, 0], [3, 0], [3, 3]])
        self.material = Material(young_modulus=200e9, poisson_ratio=0.3)
        self.elements = [
            create_truss_element([0, 1], self.nodes, self.material, area=0.01),
            create_truss_element([1, 2], self.nodes, self.material, area=0.01),
            create_truss_element([0, 2], self.nodes, self.material, area=0.01)
        ]
        self.forces = np.array([0, 0, 0, 0, 0, -1000])
        self.fixed_dofs = np.array([0, 1, 2, 3])
        self.solver = FEASolver(self.nodes, self.elements, self.forces, self.fixed_dofs)

    def test_solve(self):
        U = self.solver.solve()
        self.assertEqual(len(U), 6)
        self.assertAlmostEqual(U[0], 0, places=10)
        self.assertAlmostEqual(U[1], 0, places=10)
        self.assertAlmostEqual(U[2], 0, places=10)
        self.assertAlmostEqual(U[3], 0, places=10)
        self.assertLess(U[4], 0)  # Vertical displacement should be negative
        self.assertLess(U[5], 0)  # Vertical displacement should be negative

    def test_stiffness_matrix(self):
        K = self.solver._assemble_stiffness_matrix(6)
        self.assertEqual(K.shape, (6, 6))
        self.assertGreater(np.sum(K.diagonal()), 0)  # Diagonal elements should be positive

    def test_stress_calculation(self):
        U = self.solver.solve()
        stresses = self.solver.calculate_stresses(U)
        self.assertEqual(len(stresses), 3)  # One stress value for each truss element
        self.assertGreater(np.abs(stresses[2]), np.abs(stresses[0]))  # Diagonal member should have higher stress

    def test_beam_element(self):
        beam_nodes = np.array([[0, 0], [5, 0]])
        beam_material = Material(young_modulus=200e9, poisson_ratio=0.3)
        beam_element = create_beam_element([0, 1], beam_nodes, beam_material, moment_of_inertia=1e-5)
        beam_forces = np.array([0, 0, 0, 0, 0, -1000])
        beam_fixed_dofs = np.array([0, 1, 2])
        beam_solver = FEASolver(beam_nodes, [beam_element], beam_forces, beam_fixed_dofs)
        
        U = beam_solver.solve()
        self.assertEqual(len(U), 6)
        self.assertAlmostEqual(U[0], 0, places=10)
        self.assertAlmostEqual(U[1], 0, places=10)
        self.assertAlmostEqual(U[2], 0, places=10)
        self.assertLess(U[4], 0)  # Vertical displacement should be negative
        self.assertLess(U[5], 0)  # Rotation should be negative

if __name__ == '__main__':
    unittest.main()
