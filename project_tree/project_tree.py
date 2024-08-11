import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ast
import logging
from typing import Any, List, Optional
from collections import deque
from abc import ABC, abstractmethod
from pathlib import Path
import json
import src.anthropic_bots as bots
import src.base
from difflib import get_close_matches
import importlib
from typing import Dict, List, Tuple
import traceback
import unittest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to create or load a project, print its structure, and handle errors."""

    project_name, project_requirements, project_goals = PromptLib.test_project_prompt()

    root_dir = Path(r'C:\Users\Ben Rinauto\Documents\Code\llm-utilities-git\llm-utilities\.experiments')
    project_structure_file = root_dir / project_name / 'project_structure.json'

    if project_structure_file.exists():
        logger.info(f"Loading existing project: {project_name}")
        root = ProjectRoot(name=project_name, requirements=project_requirements, goals=project_goals, root_directory=root_dir)
    else:
        logger.info(f"Creating new project: {project_name}")
        root = ProjectRoot(name=project_name, requirements=project_requirements, goals=project_goals, root_directory=root_dir)

    project_tree = LazyMTree(root)
    print_visitor = TreePrintVisitor()
    logger.info("Initial Project Structure:")
    print_visitor.visit(project_tree)
    """
    import_graph = ImportDependencyGraph(root)
    dependency_visitor = DependencyUpdateVisitor(import_graph)
    dependency_visitor.visit()
    logger.info("Import dependencies resolved.")
    """
    test_visitor = TestVisitor(root)
    test_visitor.visit()

    # TODO - project evaluator / reliability 

# Utility Functions
def write_file(file_path: Path, content: str):
    """Write content to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as error:
        logger.error(f"Error writing to file {file_path}: {str(error)}", exc_info=True)
        raise error

