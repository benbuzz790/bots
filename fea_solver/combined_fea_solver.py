
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt

class Material:
    def __init__(self, young_modulus, poisson_ratio):
        self.E = young_modulus
        self.nu = poisson_ratio

class Element:
    def __init__(self, nodes, material):
        self.nodes = np.array(nodes)
        self.material = material

    def stiffness_matrix(self):
        raise NotImplementedError("Subclass must implement stiffness_matrix method")

class TrussElement(Element):
    def __init__(self, nodes, material, area):
        super().__init__(nodes, material)
        self.area = area

    def stiffness_matrix(self):
        node1, node2 = self.nodes
        L = np.linalg.norm(node2 - node1)
        c = (node2[0] - node1[0]) / L
        s = (node2[1] - node1[1]) / L
        
        k = (self.material.E * self.area / L) * np.array([
            [c*c, c*s, -c*c, -c*s],
            [c*s, s*s, -c*s, -s*s],
            [-c*c, -c*s, c*c, c*s],
            [-c*s, -s*s, c*s, s*s]
        ])
        return k

    def stress(self, displacements):
        node1, node2 = self.nodes
        L = np.linalg.norm(node2 - node1)
        c = (node2[0] - node1[0]) / L
        s = (node2[1] - node1[1]) / L
        
        B = np.array([-c, -s, c, s]) / L
        u = displacements[self.nodes].flatten()
        strain = B.dot(u)
        stress = self.material.E * strain
        return stress

class BeamElement(Element):
    def __init__(self, nodes, material, moment_of_inertia):
        super().__init__(nodes, material)
        self.moment_of_inertia = moment_of_inertia

    def stiffness_matrix(self):
        node1, node2 = self.nodes
        L = np.linalg.norm(node2 - node1)
        EI = self.material.E * self.moment_of_inertia
        
        k = (EI / L**3) * np.array([
            [12, 6*L, -12, 6*L],
            [6*L, 4*L**2, -6*L, 2*L**2],
            [-12, -6*L, 12, -6*L],
            [6*L, 2*L**2, -6*L, 4*L**2]
        ])
        return k

class FEASolver:
    def __init__(self, nodes, elements, forces, fixed_dofs):
        self.nodes = np.array(nodes)
        self.elements = elements
        self.forces = np.array(forces)
        self.fixed_dofs = np.array(fixed_dofs)
        
    def solve(self):
        n_dofs = len(self.nodes) * 2
        
        # Create global stiffness matrix
        K = self._assemble_stiffness_matrix(n_dofs)
        
        # Apply boundary conditions
        K, F = self._apply_boundary_conditions(K, self.forces, self.fixed_dofs)
        
        # Solve the system
        U = spsolve(K, F)
        
        return U
    
    def _assemble_stiffness_matrix(self, n_dofs):
        rows, cols, data = [], [], []
        
        for el in self.elements:
            ke = el.stiffness_matrix()
            ndofs = ke.shape[0]
            el_dofs = np.array([node * 2 + i for node in el.nodes for i in range(2)])
            
            for i in range(ndofs):
                for j in range(ndofs):
                    rows.append(el_dofs[i])
                    cols.append(el_dofs[j])
                    data.append(ke[i, j])
        
        K = coo_matrix((np.array(data), (np.array(rows), np.array(cols))), shape=(n_dofs, n_dofs)).tocsc()
        return K
    
    def _apply_boundary_conditions(self, K, F, fixed_dofs):
        for dof in fixed_dofs:
            K[dof, :] = 0
            K[dof, dof] = 1
            F[dof] = 0
        return K, F

    def calculate_stresses(self, displacements):
        stresses = []
        for el in self.elements:
            if isinstance(el, TrussElement):
                stress = el.stress(displacements)
                stresses.append(stress)
        return np.array(stresses)

    def visualize(self, displacements, scale=1.0):
        plt.figure(figsize=(10, 8))
        
        # Plot original structure
        for el in self.elements:
            x = [self.nodes[el.nodes[0]][0], self.nodes[el.nodes[1]][0]]
            y = [self.nodes[el.nodes[0]][1], self.nodes[el.nodes[1]][1]]
            plt.plot(x, y, 'b-')
        
        # Plot deformed structure
        deformed_nodes = self.nodes + scale * displacements.reshape(-1, 2)
        for el in self.elements:
            x = [deformed_nodes[el.nodes[0]][0], deformed_nodes[el.nodes[1]][0]]
            y = [deformed_nodes[el.nodes[0]][1], deformed_nodes[el.nodes[1]][1]]
            plt.plot(x, y, 'r--')
        
        plt.axis('equal')
        plt.title('FEA Results (Blue: Original, Red: Deformed)')
        plt.show()

def run_truss_example():
    print("Running truss example...")
    nodes = np.array([[0, 0], [3, 0], [3, 3]])
    material = Material(young_modulus=200e9, poisson_ratio=0.3)
    elements = [
        TrussElement([nodes[0], nodes[1]], material, area=0.01),
        TrussElement([nodes[1], nodes[2]], material, area=0.01),
        TrussElement([nodes[0], nodes[2]], material, area=0.01)
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
    beam_element = BeamElement([beam_nodes[0], beam_nodes[1]], beam_material, moment_of_inertia=1e-5)
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
