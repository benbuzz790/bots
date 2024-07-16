
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

class FEASolver:
    def __init__(self, mesh, material, boundary_conditions):
        self.mesh = mesh
        self.material = material
        self.boundary_conditions = boundary_conditions
        self.K = None
        self.f = None
        self.u = None

    def assemble_stiffness_matrix(self):
        num_nodes = self.mesh.get_num_nodes()
        num_elements = self.mesh.get_num_elements()
        
        rows, cols, data = [], [], []
        
        for elem in range(num_elements):
            elem_nodes = self.mesh.get_element_nodes(elem)
            elem_coords = self.mesh.get_node_coordinates(elem_nodes)
            
            # Compute element stiffness matrix (simplified for tetrahedral elements)
            B = self.compute_B_matrix(elem_coords)
            V = self.mesh.calculate_element_volume(elem)
            D = self.compute_D_matrix()
            
            Ke = V * np.dot(np.dot(B.T, D), B)
            
            # Assemble into global stiffness matrix
            for i in range(12):
                for j in range(12):
                    rows.append(elem_nodes[i//3]*3 + i%3)
                    cols.append(elem_nodes[j//3]*3 + j%3)
                    data.append(Ke[i, j])
        
        self.K = coo_matrix((data, (rows, cols)), shape=(num_nodes*3, num_nodes*3)).tocsr()

    def compute_B_matrix(self, elem_coords):
        # Simplified B matrix computation for tetrahedral elements
        x = elem_coords[:, 0]
        y = elem_coords[:, 1]
        z = elem_coords[:, 2]
        
        vol = np.abs(np.dot(x[1:] - x[0], np.cross(y[1:] - y[0], z[1:] - z[0]))) / 6
        
        a = np.array([
            [y[1]*(z[2]-z[3]) + y[2]*(z[3]-z[1]) + y[3]*(z[1]-z[2])],
            [y[2]*(z[3]-z[0]) + y[3]*(z[0]-z[2]) + y[0]*(z[2]-z[3])],
            [y[3]*(z[0]-z[1]) + y[0]*(z[1]-z[3]) + y[1]*(z[3]-z[0])],
            [y[0]*(z[1]-z[2]) + y[1]*(z[2]-z[0]) + y[2]*(z[0]-z[1])]
        ])
        
        b = np.array([
            [z[1]*(x[2]-x[3]) + z[2]*(x[3]-x[1]) + z[3]*(x[1]-x[2])],
            [z[2]*(x[3]-x[0]) + z[3]*(x[0]-x[2]) + z[0]*(x[2]-x[3])],
            [z[3]*(x[0]-x[1]) + z[0]*(x[1]-x[3]) + z[1]*(x[3]-x[0])],
            [z[0]*(x[1]-x[2]) + z[1]*(x[2]-x[0]) + z[2]*(x[0]-x[1])]
        ])
        
        c = np.array([
            [x[1]*(y[2]-y[3]) + x[2]*(y[3]-y[1]) + x[3]*(y[1]-y[2])],
            [x[2]*(y[3]-y[0]) + x[3]*(y[0]-y[2]) + x[0]*(y[2]-y[3])],
            [x[3]*(y[0]-y[1]) + x[0]*(y[1]-y[3]) + x[1]*(y[3]-y[0])],
            [x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1])]
        ])
        
        B = np.zeros((6, 12))
        for i in range(4):
            B[0, i*3] = a[i] / (6*vol)
            B[1, i*3+1] = b[i] / (6*vol)
            B[2, i*3+2] = c[i] / (6*vol)
            B[3, i*3] = b[i] / (6*vol)
            B[3, i*3+1] = a[i] / (6*vol)
            B[4, i*3+1] = c[i] / (6*vol)
            B[4, i*3+2] = b[i] / (6*vol)
            B[5, i*3] = c[i] / (6*vol)
            B[5, i*3+2] = a[i] / (6*vol)
        
        return B

    def compute_D_matrix(self):
        E = self.material.young_modulus
        v = self.material.poisson_ratio
        
        D = np.array([
            [1-v, v, v, 0, 0, 0],
            [v, 1-v, v, 0, 0, 0],
            [v, v, 1-v, 0, 0, 0],
            [0, 0, 0, (1-2*v)/2, 0, 0],
            [0, 0, 0, 0, (1-2*v)/2, 0],
            [0, 0, 0, 0, 0, (1-2*v)/2]
        ]) * (E / ((1+v) * (1-2*v)))
        
        return D

    def solve(self):
        self.assemble_stiffness_matrix()
        
        num_nodes = self.mesh.get_num_nodes()
        f = self.boundary_conditions.get_force_vector(num_nodes)
        fixed_dofs = self.boundary_conditions.get_fixed_dofs()
        
        # Apply boundary conditions
        free_dofs = list(set(range(num_nodes*3)) - set(fixed_dofs))
        Kff = self.K[free_dofs, :][:, free_dofs]
        ff = f[free_dofs]
        
        # Solve the system
        uf = spsolve(Kff, ff)
        
        # Reconstruct full displacement vector
        self.u = np.zeros(num_nodes*3)
        self.u[free_dofs] = uf

    def calculate_stresses(self):
        num_elements = self.mesh.get_num_elements()
        stresses = np.zeros((num_elements, 6))  # 6 stress components per element
        
        D = self.compute_D_matrix()
        
        for elem in range(num_elements):
            elem_nodes = self.mesh.get_element_nodes(elem)
            elem_coords = self.mesh.get_node_coordinates(elem_nodes)
            
            B = self.compute_B_matrix(elem_coords)
            
            elem_displacements = self.u[np.array([3*node + i for node in elem_nodes for i in range(3)])]
            
            elem_strain = np.dot(B, elem_displacements)
            elem_stress = np.dot(D, elem_strain)
            
            stresses[elem] = elem_stress
        
        return stresses

    def get_displacements(self):
        return self.u.reshape(-1, 3)

    def get_von_mises_stress(self, stresses):
        von_mises = np.sqrt(0.5 * ((stresses[:, 0] - stresses[:, 1])**2 + 
                                   (stresses[:, 1] - stresses[:, 2])**2 + 
                                   (stresses[:, 2] - stresses[:, 0])**2 + 
                                   6*(stresses[:, 3]**2 + stresses[:, 4]**2 + stresses[:, 5]**2)))
        return von_mises
