
import numpy as np

class MeshHandler:
    def __init__(self, vertices, faces):
        self.vertices = np.array(vertices)
        self.faces = np.array(faces)

    def get_num_elements(self):
        return len(self.faces)

    def get_num_nodes(self):
        return len(self.vertices)

    def get_element_nodes(self, element_id):
        return self.vertices[self.faces[element_id]]

    def get_node_coordinates(self, node_id):
        return self.vertices[node_id]

    def calculate_element_volume(self, element_id):
        nodes = self.get_element_nodes(element_id)
        a, b, c = nodes[1] - nodes[0], nodes[2] - nodes[0], nodes[3] - nodes[0]
        return abs(np.dot(a, np.cross(b, c))) / 6

    def calculate_total_volume(self):
        return sum(self.calculate_element_volume(i) for i in range(self.get_num_elements()))
