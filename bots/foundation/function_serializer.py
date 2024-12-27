import inspect
import types
import marshal
import pickle
import base64
import functools
import builtins
import weakref
import ast


class InheritanceError(Exception):
    """Custom error for inheritance-related issues."""
    pass


class EnhancedFunctionSerializer:
    """
    Enhanced serialization system for Python functions that handles:
    - Instance methods and class methods
    - Built-in function references
    - Lambda functions
    - Nested functions and closures

    Also detects and warns about inheritance-related issues.
    """
    SAFE_BUILTINS = {name: getattr(builtins, name) for name in dir(builtins
        ) if isinstance(getattr(builtins, name), types.BuiltinFunctionType)}


    class InheritanceChecker(ast.NodeVisitor):

        def __init__(self):
            super().__init__()
            self.has_super = False
            self.has_cls_construction = False
            self.has_parent_refs = False
            self.inside_class_method = False
            self.current_scope = []
            self.method_calls = set()
            self.in_method = False

        def visit_ClassDef(self, node):
            self.current_scope.append(('class', node.name))
            self.generic_visit(node)
            self.current_scope.pop()

        def visit_FunctionDef(self, node):
            self.current_scope.append(('function', node.name))
            self.in_method = True
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name
                    ) and decorator.id == 'classmethod':
                    self.inside_class_method = True
            self.generic_visit(node)
            self.in_method = False
            self.current_scope.pop()

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == 'super':
                self.has_super = True
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Call):
                    if isinstance(node.func.value.func, ast.Name
                        ) and node.func.value.func.id == 'super':
                        self.has_super = True
                elif isinstance(node.func.value, ast.Name
                    ) and node.func.value.id == 'super':
                    self.has_super = True
            if self.inside_class_method:
                if isinstance(node.func, ast.Name) and node.func.id == 'cls':
                    self.has_cls_construction = True
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name
                        ) and node.func.value.id == 'cls':
                        self.has_cls_construction = True
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name
                    ) and node.func.value.id in ('self', 'super'):
                    self.method_calls.add(node.func.attr)
            self.generic_visit(node)

        def visit_Attribute(self, node):
            if isinstance(node.value, ast.Name) and node.value.id in ('self',
                'super'):
                current_method = next((scope[1] for scope in reversed(self.
                    current_scope) if scope[0] == 'function'), None)
                if current_method and node.attr != current_method:
                    self.has_parent_refs = True
            self.generic_visit(node)

    @staticmethod
    def _get_function_type(func):
        """Determine the type of the function."""
        if isinstance(func, types.LambdaType):
            return 'lambda'
        elif isinstance(func, types.MethodType):
            return 'method'
        elif isinstance(func, (classmethod, staticmethod)):
            return 'descriptor'
        else:
            return 'function'

    @staticmethod
    def _serialize_class_method_descriptor(descriptor):
        """Serialize a class method or static method descriptor."""
        if isinstance(descriptor, classmethod):
            func = descriptor.__get__(None, object).__func__
        else:
            func = descriptor.__func__
        return {'type': 'classmethod' if isinstance(descriptor, classmethod
            ) else 'staticmethod', 'func': func}

    @staticmethod
    def _handle_builtin(obj):
        """Convert built-in functions to their name reference."""
        if isinstance(obj, types.BuiltinFunctionType):
            builtin_name = obj.__name__
            if builtin_name in dir(builtins):
                return f'__builtin__{builtin_name}'
        return obj

    @staticmethod
    def _restore_builtin(name):
        """Restore a built-in function from its name."""
        if isinstance(name, str) and name.startswith('__builtin__'):
            builtin_name = name[11:]
            return getattr(builtins, builtin_name)
        return name

    def _check_inheritance_safety(self, func):
        """
        Analyze function for inheritance-related risks.

        Checks for:
        1. super() calls
        2. References to parent class methods
        3. Class construction
        4. Method resolution order dependencies
        """
        original_func = func
        if isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        elif isinstance(func, types.MethodType):
            func = func.__func__
            
        try:
            if isinstance(original_func, types.MethodType):
                # For bound methods, try to get source from the class
                cls = original_func.__self__.__class__
                source = inspect.getsource(cls)
            elif isinstance(original_func, (classmethod, staticmethod)):
                source = inspect.getsource(original_func.__func__)
            else:
                source = inspect.getsource(func)

            source = inspect.cleandoc(source)
            tree = ast.parse(source)
            checker = self.InheritanceChecker()
            checker.visit(tree)
        except (OSError, TypeError, KeyError, AttributeError, SyntaxError, ValueError) as e:
            try:
                source = inspect.getsource(func)
                source = inspect.cleandoc(source)
                tree = ast.parse(source)
                checker = self.InheritanceChecker()
                checker.visit(tree)
            except (OSError, TypeError, SyntaxError, ValueError):
                return
        if checker.has_super:
            suggestion = """
To make this method serializable, avoid using super() and explicitly define the behavior:

Instead of:
    def method(self):
        return super().method()

Use:
    def method(self):
        # Explicitly implement the behavior
        return specific_implementation()
"""
            raise InheritanceError(
                f"Method contains super() calls which won't survive serialization.{suggestion}"
                )
        if checker.has_cls_construction:
            suggestion = """
To make this classmethod serializable, accept the instance as a parameter:

Instead of:
    @classmethod
    def create(cls, param):
        return cls(param)

Use:
    def create(param):
        # Return a dict of parameters instead
        return {'param': param}
"""
            raise InheritanceError(
                f'Method constructs class instances which may not exist after deserialization.{suggestion}'
                )
        if checker.has_parent_refs:
            suggestion = """
To make this method serializable, explicitly accept parent class dependencies:

Instead of:
    def method(self):
        return self.parent_method()

Use:
    def method(self, parent_method=None):
        return parent_method()
"""
            raise InheritanceError(
                f"Method may reference parent class methods which won't be available after deserialization.{suggestion}"
                )
    def serialize_function(self, func):
        """Serialize a function with enhanced handling for special cases."""
        self._check_inheritance_safety(func)
        func_type = self._get_function_type(func)
        if func_type == 'method':
            func = func.__func__
        elif func_type == 'descriptor':
            descriptor_data = self._serialize_class_method_descriptor(func)
            func = descriptor_data['func']
            func_type = descriptor_data['type']
        code = func.__code__
        func_name = (func.__name__ if func_type != 'lambda' else
            f'lambda_{hash(code.co_code)}')
        code_bytes = marshal.dumps(code)
        code_str = base64.b64encode(code_bytes).decode('utf-8')
        closure = func.__closure__
        closure_vars = []
        if closure:
            for cell in closure:
                cell_contents = cell.cell_contents
                if isinstance(cell_contents, (types.FunctionType, types.
                    MethodType)):
                    closure_vars.append(('function', self.
                        serialize_function(cell_contents)))
                else:
                    closure_vars.append(('value', cell_contents))
        glob = {}
        for name in code.co_names:
            if name in func.__globals__:
                value = func.__globals__[name]
                if isinstance(value, types.FunctionType):
                    glob[name] = 'function', self.serialize_function(value)
                else:
                    glob[name] = 'value', self._handle_builtin(value)
        func_data = {'type': func_type, 'code': code_str, 'name': func_name,
            'defaults': func.__defaults__, 'closure_vars': closure_vars,
            'globals': glob, 'kwdefaults': func.__kwdefaults__}
        return pickle.dumps(func_data)

    def deserialize_function(self, serialized_data):
        """Deserialize and reconstruct a function with enhanced handling for special cases."""
        func_data = pickle.loads(serialized_data)
        code_bytes = base64.b64decode(func_data['code'])
        code = marshal.loads(code_bytes)
        glob = {}
        for name, (value_type, value) in func_data['globals'].items():
            if value_type == 'function':
                glob[name] = self.deserialize_function(value)
            else:
                glob[name] = self._restore_builtin(value)
        glob['__builtins__'] = __builtins__
        closure = None
        if func_data['closure_vars']:
            closure_values = []
            for value_type, value in func_data['closure_vars']:
                if value_type == 'function':
                    closure_values.append(self.deserialize_function(value))
                else:
                    closure_values.append(value)
            closure = tuple(types.CellType(value) for value in closure_values)
        func = types.FunctionType(code, glob, func_data['name'], func_data[
            'defaults'], closure)
        if func_data['kwdefaults']:
            func.__kwdefaults__ = func_data['kwdefaults']
        if func_data['type'] == 'classmethod':
            func = classmethod(func)
        elif func_data['type'] == 'staticmethod':
            func = staticmethod(func)
        return func

    def _get_source_debug(self, func):
        """Debug helper to see what source code we're actually getting."""
        original_func = func
        if isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        elif isinstance(func, types.MethodType):
            func = func.__func__
        print('\nAttempting to get source for:', original_func)
        try:
            source = inspect.getsource(original_func)
            print('Got source from original_func:', source[:100])
            return source
        except (OSError, TypeError) as e:
            print('Failed original_func:', str(e))
            try:
                source = inspect.getsource(func)
                print('Got source from func:', source[:100])
                return source
            except (OSError, TypeError) as e:
                print('Failed func:', str(e))
                try:
                    if isinstance(original_func, types.MethodType):
                        source = inspect.getsource(original_func.__self__.
                            __class__.__dict__[original_func.__name__])
                        print('Got source from class dict:', source[:100])
                        return source
                    else:
                        source = inspect.getsource(original_func.__class__.
                            __dict__[original_func.__name__])
                        print('Got source from class dict:', source[:100])
                        return source
                except (OSError, TypeError, KeyError, AttributeError) as e:
                    print('Failed class dict:', str(e))
                    return None