def read_file(file_path: Path) -> str:
    """Read content from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def initialize_bot(bot_file_path: Path, max_tokens: int = 1024, tool_file: Path = None):
    """Initialize or load a bot."""
    try:
        if bot_file_path.exists() and bot_file_path.stat().st_size > 0:
            bot = src.base.load(bot_file_path)
        else:
            bot = bots.AnthropicBot(max_tokens=max_tokens)
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in bot file: {bot_file_path}. Creating a new bot.")
        bot = bots.AnthropicBot(max_tokens=max_tokens)
    if tool_file: bot.add_tools(tool_file)
    return bot

def get_investigation_order(func_graph: 'FunctionDependencyGraph', error_traceback: str):
    # Parse the traceback to get the call stack
    tb_lines = error_traceback.split('\n')
    call_stack = []
    for line in tb_lines:
        if "File " in line:
            parts = line.split(', ')
            file_name = parts[0].split('"')[1]
            func_name = parts[1].split(' ')[1]
            call_stack.append((Path(file_name).stem, func_name))
    
    # Reverse the call stack to start from the original caller
    call_stack = list(reversed(call_stack))
    
    # BFS to get nodes in order of distance from the original caller
    to_investigate = []
    visited = set()
    queue = deque([(node, 0) for node in call_stack])
    
    while queue:
        (file_name, func_name), distance = queue.popleft()
        if (file_name, func_name) not in visited:
            visited.add((file_name, func_name))
            to_investigate.append((file_name, func_name, distance))
            
            # Add called functions to the queue
            called_funcs = func_graph.get_function_calls(file_name, func_name)
            for called_file, called_func in called_funcs:
                if (called_file, called_func) not in visited:
                    queue.append(((called_file, called_func), distance + 1))
    
    # Sort by distance (which is already mostly done due to BFS)
    # and then alphabetically by file name and function name for consistency
    to_investigate.sort(key=lambda x: (x[2], x[0], x[1]))
    
    return to_investigate
class LazyMTreeNode(ABC):
    def __init__(self, value: Any, parent: Optional['LazyMTreeNode']=None, children: Optional[List['LazyMTreeNode']]=None):
        self.value = value
        self.parent = parent
        self._children = children or []
        self._expanded = children is not None

    @property
    def children(self) -> List['LazyMTreeNode']:
        if not self._expanded:
            self._children = self._expand()
            self._expanded = True
        return self._children

    @abstractmethod
    def _expand(self) -> List['LazyMTreeNode']:
        pass
    
class LazyMTree:
    """Lazy M-ary tree implementation."""

    def __init__(self, root: LazyMTreeNode):
        self.root = root

    def breadth_first_traverse(self):
        """Perform a breadth-first traversal of the tree."""
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node.value
            queue.extend(node.children)

    def depth_first_traverse(self):
        """Perform a depth-first traversal of the tree."""
        stack = [self.root]
        while stack:
            node = stack.pop()
            yield node.value
            stack.extend(reversed(node.children))

class ProjectNode(LazyMTreeNode):
    """Base class for project-related nodes."""

    def __init__(self, name: str, requirements: str, goals: str, parent = None, children=None):
        super().__init__(value=name, parent=parent, children=children)
        self.name = name
        self.requirements = requirements
        self.goals = goals
        self.file_path = None

    def get_project_root(self):
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def _gather_context(self) -> str:
        context = f'File: {self.file_path}\n'
        context += f"Local requirements: {self.requirements}\n"
        context += f"Local goals: {self.goals}\n"
        if isinstance(self, PythonFileNode):
            context += f"Interface:\n{self.interface}\n"
        context += "\n"
        
        # Add all interfaces from the registry
        project_root = self.get_project_root()
        all_interfaces = project_root.interface_registry.get_all()
        context += "Project Interfaces:\n"
        for file_path, interface in all_interfaces.items():
            if file_path != str(self.file_path):  # Don't include self
                context += f"{file_path} Interface:\n{interface}\n\n"
        
        # Traverse up the tree (keeping this for hierarchical context)
        parent = self.parent
        while parent:
            if isinstance(parent, ProjectNode):
                context += f'Parent: {parent.name}\n'
                context += f'Parent Requirements: {parent.requirements}\n'
                context += f"Parent Goals: {parent.goals}\n\n"
            parent = parent.parent
        return context

    @abstractmethod
    def get_type(self) -> str:
        """Get the type of the node."""
        pass

    @abstractmethod
    def to_string(self) -> str:
        """Convert the node to a string representation."""
        pass

    def extract_requirements_and_goals(self, response: str) -> tuple:
        """Extract requirements and goals from a response."""
        code_blocks, labels = src.base.remove_code_blocks(response)
        requirements = ''
        goals = ''
        for code, label in zip(code_blocks, labels):
            if label.strip().lower() == 'requirements':
                requirements = code
            elif label.strip().lower() == 'goals':
                goals = code
        if not requirements:
            raise ValueError(f"Requirements block not found in: {response}")
        if not goals:
            raise ValueError(f"Goals block not found in: {response}")
        return requirements, goals

    def to_dict(self) -> dict:
        """Convert the node to a dictionary for serialization."""
        return {
            'type': self.get_type(),
            'name': self.name,
            'requirements': self.requirements,
            'goals': self.goals,
            'file_path': str(self.file_path) if self.file_path else None,
            'file_type': getattr(self, 'file_type', None)
        }

    @classmethod
    def from_dict(cls, data: dict, parent: 'ProjectNode' = None):
        node_type = data['type']
        children = [ProjectNode.from_dict(child, parent) for child in data.get('children', [])]
        
        if node_type == 'Directory':
            node = DirectoryNode(name=data['name'], file_path=Path(data['file_path']), requirements=data['requirements'], goals=data['goals'], parent=parent, children=children)
        elif node_type == 'ProjectRoot':
            node = ProjectRoot(name=data['name'], requirements=data['requirements'], goals=data['goals'], root_directory=data['file_path'], children=children)
        elif node_type == 'PythonFileNode':
            node = PythonFileNode(name=data['name'], file_path=Path(data['file_path']), requirements=data['requirements'], goals=data['goals'], parent=parent, interface=data.get('interface', ''))
        elif node_type == 'TextFileNode':
            node = TextFileNode(name=data['name'], file_path=Path(data['file_path']), requirements=data['requirements'], goals=data['goals'], parent=parent)
        elif node_type == 'OtherFileNode':
            node = OtherFileNode(name=data['name'], file_path=Path(data['file_path']), requirements=data['requirements'], goals=data['goals'], parent=parent)
        else:
            node = cls(name=data['name'], requirements=data['requirements'], goals=data['goals'], parent=parent, children=children)
        
        node.file_path = Path(data['file_path']) if data['file_path'] else None
        node._expanded = True
        return node

class InterfaceRegistry:
    def __init__(self):
        self.interfaces = {}

    def register(self, file_path: str, interface: str):
        self.interfaces[file_path] = interface

    def get(self, file_path: str) -> str:
        return self.interfaces.get(file_path, "")

    def get_all(self) -> dict:
        return self.interfaces

class ProjectRoot(ProjectNode):
    def __init__(self, name: str, requirements: str, goals: str, root_directory: str, children=None):
        super().__init__(name=name, requirements=requirements, goals=goals, children=children)
        self.file_path = Path(root_directory) / name
        self.bot_file = f'{name}_root.bot'
        self.bot_file_path = self.file_path / self.bot_file
        self.bot = initialize_bot(self.bot_file_path)
        self.info_file_path = self.file_path / 'project_info.txt'
        self.structure_file_path = self.file_path / 'project_structure.json'
        self.interface_registry = InterfaceRegistry()
        
        if not self.structure_file_path.exists():
            os.makedirs(self.file_path, exist_ok=True)
            self._create_project_files()
        else:
            self._load_project_structure()

    def _create_project_files(self):
        """Create initial project files."""
        write_file(self.info_file_path, 
            f'Project Name: {self.name}\n'
            f'Requirements:\n{self.requirements}\n'
            f'Goals:\n{self.goals}\n')
        
        self._expand()
        self._save_project_structure()

    def _load_project_structure(self):
        with open(self.structure_file_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        self._load_structure(structure)

    def _load_structure(self, structure: dict):
        self._children = [ProjectNode.from_dict(child, self) for child in structure.get('children', [])]
        self._expanded = True
        
        for file_path, interface in structure.get('interfaces', {}).items():
            self.interface_registry.register(file_path, interface)
        
        # Load interfaces
        for file_path, interface in structure.get('interfaces', {}).items():
            self.interface_registry.register(file_path, interface)

    def _save_project_structure(self):
        """Save project structure to a JSON file."""
        structure = self.to_dict()
        with open(self.structure_file_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2)

    def _expand(self):
        """Expand the root node to generate its children."""
        prompt = PromptLib.root_prompt(self.name, self._gather_context())
        response = self.bot.respond(prompt)
        directory_list = self.get_directories(response)
        nodes = []
        for directory in directory_list:
            directory_full = self.file_path / directory
            next_prompt = PromptLib.dir_goals_prompt(directory_full, self.name)
            response = self.bot.respond(next_prompt)
            requirements, goals = self.extract_requirements_and_goals(response)
            self.bot.save(self.bot_file_path)
            try:    
                nodes.append(DirectoryNode(directory, directory_full, requirements, goals, self))
            except Exception as error:
                logger.error(f"Error creating DirectoryNode: {error}", exc_info=True)
                nodes.append(ErrorNode(name='Error', text=str(error)))
        return nodes
    
    def get_type(self):
        return 'ProjectRoot'
    
    def to_string(self) -> str:
        return f'Project Root: {self.name}'
    
    def get_directories(self, response):
        directories = []
        lines = response.split('\n')
        for line in lines:
            cleaned_line = line.strip()
            if cleaned_line.startswith('-'):
                item = cleaned_line[1:].strip()
                directories.append(item)
        return directories

    def to_dict(self) -> dict:
        """Convert the project structure to a dictionary for serialization."""
        data = super().to_dict()
        data['children'] = [child.to_dict() for child in self.children]
        data['interfaces'] = self.interface_registry.get_all()
        return data

class DirectoryNode(ProjectNode):
    """Represents a directory in the project structure."""

    def __init__(self, name: str, file_path: Path, requirements: str, goals: str, parent: ProjectNode, children=None):
        super().__init__(name, requirements, goals, parent, children)
        self.file_path = file_path
        os.makedirs(self.file_path, exist_ok=True)
        self.bot_file = 'dir.bot'
        self.bot_file_path = self.file_path / self.bot_file
        self.bot = initialize_bot(self.bot_file_path)
        self.info_file_path = self.file_path / 'dir_info.txt'
        write_file(self.info_file_path, 
                   f'Directory Name: {file_path}\n\n'
                   f'Requirements:\n{requirements}\n\n'
                   f'Goals:\n{goals}\n\n')
        self.interfaces = {}

    def _expand(self):
        """Expand the directory node to generate its children."""
        prompt = f"""
        Based on the following context for the directory '{self.file_path}',
        generate a list of files that should be created in this directory.
        Respond with only the file names, one per line, prefixed with a hyphen.
        
        Here is the context:
        {self._gather_context()}
        """
        response = self.bot.respond(prompt)
        file_list = self.get_files(response)
        nodes = []
        for file_name in file_list:
            file_type = self.get_file_type(file_name)
            next_prompt = PromptLib.file_def_prompt(file_name, self.file_path)
            response = self.bot.respond(next_prompt)
            requirements, goals = self.extract_requirements_and_goals(response)
            try:
                if file_type == 'python':
                    interface = self._generate_interface(file_name, requirements, goals)
                    self.interfaces[file_name] = interface
                    nodes.append(PythonFileNode(file_name, self.file_path / file_name, requirements, goals, self, interface))
                elif file_type in ['markdown', 'gitignore']:
                    nodes.append(TextFileNode(file_name, self.file_path / file_name, requirements, goals, self))
                else:
                    nodes.append(OtherFileNode(file_name, self.file_path / file_name, requirements, goals, self))
            except Exception as error:
                logger.error(f"Error creating file node: {error}", exc_info=True)
                nodes.append(ErrorNode(name='Error', text=str(error)))
        
        self.bot.save(self.bot_file_path)
        return nodes
    
    def _generate_interface(self, file_name, requirements, goals):
        prompt = PromptLib.interface_prompt(file_name, self.file_path, goals, requirements)
        response = self.bot.respond(prompt)
        # Extract the code block from the response
        code_blocks, _ = src.base.remove_code_blocks(response)
        return code_blocks[0] if code_blocks else ""

    def get_type(self):
        return 'Directory'

    def to_string(self) -> str:
        return f'Directory: {self.name} ({self.file_path})'

    def get_files(self, response):
            files = []
            lines = response.split('\n')
            for line in lines:
                if line.strip().startswith('-'):
                    item = line.strip()[1:].strip()
                    files.append(item)
            return files

    def get_file_type(self, file_name):
        if file_name.endswith('.py'):
            return 'python'
        elif file_name.endswith('.md'):
            return 'markdown'
        elif file_name == '.gitignore':
            return 'gitignore'
        else:
            return 'other'

    def to_dict(self) -> dict:
        """Convert the directory structure to a dictionary for serialization."""
        data = super().to_dict()
        data['children'] = [child.to_dict() for child in self.children]
        data['interfaces'] = self.interfaces
        return data

class PythonFileNode(ProjectNode):
    """Represents a Python file in the project structure."""

    def __init__(self, name: str, file_path: Path, requirements: str, goals: str, parent: ProjectNode, interface: str):
        super().__init__(name, requirements, goals, parent)
        self.file_path = file_path
        self.file_type = 'python'
        self.bot_path = self.file_path.with_suffix('.bot')
        self._ast = None
        self.interface = interface
        
        self.bot = initialize_bot(self.bot_path, 4096, Path(r"project_tree\py_bot_tools.py"))

        self.info_file_path = self.file_path.with_suffix('.txt')
        write_file(self.info_file_path, 
                   f'File Name: {self.file_path}\n\n'
                   f'Requirements:\n{self.requirements}\n\n'
                   f'Goals:\n{self.goals}\n\n'
                   f'Interface:\n{self.interface}\n\n')
        
        # Register the interface
        self.get_project_root().interface_registry.register(str(self.file_path), self.interface)

    def _expand(self):
        """Expand the Python file node (generate file content if it doesn't exist)."""
        if not self.file_path.exists():
            self._generate_file_content()
        if self._ast is None:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    tree = ast.parse(file.read())
                    self._ast = tree
            except Exception as error:
                logger.error(f"Error parsing Python file: {error}", exc_info=True)
                return [ErrorNode(name='Error', text=str(error))]
        return []

    def _generate_file_content(self):
        """Generate content for the Python file."""
        context = self._gather_context()
        prompt = PromptLib.file_gen_prompt(self.file_path, context, self.interface)
        response = self.bot.respond(prompt,tool_auto=True)
        result = self.write_code(response)
        counter = 0
        retry_limit = 3
        while result != 'success' and counter < retry_limit:
            counter += 1
            response = self.bot.respond(f'Please try again, there were issues with your syntax\n\n{result}')
            result = self.write_code(response)
        if result != 'success':
            self.write_code(f'"""\n\nCode writing failed\n\n{self.bot.conversation.build_messages()}\n\n"""')

    def write_code(self, response):
        self.bot.save(self.bot_path)
        code_blocks, _ = src.base.remove_code_blocks(response)
        if code_blocks:
            code = code_blocks[0]
            try:
                ast.parse(code)  # Validate the generated code
                write_file(self.file_path, code)
                result = 'success'
            except SyntaxError as error:
                result = f"Generated invalid Python code for {self.file_path}\n\n{error}"
                logger.error(f"Generated invalid Python code for {self.file_path}")
        else:
            result = "No code blocks found" 
        return result        

    def to_string(self) -> str:
        return f'Python File: ({self.file_path})'
    
    def get_type(self) -> str:
        return 'PythonFileNode'

    def to_dict(self) -> dict:
        """Convert the Python file node to a dictionary for serialization."""
        data = super().to_dict()
        data['interface'] = self.interface
        return data

class TextFileNode(ProjectNode):
    """Represents a text file (like Markdown or .gitignore) in the project structure."""

    def __init__(self, name: str, file_path: Path, requirements: str, goals: str, parent: ProjectNode):
        super().__init__(name, requirements, goals, parent)
        self.file_type = 'text'
        self.file_path = file_path
        self.bot = initialize_bot(self.file_path, 4096)

    def _expand(self):
        if not self.file_path.exists():
            self._generate_file_content()
        return []

    def _generate_file_content(self):
        context = self._gather_context()
        prompt = f"Generate content for {self.name} file {self.file_path} based on: {context}"
        response = self.bot.respond(prompt)
        write_file(self.file_path, response)

    def to_string(self) -> str:
        return f'{self.name.capitalize()} File: ({self.file_path})'
    
    def get_type(self) -> str:
        return 'TextFileNode'

class OtherFileNode(ProjectNode):
    """Represents another file type in the project structure."""

    def __init__(self, name: str, file_path: Path, requirements: str, goals: str, parent: ProjectNode):
        super().__init__(name, requirements, goals, parent)  # Remove 'other' from here
        self.file_type = 'other'  # Set file_type as a separate attribute
        self.file_path = file_path

    def _expand(self):
        return []  # Other file types don't have children

    def to_string(self) -> str:
        return f'Other File: ({self.file_path})'
    
    def get_type(self) -> str:
        return 'OtherFileNode'

class ErrorNode(ProjectNode):
    """Represents an error in the project structure."""

    def __init__(self, name: str, text: str):
        super().__init__(name, None, None, None)
        self.text = text

    def get_type(self) -> str:
        return 'Error'

    def to_string(self) -> str:
        return f'Error:{self.name}\n\n{self.text}'
    
    def _expand(self) -> List['LazyMTreeNode']:
        return []

class TreePrintVisitor:
    """Visitor class to print the tree structure."""

    def visit(self, tree: LazyMTree):
        """
        Visit and print the tree structure.

        Args:
            tree: The LazyMTree to visit and print.
        """
        def print_node(node: LazyMTreeNode, depth: int = 0):
            if isinstance(node, ProjectNode):
                print('  ' * depth + node.to_string())
            if isinstance(node, LazyMTreeNode):
                for child in node.children:
                    if child:
                        print_node(child, depth + 1)
            if isinstance(node, str):
                print('  ' * depth + node)
                Warning(f"String node found:\n\n{node}")
        print_node(tree.root)

class ImportSuggester:

    def __init__(self, root: ProjectRoot):
        self.root = root
        self.bot = bots.AnthropicBot()
        self.all_modules = self._get_all_modules()

    def _get_all_modules(self):
        modules = []
        for root, dirs, files in os.walk(self.root.file_path):
            for file in files:
                if file.endswith('.py'):
                    module_path = os.path.relpath(os.path.join(root, file), self.root.file_path)
                    module_name = os.path.splitext(module_path.replace(os.path.sep, '.'))[0]
                    modules.append(module_name)
        return modules

    def fuzzy_match(self, import_name):
        matches = get_close_matches(import_name, self.all_modules, n=3, cutoff=0.6)
        return matches

    def llm_match(self, import_name, file_context):
        prompt = PromptLib.import_suggestion_prompt(import_name, file_context, self.all_modules)
        response = self.bot.respond(prompt)
        return response.strip()

class ImportDependencyGraph:
    def __init__(self, root: ProjectRoot):
        self.root = root
        self.graph = {}
        self._build_graph()

    def _build_graph(self):
        for node in self._traverse_tree(self.root):
            if isinstance(node, PythonFileNode):
                self.graph[node] = self._get_dependencies(node)

    def _traverse_tree(self, node):
        if isinstance(node, ProjectNode):
            yield node
            for child in node.children:
                yield from self._traverse_tree(child)
        else:
            print(f"Warning: Import Visitor encountered non-ProjectNode object during traversal: {node}")


    def _get_dependencies(self, node: PythonFileNode):
        dependencies = []
        try:
            with open(node.file_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                for stmt in ast.walk(tree):
                    if isinstance(stmt, ast.Import):
                        for alias in stmt.names:
                            dependencies.append(alias.name)
                    elif isinstance(stmt, ast.ImportFrom):
                        dependencies.append(stmt.module)
            return dependencies
        except FileNotFoundError as error:
            return [f'File{node.file_path} does not exist']
        
    def get_dependents(self, node: PythonFileNode):
        return [n for n, deps in self.graph.items() if node.name in deps]

class FunctionDependencyGraph:
    def __init__(self, root: ProjectRoot):
        self.root = root
        self.graph: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        self._build_graph()

    def _build_graph(self):
        for node in self._traverse_tree(self.root):
            if isinstance(node, PythonFileNode):
                self._add_function_calls(node)

    def _traverse_tree(self, node):
        yield node
        for child in node.children:
            yield from self._traverse_tree(child)

    def _add_function_calls(self, node: PythonFileNode):
        with open(node.file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read())
            for func_def in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
                func_key = (node.file_path.stem, func_def.name)
                self.graph[func_key] = []
                for call in [n for n in ast.walk(func_def) if isinstance(n, ast.Call)]:
                    if isinstance(call.func, ast.Name):
                        called_func = call.func.id
                        self.graph[func_key].append((node.file_path.stem, called_func))
                    elif isinstance(call.func, ast.Attribute):
                        module = call.func.value.id if isinstance(call.func.value, ast.Name) else None
                        self.graph[func_key].append((module, call.func.attr))

    def get_function_calls(self, file_name: str, function_name: str) -> List[Tuple[str, str]]:
        return self.graph.get((file_name, function_name), [])

    def get_function_callers(self, file_name: str, function_name: str) -> List[Tuple[str, str]]:
        return [(caller, func) for (caller, func), called in self.graph.items() 
                if (file_name, function_name) in called]

    def get_all_functions(self) -> List[Tuple[str, str]]:
        return list(self.graph.keys())

    def get_orphan_functions(self) -> List[Tuple[str, str]]:
        all_functions = set(self.graph.keys())
        called_functions = set()
        for calls in self.graph.values():
            called_functions.update(calls)
        return list(all_functions - called_functions)

    def get_function_call_chain(self, file_name: str, function_name: str, max_depth: int = 5) -> List[List[Tuple[str, str]]]:
        def dfs(current, depth, chain):
            if depth > max_depth:
                return
            chain.append(current)
            if tuple(current) in self.graph:
                for call in self.graph[tuple(current)]:
                    dfs(call, depth + 1, chain.copy())
            else:
                chains.append(chain)

        chains = []
        dfs((file_name, function_name), 0, [])
        return chains

class DependencyUpdateVisitor:
    """Visitor class to correct import statements"""
    
    def __init__(self, dependency_graph: ImportDependencyGraph):
        self.dependency_graph = dependency_graph
        self.visited = set()

    def visit(self):
        for node in self.dependency_graph.graph:
            if node not in self.visited:
                self._visit_node(node)

    def _visit_node(self, node: PythonFileNode):
        self.visited.add(node)
        
        # Visit dependencies first
        for dep_name in self.dependency_graph.graph[node]:
            dep_node = self._find_node(dep_name)
            if dep_node and dep_node not in self.visited:
                self._visit_node(dep_node)

        # Update the current node
        self._update_node(node)

    def _find_node(self, name):
        for node in self.dependency_graph.graph:
            if node.name == name or node.file_path.stem == name:
                return node
        return None

    def _get_file_content(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _update_node(self, node: PythonFileNode):
        import_outlines = self._get_import_outlines(node)
        missing_imports = self._get_missing_imports(node)
        prompt = PromptLib.update_node_prompt(node.file_path, import_outlines, missing_imports, node.interface)
        response = node.bot.respond(prompt)
        node.write_code(response)

    def _get_missing_imports(self, node):
        missing = []
        for dep_name in self.dependency_graph.graph[node]:
            if not self._find_node(dep_name):
                # Check if the import is an external package
                if self._is_external_package(dep_name):
                    continue  # Skip external packages
                
                import_suggester = ImportSuggester(self.dependency_graph.root)
                fuzzy_matches = import_suggester.fuzzy_match(dep_name)
                llm_suggestion = import_suggester.llm_match(dep_name, self._get_file_content(node.file_path))
                missing.append(f"Missing import: {dep_name}\n"
                               f"Fuzzy matches: {', '.join(fuzzy_matches)}\n"
                               f"LLM suggestion:\n{llm_suggestion}\n")
        return "\n".join(missing) if missing else "None"

    def _is_external_package(self, package_name):
        # Check if the package can be imported
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except ImportError:
            return False

    def _get_import_outlines(self, node):
        outlines = ""
        for dep_name in self.dependency_graph.graph[node]:
            dep_node = self._find_node(dep_name)
            if dep_node:
                outlines += f"File: {dep_node.file_path}\n"
                outlines += self._get_file_outline(dep_node.file_path) + "\n\n"
            else:
                outlines += f"File: {dep_name} (Not found)\n"
                outlines += "This module is imported but not found in the project structure.\n\n"
        return outlines

    def _get_file_outline(self, file_path):
        try:
            with open(file_path, 'r') as file:
                tree = ast.parse(file.read())
            outline = ""
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    outline += f"{node.__class__.__name__}: {node.name}\n"
            return outline
        except FileNotFoundError:
            return "File not found"
        except SyntaxError:
            return "Unable to parse file (syntax error)"
        except Exception as e:
            return f"Error reading file: {str(e)}"

class TestVisitor:
    def __init__(self, root: ProjectRoot):
        self.root = root
        self.error_handler = ErrorHandler(root)
        self.error_queue = deque()
        self.unresolved_errors = []

    def visit(self):
        self.error_queue.clear()
        self.unresolved_errors.clear()
        for node in self._traverse_tree(self.root):
            if isinstance(node, PythonFileNode):
                self._run_tests(node)
            elif not isinstance(node, ProjectNode):
                raise ValueError(f"Encountered unexpected node type during visitation: {type(node)}\n\n{node}")
        
        while self.error_queue:
            node, error_info = self.error_queue.popleft()
            resolution = self.error_handler.handle_error(error_info, node)
            if resolution == 'corrected':
                # If a correction was made, rerun tests for this node and all its dependencies
                self._rerun_tests(node)
            elif resolution == 'unresolved':
                # If no bot took responsibility, add to unresolved errors
                self.unresolved_errors.append((node, error_info))
        
        if self.unresolved_errors:
            self._handle_unresolved_errors()

    def _traverse_tree(self, node):
        if isinstance(node, ProjectNode):
            yield node
            for child in node.children:
                yield from self._traverse_tree(child)
        else:
            print(f"Warning: Test Visitor encountered non-ProjectNode object during traversal: {node}")

    def _run_tests(self, node: PythonFileNode):
        file_path = node.file_path
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        
        sys.path.insert(0, str(file_path.parent))
        try:
            spec.loader.exec_module(module)
            suite = unittest.TestLoader().loadTestsFromModule(module)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            
            if not result.wasSuccessful():
                error_info = self._get_error_info(result)
                self.error_queue.append((node, error_info))
        except Exception as e:
            error_info = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }
            self.error_queue.append((node, error_info))
        finally:
            sys.path.pop(0)

    def _get_error_info(self, result):
        error_info = {}
        for test, error in result.errors + result.failures:
            error_info[test.id()] = {
                'type': 'Error' if test in result.errors else 'Failure',
                'message': error,
                'traceback': error
            }
        return error_info

    def _rerun_tests(self, node: PythonFileNode):
        # Rerun tests for this node and all its dependencies
        dependency_graph = ImportDependencyGraph(self.root)
        nodes_to_test = [node] + dependency_graph.get_dependents(node)
        for dependent_node in nodes_to_test:
            self._run_tests(dependent_node)

    def _handle_unresolved_errors(self):
        print("The following errors could not be resolved by individual file bots:")
        for node, error_info in self.unresolved_errors:
            print(f"File: {node.file_path}")
            print(self.error_handler._format_error_info(error_info))
        
        # Escalate to a higher-level problem solver
        self._escalate_to_project_bot()

    def _escalate_to_project_bot(self):
        project_bot = self.root.bot  # Assuming the project root has a bot
        
        prompt = f"""
        The following errors in the project could not be resolved by individual file bots:

        {self._format_unresolved_errors()}

        Please analyze these errors and suggest a high-level solution. 
        This may involve changes to multiple files or the project structure.
        If you suggest changes, please provide the full updated content for each file you modify.
        """

        response = project_bot.respond(prompt)
        self._apply_project_wide_changes(response)

    def _format_unresolved_errors(self):
        formatted = ""
        for node, error_info in self.unresolved_errors:
            formatted += f"File: {node.file_path}\n"
            formatted += self.error_handler._format_error_info(error_info)
            formatted += "\n"
        return formatted

    def _apply_project_wide_changes(self, response):
        # Extract file changes from the response
        file_changes = self._parse_file_changes(response)
        
        for file_path, new_content in file_changes.items():
            node = self._find_node(file_path)
            if node and isinstance(node, PythonFileNode):
                node.write_code(new_content)
                print(f"Updated file: {file_path}")
        
        # After applying changes, rerun all tests
        self.visit()

    def _parse_file_changes(self, response):
        changes = {}
        parts = response.split("```python")
        for i in range(1, len(parts), 2):
            file_content = parts[i].split("```")[0]
            file_path = parts[i-1].split("File: ")[-1].strip()
            changes[file_path] = file_content
        return changes

    def _find_node(self, file_path: str):
        for node in self._traverse_tree(self.root):
            if isinstance(node, PythonFileNode) and str(node.file_path) == file_path:
                return node
        return None

class ErrorHandler:
    def __init__(self, root: ProjectRoot):
        self.root = root

    def handle_error(self, error_info, node: PythonFileNode):
        involved_files = self._get_involved_files(error_info)
        for file_path in involved_files:
            file_node = self._find_node(file_path)
            if file_node:
                if self._consult_file_bot(file_node, error_info):
                    return 'corrected'
        return 'unresolved'

    def _get_involved_files(self, error_info):
        involved_files = set()
        if isinstance(error_info, dict):
            # If error_info is a dictionary of errors
            for error in error_info.values():
                if isinstance(error, dict) and 'traceback' in error:
                    for line in error['traceback'].split('\n'):
                        if 'File "' in line:
                            file_path = line.split('File "')[1].split('"')[0]
                            involved_files.add(Path(file_path))
        else:
            # If error_info is a single error
            if isinstance(error_info, dict) and 'traceback' in error_info:
                for line in error_info['traceback'].split('\n'):
                    if 'File "' in line:
                        file_path = line.split('File "')[1].split('"')[0]
                        involved_files.add(Path(file_path))
        return involved_files

    def _find_node(self, file_path: Path):
        for node in self._traverse_tree(self.root):
            if isinstance(node, PythonFileNode) and node.file_path == file_path:
                return node
        return None

    def _traverse_tree(self, node):
        yield node
        for child in node.children:
            yield from self._traverse_tree(child)

    def _consult_file_bot(self, node: PythonFileNode, error_info):
        prompt = self._generate_error_prompt(node, error_info)
        response = node.bot.respond(prompt)
        if self._is_responsible(response):
            return self._correct_file(node, response)
        return False

    def _generate_error_prompt(self, node: PythonFileNode, error_info):
        return f"""
        An error occurred during testing that involves the file {node.file_path}.
        Here's the error information:

        {self._format_error_info(error_info)}

        Based on this information:
        1. Is this file responsible for the error?
        2. If yes, how would you correct it?

        Please provide your analysis and, if applicable, the corrected code for the entire file.
        """

    def _format_error_info(self, error_info):
        formatted = ""
        if not isinstance(error_info, dict):
            raise SyntaxError(f"error_info was a not a dict, but dict was expected. error_info:{error_info}")
        else:
            try:
                for test, info in error_info.items():
                    formatted += f"Test: {test}\n"
                    formatted += f"Type: {info['type']}\n"
                    formatted += f"Message: {info['message']}\n"
                    formatted += f"Traceback:\n{info['traceback']}\n\n"
                return formatted
            except TypeError as error:
                print("\n\n"+error_info+"\n\n")

    def _is_responsible(self, response):
        return "yes" in response.lower()

    def _correct_file(self, node: PythonFileNode, response):
        if "```python" in response:
            node.write_code(response)
            print(f"File {node.file_path} has been corrected.")
            return True
        else:
            print(f"No corrected code found in the response for {node.file_path}.")
            return False

class PromptLib:
    def __init__(self):
        pass

    @staticmethod
    def feapy_prompt():
        project_name = "feapy"
        project_goals = "Develop a Python-based Finite Element Analysis tool for structural engineering calculations"
        project_requirements = """
        1. Implement 2D and 3D element types (e.g., truss, beam, plate)
        2. Support linear static analysis
        3. Include material library with common engineering materials
        4. Provide graphical output of results (deformation, stress, strain)
        5. Include documentation and example problems
        6. Keep the project SMALL. Proof-of-concept level. Ensure all modules have this requirement.
        7. No more than 7 requirements can be placed on any directory.
        8. No more than 4 top level directories.
        9. Name the src folder "feapy" instead
        10. Create a setup file setup.py in the feapy folder (I'll move it later)
        11. Testing: All python files will contain their own unittests. The tests folder will contain only tests that combine the functionality of one or more files.
        12. Requirements vs. Goals: All requirements should be testable. Goals do not have to be testable, but should memorialize the purpose of the requirements.
        """
        return project_name, project_requirements, project_goals
    
    @staticmethod
    def test_project_prompt():
        project_name = f"test@{src.base.formatted_datetime()}"
        project_goals = "Create a small python project to demonstrate your capabilities"
        project_requirements = """
        1. Keep the project SMALL. Proof-of-concept level. Ensure all modules have this requirement.
        2. No more than 5 requirements can be placed on any directory.
        3. Exactly three top level directories.
        4. The subject of the test project - make a connect four game in python.
        5. Testing: All python files will contain their own unittests. There will be no /tests folder - rather, tests that rely on more than one module should be built into the directory where those modules are used in conjunction.
        6. The game should have a testable GUI. When testing the GUI, ensure that no user interaction is required. All GUI elements that require dismissal should have <1 second timeouts during testing, for instance, rather than requiring someone to click.
        7. No pop-ups.
        8. Requirements vs. Goals: All requirements should be testable. Goals do not have to be testable, but should memorialize the purpose of the requirements.
        """
        return project_name, project_requirements, project_goals
    
    @staticmethod
    def root_prompt(name, context):
        return f"""
        Based on the following context for the project '{name}',
        generate a list of top-level directories that should be created for this project.
        Consider common project structures and the specific goals and requirements of this project.
        Respond with only the subdirectories, one per line, prefixed with a hyphen.

        Here is the context:
        {context}
        """ 

    @staticmethod   
    def dir_goals_prompt(dir_path, proj_name):
        return f"""
        For the directory '{dir_path}' in the project '{proj_name}', provide:
        1. High level goals and purpose for the directory in a code block labeled 'goals'
        2. A preliminary set of requirements for the directory in a code block labeled 'requirements'
        Be specific and thorough with requirements, but also be very concise.
        You have approximately 300 words before you're cut off.
        Write your response as a set of code blocks labeled ```requirements and ```goals
        """

    @staticmethod
    def dir_file_names_prompt(directory_path, context):
        return f"""
        Based on the following context for the directory '{directory_path}',
        generate a list of files that should be created in this directory.
        Respond with only the file names, one per line, prefixed with a hyphen.
        
        Here is the context:
        {context}
        """
    
    @staticmethod
    def file_def_prompt(file_name, directory_path):
        return f"""
        For the file '{file_name}' in the directory '{directory_path}', provide:
        1. High level goals and purpose for the file in a code block labeled 'goals'
        2. A preliminary set of requirements for the file in a code block labeled 'requirements'
        Be specific, thorough, and brief. Don't write any code or pseudo-code.     
        You have approximately 300 words before you're cut off.
        Write your response as a set of code blocks labeled ```requirements and ```goals
        """

    @staticmethod
    def interface_prompt(file_name, directory_path, goals, requirements):
        return f"""
        For the Python file '{file_name}' in the directory '{directory_path}', create an interface specification.
        This interface should describe the intended way for the file to be accessed externally.
        Include only the classes and functions that should be accessible from outside the file.
        Provide function and class headers without their implementations.
        Base this interface on the file's goals and requirements:

        Goals: {goals}
        Requirements: {requirements}

        Respond with a code block containing only the interface specification.
        """

    @staticmethod
    def file_gen_prompt(file_path, context, interface):
        return f"""Based on the following context and interface, generate Python code for the file {file_path}:

        Context:
        {context}

        Global Interface Registry:
        {interface}

        Write concise, well-structured Python code that implements the interface and addresses the goals and requirements. 
        Ensure that all elements specified in your interface are included in your implementation. Do not use functions that do not appear in the global interface registry.
        Reply with a single python code block. Code will be extracted from that block.
        
        Include unittests for the interface functions and any other functions you've written. When run, the file should run the unittests.
        """

    @staticmethod
    def update_node_prompt(file_path, import_outlines, missing_imports, interface):
        return f"""
        You are updating the file {file_path}. Here are the outlines of the files it imports:

        {import_outlines}

        The following imports were not found in the project structure:
        {missing_imports}

        This file should implement the following interface:
        {interface}

        Based on this information, please rewrite the entire content of {file_path}.
        Ensure that:
        1. The file implements all elements specified in the interface.
        2. Existing imports and function calls are consistent with the interfaces provided.
        3. Missing imports are handled as previously instructed.

        Maintain the original functionality and purpose of the file while improving its integration with the imported modules and adhering to the specified interface.

        Respond with only the updated Python code for the file.
        """
    
    def import_suggestion_prompt(import_name, file_context, available_modules):
        return f"""
        In the context of the following Python file:

        {file_context}

        The import '{import_name}' is missing. Based on the file's context and the following list of available modules in the project, suggest the most likely correct import:

        Available modules:
        {', '.join(available_modules)}

        Provide your suggestion in the format:
        Suggested import: [your suggestion]
        Reason: [brief explanation]

        If none of the available modules seem appropriate, you may suggest creating a new module or using an external library.
        """

if __name__ == "__main__":
    main()