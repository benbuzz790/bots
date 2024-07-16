
class Material:
    def __init__(self, name, young_modulus, poisson_ratio, density):
        self.name = name
        self.young_modulus = young_modulus
        self.poisson_ratio = poisson_ratio
        self.density = density

    def __str__(self):
        return f"Material: {self.name}"

class MaterialLibrary:
    def __init__(self):
        self.materials = {}

    def add_material(self, material):
        self.materials[material.name] = material

    def get_material(self, name):
        return self.materials.get(name)

    def remove_material(self, name):
        if name in self.materials:
            del self.materials[name]

# Pre-defined materials
steel = Material("Steel", 200e9, 0.3, 7850)
aluminum = Material("Aluminum", 69e9, 0.33, 2700)
titanium = Material("Titanium", 114e9, 0.34, 4430)

# Create a default material library
default_library = MaterialLibrary()
default_library.add_material(steel)
default_library.add_material(aluminum)
default_library.add_material(titanium)
