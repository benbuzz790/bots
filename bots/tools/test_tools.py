import pytest
import networkx as nx
from typing import Dict, List, Set, Tuple
import subprocess
import time
import ast
import os
import importlib
import inspect
from pathlib import Path
from collections import defaultdict


class DependencyVisitor(ast.NodeVisitor):
    """AST visitor to find test dependencies"""

    def __init__(self):
        self.imports = set()
        self.function_calls = set()
        self.class_refs = set()
        self.fixtures_used = set()

    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for name in node.names:
            import_name = f'{module}.{name.name}' if module else name.name
            self.imports.add(import_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.function_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.function_calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.class_refs.add(node.id)
        self.generic_visit(node)


def _get_test_file_path(test_name: str) ->str:
    """Convert test name to file path"""
    parts = test_name.split('::')
    return parts[0] if parts else None


def _analyze_test_dependencies(test_file: str) ->Dict[str, Set[str]]:
    """Analyze test file using AST to find dependencies, including file-level imports"""
    try:
        with open(test_file, 'r') as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        raise
    file_visitor = DependencyVisitor()
    file_visitor.visit(tree)
    file_level_imports = file_visitor.imports
    test_deps = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                visitor = DependencyVisitor()
                visitor.visit(node)
                visitor.imports.update(file_level_imports)
                fixtures = {arg.arg for arg in node.args.args}
                visitor.fixtures_used.update(fixtures)
                test_deps[node.name] = {'imports': visitor.imports,
                    'functions': visitor.function_calls, 'classes': visitor
                    .class_refs, 'fixtures': visitor.fixtures_used}
    return test_deps


def _find_missing_dependencies(test_deps: Dict[str, Set[str]],
    available_fixtures: Set[str]) ->Set[str]:
    """
    Find missing dependencies by comparing test dependencies against available fixtures
    
    Args:
        test_deps: Dictionary containing test dependencies (imports, functions, classes, fixtures)
        available_fixtures: Set of available pytest fixtures
    
    Returns:
        Set of missing dependencies (fixtures that are required but not available)
    """
    missing_deps = set()
    if 'fixtures' in test_deps:
        required_fixtures = test_deps['fixtures']
        missing_fixtures = required_fixtures - available_fixtures - {'self'}
        missing_deps.update(missing_fixtures)
    return missing_deps


def _run_tests_with_timeout(timeout_seconds: int=300, test_dir: str='.'
    ) ->Dict[str, Dict]:
    """
    Run pytest with a timeout and return detailed results of each test

    Args:
        timeout_seconds: Maximum time to allow for all tests
        test_dir: Directory containing test files to analyze
    """
    start_time = time.time()
    test_results = {}
    try:
        test_files = []
        for root, _, files in os.walk(test_dir):
            for file in files:
                if (file.startswith('test_') or file.endswith('_test.py')
                    ) and file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    test_files.append(full_path)
        if not test_files:
            return test_results
        available_fixtures = set()
        try:
            fixture_output = subprocess.run(['pytest', '--fixtures'],
                capture_output=True, text=True, timeout=timeout_seconds - (
                time.time() - start_time))
            available_fixtures = {line.split()[0] for line in
                fixture_output.stdout.split('\n') if line.strip() and not
                line.startswith(' ')}
        except (subprocess.TimeoutExpired, Exception):
            pass
        for test_file in test_files:
            try:
                deps = _analyze_test_dependencies(test_file)
                discover_result = subprocess.run(['pytest', test_file,
                    '--collect-only', '-q'], capture_output=True, text=True,
                    timeout=timeout_seconds - (time.time() - start_time))
                for test_name, test_deps in deps.items():
                    if test_name.startswith('test_'):
                        full_test_id = f'{test_file}::{test_name}'
                        try:
                            test_result = subprocess.run(['pytest',
                                full_test_id, '-v'], capture_output=True,
                                text=True, timeout=timeout_seconds - (time.
                                time() - start_time))
                            missing_deps = _find_missing_dependencies(test_deps
                                , available_fixtures)
                            test_results[full_test_id] = {'passed': 
                                test_result.returncode == 0, 'dependencies':
                                test_deps, 'missing_dependencies':
                                missing_deps, 'output': test_result.stdout}
                        except subprocess.TimeoutExpired:
                            test_results[full_test_id] = {'passed': False,
                                'dependencies': test_deps,
                                'missing_dependencies': {'timeout'},
                                'output': 'Test timed out'}
            except Exception:
                continue
    except Exception:
        pass
    return test_results


def _build_dependency_graph(test_results: Dict[str, Dict]) ->nx.DiGraph:
    """Build a dependency graph based on test relationships, results, and actual dependencies"""
    G = nx.DiGraph()
    for test, result in test_results.items():
        G.add_node(test, passed=result['passed'], missing_deps=result.get(
            'missing_dependencies', set()), dependencies=result.get(
            'dependencies', {}))
    for test, result in test_results.items():
        if not result['passed']:
            deps = result.get('dependencies', {})
            for dep_type, dep_set in deps.items():
                for dep in dep_set:
                    for other_test, other_result in test_results.items():
                        if other_test != test:
                            other_deps = other_result.get('dependencies', {})
                            if any(dep in d for d in other_deps.values()):
                                G.add_edge(other_test, test, type=dep_type)
    return G


def _recommend_debug_order(G: nx.DiGraph) ->List[Tuple[str, Set[str]]]:
    """
    Recommend debug order based on graph traversal ensuring that:
    1. We complete all related dependency chains before moving to unrelated tests
    2. We never move to a dependent test if we just fixed an independent test
    3. We prioritize tests with fewer missing dependencies
    """
    failed_nodes = {node for node in G.nodes if not G.nodes[node]['passed']}
    if not failed_nodes:
        return []
    failed_subgraph = G.subgraph(failed_nodes)
    components = list(nx.weakly_connected_components(failed_subgraph))

    def component_complexity(component):
        subg = failed_subgraph.subgraph(component)
        return sum(len(G.nodes[n]['missing_deps']) for n in component), -len(
            component)
    components.sort(key=component_complexity)
    result_order = []
    for component in components:
        component_graph = failed_subgraph.subgraph(component)
        independent_nodes = {node for node in component_graph.nodes if 
            component_graph.in_degree(node) == 0}
        sorted_independent = sorted(independent_nodes, key=lambda n: len(G.
            nodes[n]['missing_deps']))
        for node in sorted_independent:
            result_order.append((node, G.nodes[node]['missing_deps']))
        remaining_nodes = set(component) - independent_nodes
        while remaining_nodes:
            ready_nodes = {node for node in remaining_nodes if all(pred not in
                remaining_nodes for pred in component_graph.predecessors(node))
                }
            if not ready_nodes:
                ready_nodes = {min(remaining_nodes, key=lambda n: (len(G.
                    nodes[n]['missing_deps']), component_graph.in_degree(n)))}
            sorted_ready = sorted(ready_nodes, key=lambda n: (len(G.nodes[n
                ]['missing_deps']), component_graph.in_degree(n)))
            for node in sorted_ready:
                result_order.append((node, G.nodes[node]['missing_deps']))
                remaining_nodes.remove(node)
    return result_order


def run_tests():
    """Run tests and provide a report with recommended debug order.
    Creates [filename]_results.txt files for each test file, containing the
    pytest output.

    Categories (in priority order):
    1. Syntax Errors
    2. Missing Dependencies (from static analysis)
    3. Import Errors (runtime)
    4. Other Failures

    Returns:
        dict: A report containing:
            - summary: Basic test statistics
            - categorized errors with number of dependencies, 
            listed in recommended debug order
    """
    import subprocess
    import json
    from pathlib import Path
    from bots.tools.test_tools import _run_tests_with_timeout, _build_dependency_graph, _recommend_debug_order, _find_missing_dependencies, _analyze_test_dependencies
    test_dir = 'C:\\Users\\Ben Rinauto\\Code\\temp'
    test_results = _run_tests_with_timeout(300, test_dir)

    def categorize_error(test_result):
        """Categorize error based on exception type, message, and missing dependencies."""
        output = test_result.get('output', '')
        if 'SyntaxError' in output or 'IndentationError' in output:
            return 'syntax'
        if test_result.get('missing_dependencies'):
            return 'missing_deps'
        if 'ImportError' in output or 'ModuleNotFoundError' in output:
            return 'import'
        return 'other'

    def count_minimal_dependencies(test_name, results):
        """Count only direct code dependencies (imports, inheritance, direct calls)."""
        count = 0
        if test_name in results:
            deps = results[test_name].get('dependencies', {})
            count += len(deps.get('imports', set()))
            count += len(deps.get('classes', set()))
            count += len(deps.get('functions', set()))
        return count
    file_tests = {}
    for test_name in test_results:
        file_path = test_name.split('::')[0]
        if file_path not in file_tests:
            file_tests[file_path] = []
        file_tests[file_path].append(test_name)
    for file_path in file_tests:
        try:
            result = subprocess.run(['pytest', file_path, '-v'],
                capture_output=True, text=True, timeout=30)
            results_file = Path(file_path
                ).parent / f'{Path(file_path).stem}_results.txt'
            with open(results_file, 'w') as f:
                f.write(result.stdout + result.stderr)
        except Exception as e:
            results_file = Path(file_path
                ).parent / f'{Path(file_path).stem}_results.txt'
            with open(results_file, 'w') as f:
                f.write(f'Error running tests: {str(e)}')
    categories = {'syntax': [], 'missing_deps': [], 'import': [], 'other': []}
    for test_name, result in test_results.items():
        if not result['passed']:
            category = categorize_error(result)
            dep_count = count_minimal_dependencies(test_name, test_results)
            simple_name = test_name.split('::')[-1]
            if category == 'missing_deps':
                missing = list(result.get('missing_dependencies', set()))
                categories[category].append((simple_name, dep_count, missing))
            else:
                categories[category].append((simple_name, dep_count))
    for category, tests in categories.items():
        if category == 'missing_deps':
            categories[category].sort(key=lambda x: (len(x[2]), x[1]))
        else:
            categories[category].sort(key=lambda x: x[1])
    report = {'summary': {'total': len(test_results), 'failed': sum(1 for r in
        test_results.values() if not r['passed']), 'passed': sum(1 for r in
        test_results.values() if r['passed']), 'skipped': sum(1 for r in
        test_results.values() if 'skipped' in r.get('output', '').lower())},
        'categories': [{'name': 'Syntax Errors', 'tests': categories[
        'syntax'], 'error_type': 'syntax', 'priority': 1}, {'name':
        'Missing Dependencies', 'tests': categories['missing_deps'],
        'error_type': 'missing_deps', 'priority': 2}, {'name':
        'Import Errors', 'tests': categories['import'], 'error_type':
        'import', 'priority': 3}, {'name': 'Other Failures', 'tests':
        categories['other'], 'error_type': 'other', 'priority': 4}]}
    report['categories'] = [cat for cat in report['categories'] if cat['tests']
        ]
    return json.dumps(report, indent=2)


if __name__ == '__main__':
    print(run_tests())
