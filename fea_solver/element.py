
import numpy as np

class TrussElement:
    def __init__(self, node1, node2, material=None, area=1.0):
        self.node1 = node1
        self.node2 = node2
        self.material = material
        self.area = area
        self.dofs = [node1.idx * 2, node1.idx * 2 + 1, node2.idx * 2, node2.idx * 2 + 1]

    def stiffness_matrix(self):
        E = self.material.E if self.material else 1.0
        A = self.area
        L = np.sqrt((self.node2.x - self.node1.x)**2 + (self.node2.y - self.node1.y)**2)
        c = (self.node2.x - self.node1.x) / L
        s = (self.node2.y - self.node1.y) / L
        k = E * A / L
        return k * np.array([[c**2, c*s, -c**2, -c*s],
                             [c*s, s**2, -c*s, -s**2],
                             [-c**2, -c*s, c**2, c*s],
                             [-c*s, -s**2, c*s, s**2]])

class BeamElement:
    def __init__(self, node1, node2, material=None, area=1.0, I=1.0):
        self.node1 = node1
        self.node2 = node2
        self.material = material
        self.area = area
        self.I = I
        self.dofs = [node1.idx * 2, node1.idx * 2 + 1, node2.idx * 2, node2.idx * 2 + 1]

    def stiffness_matrix(self):
        E = self.material.E if self.material else 1.0
        A = self.area
        I = self.I
        L = np.sqrt((self.node2.x - self.node1.x)**2 + (self.node2.y - self.node1.y)**2)
        c = (self.node2.x - self.node1.x) / L
        s = (self.node2.y - self.node1.y) / L
        k1 = E * A / L
        k2 = 12 * E * I / L**3
        k3 = 6 * E * I / L**2
        k4 = 2 * E * I / L
        return np.array([[k1*c**2+k2*s**2, (k1-k2)*c*s, -k1*c**2-k2*s**2, -(k1-k2)*c*s],
                         [(k1-k2)*c*s, k1*s**2+k2*c**2, -(k1-k2)*c*s, -k1*s**2-k2*c**2],
                         [-k1*c**2-k2*s**2, -(k1-k2)*c*s, k1*c**2+k2*s**2, (k1-k2)*c*s],
                         [-(k1-k2)*c*s, -k1*s**2-k2*c**2, (k1-k2)*c*s, k1*s**2+k2*c**2]])