def test_serialization():
    """Test the enhanced serialization system with various function types."""
    serializer = EnhancedFunctionSerializer()
    lambda_func = lambda x: x * 2

    def static_func(x):
        return x * 3
    static_method = staticmethod(static_func)

    def class_func(cls, x):
        return x * 10
    class_method = classmethod(class_func)

    def create_multiplier(factor):

        def multiplier(x):
            return x * factor
        return multiplier

    def process_list(lst):
        return list(map(str, filter(lambda x: x > 0, lst)))
    test_cases = [('Lambda', lambda_func, 5), ('StaticMethod',
        static_method, 6), ('ClassMethod', class_method, 3), ('Closure',
        create_multiplier(7), 3), ('BuiltinsUser', process_list, [-1, 0, 1,
        2, 3])]
    for name, func, test_input in test_cases:
        print(f'\nTesting {name}:')
        try:
            if name == 'ClassMethod':


                class DummyClass:
                    pass
                original_output = func.__get__(None, DummyClass)(test_input)
            else:
                original_output = func(test_input)
            print(f'Original output: {original_output}')
            serialized = serializer.serialize_function(func)
            restored_func = serializer.deserialize_function(serialized)
            if name == 'ClassMethod':
                restored_output = restored_func.__get__(None, DummyClass)(test_input)
            else:
                restored_output = restored_func(test_input)
            print(f'Restored output: {restored_output}')
            assert original_output == restored_output
            print('. Test passed')
        except Exception as e:
            print(f'X Test failed: {str(e)}')
    print('\nTesting super() detection:')
    try:
        derived = Derived()
        serializer.serialize_function(derived.method)
        print('X Failed to detect super() usage')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')
    except Exception as e:
        print(f'X Unexpected error: {str(e)}')

    print('\nTesting class construction detection:')
    try:
        serializer.serialize_function(Example.create)
        print('X Failed to detect class construction')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')

    print('\nTesting parent method reference detection:')
    try:
        child = Child()
        source = serializer._get_source_debug(child.method)
        print("Source code to analyze:", source)
        serializer.serialize_function(child.method)
        print('X Failed to detect parent method reference')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')

    def safe_method(x):
        return x * 2

    print('\nTesting safe method:')
    try:
        serializer.serialize_function(safe_method)
        print('+ Safe method serialized successfully')
    except InheritanceError as e:
        print(f'X Unexpected error: {str(e)}')
        print(f'✗ Test failed: {str(e)}')


