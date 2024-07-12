
def parse_input_file(filename):
    config = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=')
                key = key.strip()
                value = value.strip()
                try:
                    # Try to convert to int or float if possible
                    config[key] = int(value)
                except ValueError:
                    try:
                        config[key] = float(value)
                    except ValueError:
                        config[key] = value
    return config

def create_sample_input_file(filename='input.txt'):
    sample_input = """
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
"""
    with open(filename, 'w') as file:
        file.write(sample_input.strip())
    print(f"Sample input file created: {filename}")

if __name__ == "__main__":
    create_sample_input_file()
    config = parse_input_file('input.txt')
    print("Parsed configuration:")
    for key, value in config.items():
        print(f"{key}: {value}")
