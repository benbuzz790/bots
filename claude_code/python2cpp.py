import os
import bot_tools

def is_python_file(filename):
    return filename.endswith('.py')

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def translate_to_cpp():
    cpp_code = """
#include <iostream>
#include <fstream>
#include <string>

int fibonacci(int n) {
    if (n <= 1)
        return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

bool isPythonFile(const std::string& filename) {
    return filename.substr(filename.find_last_of(".") + 1) == "py";
}

std::string translateToPython() {
    return R"(
import os
import bot_tools

def is_python_file(filename):
    return filename.endswith('.py')

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def translate_to_cpp():
    cpp_code = '''
#include <iostream>
#include <fstream>
#include <string>

int fibonacci(int n) {
    if (n <= 1)
        return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

bool isPythonFile(const std::string& filename) {
    return filename.substr(filename.find_last_of(".") + 1) == "py";
}

std::string translateToPython() {
    // Python code here (escaped)
}

int main() {
    std::cout << "Fibonacci sequence up to 10th number:" << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << fibonacci(i) << " ";
    }
    std::cout << std::endl;

    std::string filename = __FILE__;
    if (isPythonFile(filename)) {
        std::cout << "Error: This file is already a Python file." << std::endl;
        return 1;
    }

    std::string pythonCode = translateToPython();
    std::string newFilename = filename.substr(0, filename.find_last_of(".")) + ".py";
    
    std::ofstream outFile(newFilename);
    outFile << pythonCode;
    outFile.close();

    std::cout << "Translated to Python. New file: " << newFilename << std::endl;
    std::cout << "To run the Python version, use: python " << newFilename << std::endl;

    if (std::remove(filename.c_str()) != 0) {
        std::cout << "Error deleting the C++ file." << std::endl;
    }

    return 0;
}
'''
    return cpp_code

def main():
    print("Fibonacci sequence up to 10th number:")
    for i in range(10):
        print(fibonacci(i), end=" ")
    print()

    filename = __file__
    if is_python_file(filename):
        cpp_code = translate_to_cpp()
        new_filename = os.path.splitext(filename)[0] + ".cpp"
        bot_tools.rewrite(new_filename, cpp_code)
        print(f"Translated to C++. New file: {new_filename}")
        print(f"To compile and run the C++ version, use:")
        print(f"g++ {new_filename} -o fibonacci_translator")
        print(f"./fibonacci_translator")
        os.remove(filename)
    else:
        print("Error: This file is already a C++ file.")

if __name__ == "__main__":
    main()
)";
}

int main() {
    std::cout << "Fibonacci sequence up to 10th number:" << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << fibonacci(i) << " ";
    }
    std::cout << std::endl;

    std::string filename = __FILE__;
    if (isPythonFile(filename)) {
        std::cout << "Error: This file is already a Python file." << std::endl;
        return 1;
    }

    std::string pythonCode = translateToPython();
    std::string newFilename = filename.substr(0, filename.find_last_of(".")) + ".py";
    
    std::ofstream outFile(newFilename);
    outFile << pythonCode;
    outFile.close();

    std::cout << "Translated to Python. New file: " << newFilename << std::endl;
    std::cout << "To run the Python version, use: python " << newFilename << std::endl;

    if (std::remove(filename.c_str()) != 0) {
        std::cout << "Error deleting the C++ file." << std::endl;
    }

    return 0;
}
"""
    return cpp_code

def main():
    print("Fibonacci sequence up to 10th number:")
    for i in range(10):
        print(fibonacci(i), end=" ")
    print()

    filename = __file__
    if is_python_file(filename):
        cpp_code = translate_to_cpp()
        new_filename = os.path.splitext(filename)[0] + ".cpp"
        bot_tools.rewrite(new_filename, cpp_code)
        print(f"Translated to C++. New file: {new_filename}")
        print(f"To compile and run the C++ version, use:")
        print(f"g++ {new_filename} -o fibonacci_translator")
        print(f"./fibonacci_translator")
        os.remove(filename)
    else:
        print("Error: This file is already a C++ file.")

if __name__ == "__main__":
    main()