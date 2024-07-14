
import numpy as np
from fea_solver import FEASolver, Material, create_truss_element, create_beam_element

def run_truss_example():
    print("Running truss example...")
    nodes = np.array([[0, 0], [3, 0], [3, 3]])
    material = Material(young_modulus=200e9, poisson_ratio=0.3)
    elements = [
        create_truss_element([0, 1], nodes, material, area=0.01),
        create_truss_element([1, 2], nodes, material, area=0.01),
        create_truss_element([0, 2], nodes, material, area=0.01)
    ]
    forces = np.array([0, 0, 0, 0, 0, -1000])
    fixed_dofs = np.array([0, 1, 2, 3])
    solver = FEASolver(nodes, elements, forces, fixed_dofs)

    U = solver.solve()
    print("Displacements:")
    print(U)

    stresses = solver.calculate_stresses(U)
    print("Stresses:")
    print(stresses)

    solver.visualize(U, scale=100)

def run_beam_example():
    print("Running beam example...")
    beam_nodes = np.array([[0, 0], [5, 0]])
    beam_material = Material(young_modulus=200e9, poisson_ratio=0.3)
    beam_element = create_beam_element([0, 1], beam_nodes, beam_material, moment_of_inertia=1e-5)
    beam_forces = np.array([0, 0, 0, 0, 0, -1000])
    beam_fixed_dofs = np.array([0, 1, 2])
    beam_solver = FEASolver(beam_nodes, [beam_element], beam_forces, beam_fixed_dofs)
    
    U = beam_solver.solve()
    print("Displacements:")
    print(U)

    beam_solver.visualize(U, scale=10)

if __name__ == '__main__':
    run_truss_example()
    run_beam_example()
