
import os
import numpy as np
import matplotlib.pyplot as plt
from input_parser import parse_input_file, create_sample_input_file

class ThermalSolver2D:
    def __init__(self, nx, ny, dx, dy, k):
        self.nx = nx  # Number of nodes in x-direction
        self.ny = ny  # Number of nodes in y-direction
        self.dx = dx  # Grid spacing in x-direction
        self.dy = dy  # Grid spacing in y-direction
        self.k = k    # Thermal conductivity

        self.T = np.zeros((ny, nx))  # Temperature grid
        self.q = np.zeros((ny, nx))  # Heat source/sink grid

    def set_boundary_conditions(self, left, right, top, bottom):
        # Set boundary conditions
        self.T[0, :] = bottom   # Bottom
        self.T[-1, :] = top     # Top
        self.T[:, 0] = left     # Left
        self.T[:, -1] = right   # Right

    def solve(self, max_iter=10000, tolerance=1e-6):
        iter_count = 0
        error = float('inf')

        while iter_count < max_iter and error > tolerance:
            T_old = self.T.copy()

            # Interior nodes
            self.T[1:-1, 1:-1] = (
                (self.T[1:-1, 2:] + self.T[1:-1, :-2]) / self.dx**2 +
                (self.T[2:, 1:-1] + self.T[:-2, 1:-1]) / self.dy**2 +
                self.q[1:-1, 1:-1] / self.k
            ) / (2 / self.dx**2 + 2 / self.dy**2)

            # Calculate error
            error = np.max(np.abs(self.T - T_old))
            iter_count += 1

        print(f"Solution converged after {iter_count} iterations")
        return self.T

    def add_heat_source(self, x, y, q):
        self.q[y, x] = q

    def plot_temperature(self):
        plt.figure(figsize=(10, 8))
        plt.imshow(self.T, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Temperature')
        plt.title('2D Temperature Distribution')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.savefig('temperature_distribution.png')
        plt.close()

    def save_results(self, filename='temperature_results.txt'):
        np.savetxt(filename, self.T, fmt='%.4f', delimiter='	')
        print(f"Results saved to {filename}")

def main():
    # Create a sample input file if it doesn't exist
    input_file = 'input.txt'
    if not os.path.exists(input_file):
        create_sample_input_file(input_file)

    # Parse the input file
    config = parse_input_file(input_file)

    # Create and set up the solver
    solver = ThermalSolver2D(
        nx=config['nx'],
        ny=config['ny'],
        dx=config['dx'],
        dy=config['dy'],
        k=config['k']
    )

    # Set boundary conditions
    solver.set_boundary_conditions(
        left=config['left_temp'],
        right=config['right_temp'],
        top=config['top_temp'],
        bottom=config['bottom_temp']
    )

    # Add a heat source
    solver.add_heat_source(
        config['heat_source_x'],
        config['heat_source_y'],
        config['heat_source_q']
    )

    # Solve
    T = solver.solve(max_iter=config['max_iter'], tolerance=config['tolerance'])

    # Plot and save results
    solver.plot_temperature()
    solver.save_results()
    # Example usage
    nx, ny = 50, 50
    dx = dy = 0.1
    k = 1.0

    solver = ThermalSolver2D(nx, ny, dx, dy, k)

    # Set boundary conditions
    solver.set_boundary_conditions(left=0, right=100, top=100, bottom=0)

    # Add a heat source
    solver.add_heat_source(25, 25, 1000)

    # Solve
    T = solver.solve()

    # Plot and save results
    solver.plot_temperature()
    solver.save_results()

if __name__ == "__main__":
    main()