class Base:

    def method(self):
        return 'base'


class Derived(Base):

    def method(self):
        return super().method()


class Example:

    @classmethod
    def create(cls, param):
        return cls(param)


class Parent:

    def helper(self):
        return 'help'


class Child(Parent):

    def method(self):
        return self.helper()


def test_inheritance_safety():
    """Test the inheritance safety checks."""
    serializer = EnhancedFunctionSerializer()
    print('\nTesting super() detection:')
    try:
        derived = Derived()
        serializer.serialize_function(derived.method)
        print('X Failed to detect super() usage')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')
    except Exception as e:
        print(f'X Unexpected error: {str(e)}')
    print('\nTesting class construction detection:')
    try:
        serializer.serialize_function(Example.create)
        print('X Failed to detect class construction')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')
    print('\nTesting parent method reference detection:')
    try:
        serializer.serialize_function(Child.method)
        print('X Failed to detect parent method reference')
    except InheritanceError as e:
        print(f'+ Caught expected error: {str(e)}')

    def safe_method(x):
        return x * 2
    print('\nTesting safe method:')
    try:
        serializer.serialize_function(safe_method)
        print('+ Safe method serialized successfully')
    except InheritanceError as e:
        print(f'X Unexpected error: {str(e)}')


if __name__ == '__main__':
    test_serialization()
    test_inheritance_safety()


class InheritanceChecker(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self.has_super = False
        self.has_cls_construction = False
        self.has_parent_refs = False
        self.inside_class_method = False
        self.current_scope = []
        self.method_calls = set()
        self.in_method = False

    def visit_ClassDef(self, node):
        self.current_scope.append(('class', node.name))
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node):
        self.current_scope.append(('function', node.name))
        self.in_method = True
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name
                ) and decorator.id == 'classmethod':
                self.inside_class_method = True
        self.generic_visit(node)
        self.in_method = False
        self.current_scope.pop()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'super':
            self.has_super = True
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name
                    ) and node.func.value.func.id == 'super':
                    self.has_super = True
            elif isinstance(node.func.value, ast.Name
                ) and node.func.value.id == 'super':
                self.has_super = True
        if self.inside_class_method:
            if isinstance(node.func, ast.Name) and node.func.id == 'cls':
                self.has_cls_construction = True
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name
                    ) and node.func.value.id == 'cls':
                    self.has_cls_construction = True
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name
                ) and node.func.value.id in ('self', 'super'):
                self.method_calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in ('self',
            'super'):
            current_method = next((scope[1] for scope in reversed(self.
                current_scope) if scope[0] == 'function'), None)
            if current_method and node.attr != current_method:
                self.has_parent_refs = True
        self.generic_visit(node)
