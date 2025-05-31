class User:

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hi, I'm {self.name}"

    def describe(self):
        status = "adult" if self.age >= 18 else "minor"
        return f"User: {self.name} ({self.age} years old, {status})"