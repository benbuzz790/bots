# Thermal Solver 2D

This Python script implements a 2D steady-state heat conduction solver using the finite difference method.

## Usage

1. Ensure you have Python installed with numpy and matplotlib libraries.
2. Run the script: python thermal_solver.py
3. The script will create a sample input file (input.txt) if it doesn't exist, solve the problem, and generate results.

## Input File Format

The solver uses a text-based input file (default: input.txt) to configure the problem. Each line in the file should be in the format:

parameter_name = value

Comments can be added using '#' at the beginning of a line.

### Parameters:

1. Grid configuration:
   - nx: Number of nodes in x-direction (int)
   - ny: Number of nodes in y-direction (int)
   - dx: Grid spacing in x-direction (float)
   - dy: Grid spacing in y-direction (float)

2. Material properties:
   - k: Thermal conductivity (float)

3. Boundary conditions:
   - left_temp: Temperature at the left boundary (float)
   - right_temp: Temperature at the right boundary (float)
   - top_temp: Temperature at the top boundary (float)
   - bottom_temp: Temperature at the bottom boundary (float)

4. Heat source:
   - heat_source_x: x-coordinate of the heat source (int)
   - heat_source_y: y-coordinate of the heat source (int)
   - heat_source_q: Strength of the heat source (float)

5. Solver settings:
   - max_iter: Maximum number of iterations (int)
   - tolerance: Convergence tolerance (float)

## Example Input File:

# Grid configuration
nx = 50
ny = 50
dx = 0.1
dy = 0.1

# Material properties
k = 1.0

# Boundary conditions
left_temp = 0
right_temp = 100
top_temp = 100
bottom_temp = 0

# Heat source
heat_source_x = 25
heat_source_y = 25
heat_source_q = 1000

# Solver settings
max_iter = 10000
tolerance = 1e-6

## Output

The solver generates two output files:
1. temperature_results.txt: A text file containing the temperature values for each node in the grid.
2. temperature_distribution.png: A visual representation of the temperature distribution.

## Modifying the Solver

To solve different problems, simply modify the input.txt file with your desired parameters. You can change the grid size, material properties, boundary conditions, heat source location and strength, and solver settings to suit your specific thermal conduction problem.
