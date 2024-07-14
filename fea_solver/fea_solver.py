
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
    def __init__(self, nodes, node_indices, material, area):
        super().__init__(nodes, material)
        self.area = area
        self.node_indices = node_indices
        self.dofs = [node_idx * 2 for node_idx in node_indices] + [node_idx * 2 + 1 for node_idx in node_indices]

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
        u = displacements[self.dofs].flatten()
        strain = B.dot(u)
        stress = self.material.E * strain
        return stress

class BeamElement(Element):
    def __init__(self, nodes, node_indices, material, moment_of_inertia):
        super().__init__(nodes, material)
        self.moment_of_inertia = moment_of_inertia
        self.node_indices = node_indices
        self.dofs = [node_idx * 2 for node_idx in node_indices] + [node_idx * 2 + 1 for node_idx in node_indices]

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
    def __init__(self, nodes, elements, materials, constraints):
        self.nodes = nodes
        self.elements = elements
        self.materials = materials
        self.constraints = constraints

    def solve(self):
        n_dofs = len(self.nodes) * 2
        K = self._assemble_stiffness_matrix(n_dofs)
        F = self._assemble_force_vector(n_dofs)
        U = self._apply_constraints(K, F)
        self._calculate_stresses(U)
        return U

    def _assemble_stiffness_matrix(self, n_dofs):
        data = []
        rows = []
        cols = []

        for element in self.elements:
            ke = element.stiffness_matrix()
            dofs = element.dofs

            for i in range(len(dofs)):
                for j in range(len(dofs)):
                    data.append(ke[i,j])
                    rows.append(dofs[i])
                    cols.append(dofs[j])

        K = coo_matrix((data, (rows, cols)), shape=(n_dofs, n_dofs)).tocsc()
        return K

    def _assemble_force_vector(self, n_dofs):
        # Placeholder for assembling the force vector
        return np.zeros(n_dofs)

    
def _apply_constraints(self, K, F):
    # Apply point loads
    for node, force in self.point_loads.items():
        dof = node.idx * 2
        F[dof] += force[0]
        F[dof + 1] += force[1]

    # Apply distributed loads
    for element, load in self.distributed_loads.items():
        element_dofs = element.dofs
        element_force = element.distribute_load(load)
        F[element_dofs] += element_force

    # Apply prescribed displacements
    for node, displacement in self.prescribed_displacements.items():
        dof = node.idx * 2
        K[dof, :] = 0
        K[dof, dof] = 1
        F[dof] = displacement[0]
        
        K[dof + 1, :] = 0
        K[dof + 1, dof + 1] = 1
        F[dof + 1] = displacement[1]

    return np.linalg.solve(K, F)
def _assemble_stiffness_matrix(self, n_dofs):
    data = []
    rows = []
    cols = []

    for element in self.elements:
        ke = element.stiffness_matrix()
        dofs = element.dofs

        for i in range(len(dofs)):
            for j in range(len(dofs)):
                data.append(ke[i,j])
                rows.append(dofs[i])
                cols.append(dofs[j])

    K = coo_matrix((data, (rows, cols)), shape=(n_dofs, n_dofs)).tocsc()
    return K



def create_truss_element(node_indices, nodes, material, area):
    return TrussElement(nodes[node_indices], node_indices, material, area)

def create_beam_element(node_indices, nodes, material, moment_of_inertia):
    return BeamElement(nodes[node_indices], node_indices, material, moment_of_inertia)