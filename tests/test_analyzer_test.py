import os
import pytest
import shutil
from pathlib import Path
import networkx as nx
from bots.tools.test_tools import _analyze_test_dependencies, _build_dependency_graph, _recommend_debug_order, _run_tests_with_timeout
TEST_ROOT = Path(__file__).parent
TEMP_TEST_DIR = TEST_ROOT / 'temp_test_files'


@pytest.fixture(scope='module')
def setup_test_files():
    """Create temporary test files with known dependencies"""
    TEMP_TEST_DIR.mkdir(exist_ok=True)
    yield TEMP_TEST_DIR
    shutil.rmtree(TEMP_TEST_DIR)


def create_test_graph(node_configs):
    """Helper function to create test dependency graphs
    
    Args:
        node_configs: List of tuples (node_name, passed, missing_deps, edges)
            where edges is a list of target nodes this node should connect to
    
    Returns:
        NetworkX DiGraph configured according to inputs
    """
    G = nx.DiGraph()
    for node_name, passed, missing_deps, _ in node_configs:
        G.add_node(node_name, passed=passed, missing_deps=set(missing_deps))
    for node_name, _, _, edges in node_configs:
        for target in edges:
            G.add_edge(node_name, target)
    return G


def test_basic_dependency_chain():
    """Test that a simple linear dependency chain is ordered correctly.
    
    Graph structure:
    test1 -> test2 -> test3
    
    Expected behavior:
    - Should recommend fixing test1 first
    - Then test2
    - Finally test3
    """
    G = create_test_graph([('test1', False, [], ['test2']), ('test2', False,
        [], ['test3']), ('test3', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    assert ordered_tests == ['test1', 'test2', 'test3']


def test_independent_tests_priority():
    """Test that independent tests are prioritized correctly.
    
    Graph structure:
    test1   test2   test3
    (all independent, but with different numbers of missing dependencies)
    
    Expected behavior:
    - Should order tests by number of missing dependencies (fewer first)
    - For equal missing deps, order doesn't matter
    """
    G = create_test_graph([('test1', False, ['dep1', 'dep2'], []), ('test2',
        False, ['dep1'], []), ('test3', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    assert ordered_tests[0] == 'test3'
    assert ordered_tests[1] == 'test2'
    assert ordered_tests[2] == 'test1'


def test_complex_dependency_web():
    """Test handling of a complex web of dependencies.
    
    Graph structure:
    test1 -> test2 -> test4
      ↓       ↓
    test3   test5
    
    Expected behavior:
    - Should start with test1 (root of most dependencies)
    - Should complete each dependency chain before moving to independent chains
    - Should handle branching dependencies correctly
    """
    G = create_test_graph([('test1', False, [], ['test2', 'test3']), (
        'test2', False, [], ['test4', 'test5']), ('test3', False, [], []),
        ('test4', False, [], []), ('test5', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    assert ordered_tests[0] == 'test1'
    test2_idx = ordered_tests.index('test2')
    test4_idx = ordered_tests.index('test4')
    test5_idx = ordered_tests.index('test5')
    assert test2_idx < test4_idx
    assert test2_idx < test5_idx


def test_missing_dependencies_priority():
    """Test that missing dependencies affect priority correctly.
    
    Graph structure:
    test1 -> test2
    test3 -> test4
    
    With test1 having more missing deps than test3.
    
    Expected behavior:
    - Should prioritize the chain starting with fewer missing dependencies
    - Should maintain dependency order within each chain
    """
    G = create_test_graph([('test1', False, ['dep1', 'dep2'], ['test2']), (
        'test2', False, [], []), ('test3', False, ['dep1'], ['test4']), (
        'test4', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    test1_idx = ordered_tests.index('test1')
    test2_idx = ordered_tests.index('test2')
    test3_idx = ordered_tests.index('test3')
    test4_idx = ordered_tests.index('test4')
    assert test3_idx < test1_idx
    assert test4_idx < test1_idx
    assert test1_idx < test2_idx


def test_parallel_chains_priority():
    """Test handling of parallel dependency chains.
    
    Graph structure:
    test1 -> test2 -> test3
    test4 -> test5 -> test6
    
    With varying missing dependencies.
    
    Expected behavior:
    - Should complete one chain before starting another
    - Should prioritize chains based on complexity (missing deps)
    - Should maintain correct order within each chain
    """
    G = create_test_graph([('test1', False, ['dep1'], ['test2']), ('test2',
        False, [], ['test3']), ('test3', False, [], []), ('test4', False, [
        'dep1', 'dep2'], ['test5']), ('test5', False, [], ['test6']), (
        'test6', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    test1_chain = [ordered_tests.index(t) for t in ['test1', 'test2', 'test3']]
    test4_chain = [ordered_tests.index(t) for t in ['test4', 'test5', 'test6']]
    assert max(test1_chain) < min(test4_chain)
    assert test1_chain == sorted(test1_chain)
    assert test4_chain == sorted(test4_chain)


def test_diamond_dependency():
    """Test handling of diamond-shaped dependency patterns.
    
    Graph structure:
        test1
       /     \\
    test2   test3
       \\     /
        test4
    
    Expected behavior:
    - Should handle test4 only after BOTH test2 and test3 are handled
    - Should handle test2 and test3 only after test1
    """
    G = create_test_graph([('test1', False, [], ['test2', 'test3']), (
        'test2', False, [], ['test4']), ('test3', False, [], ['test4']), (
        'test4', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    assert ordered_tests[0] == 'test1'
    assert ordered_tests[-1] == 'test4'
    test2_idx = ordered_tests.index('test2')
    test3_idx = ordered_tests.index('test3')
    assert 0 < test2_idx < len(ordered_tests) - 1
    assert 0 < test3_idx < len(ordered_tests) - 1


def test_mixed_failing_passing():
    """Test handling of graphs with both passing and failing tests.
    
    Graph structure includes passing and failing tests with dependencies.
    
    Expected behavior:
    - Should only include failing tests in the debug order
    - Should maintain correct dependency ordering for failing tests
    - Should consider dependencies through passing tests
    """
    G = create_test_graph([('test1', False, [], ['test2']), ('test2', True,
        [], ['test3']), ('test3', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    assert 'test2' not in ordered_tests
    assert ordered_tests == ['test1', 'test3']


def test_empty_graph():
    """Test handling of empty graphs.
    
    Expected behavior:
    - Should return empty list
    - Should not raise any exceptions
    """
    G = nx.DiGraph()
    debug_order = _recommend_debug_order(G)
    assert debug_order == []


def test_basic_infrastructure():
    """Basic integration test to verify infrastructure works"""
    os.chdir(TEST_ROOT)
    test_results = _run_tests_with_timeout(timeout_seconds=10)
    G = _build_dependency_graph(test_results)
    debug_order = _recommend_debug_order(G)
    assert isinstance(debug_order, list)
    for test, deps in debug_order:
        assert isinstance(test, str)
        assert isinstance(deps, set)


def test_multiple_root_causes():
    """Test handling of multiple independent failure chains.
    
    Graph structure:
    test1 -> test2    test3 -> test4
      |                  |
    test5            test6
    
    With varying missing dependencies across chains.
    
    Expected behavior:
    - Should group related failures together
    - Should handle each failure chain independently
    - Should prioritize chains by total missing dependencies
    - Should maintain correct ordering within each chain
    """
    G = create_test_graph([('test1', False, ['dep1'], ['test2', 'test5']),
        ('test2', False, [], []), ('test3', False, ['dep1', 'dep2'], [
        'test4', 'test6']), ('test4', False, [], []), ('test5', False, [],
        []), ('test6', False, [], [])])
    debug_order = _recommend_debug_order(G)
    ordered_tests = [test for test, _ in debug_order]
    chain1 = [ordered_tests.index(t) for t in ['test1', 'test2', 'test5']]
    chain2 = [ordered_tests.index(t) for t in ['test3', 'test4', 'test6']]
    assert max(chain1) < min(chain2)
    assert chain1 == sorted(chain1)
    assert chain2 == sorted(chain2)
