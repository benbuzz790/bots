
import numpy as np

class Force:
    def __init__(self, node_id, force_vector):
        self.node_id = node_id
        self.force_vector = np.array(force_vector)

class FixedSupport:
    def __init__(self, node_id):
        self.node_id = node_id

class BoundaryConditions:
    def __init__(self):
        self.forces = []
        self.fixed_supports = []

    def add_force(self, force):
        self.forces.append(force)

    def add_fixed_support(self, fixed_support):
        self.fixed_supports.append(fixed_support)

    def get_force_vector(self, num_nodes):
        force_vector = np.zeros((num_nodes, 3))
        for force in self.forces:
            force_vector[force.node_id] += force.force_vector
        return force_vector.flatten()

    def get_fixed_dofs(self):
        return [node_id * 3 + i for node_id in self.fixed_supports for i in range(3)]
