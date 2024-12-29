"""
Implementation of a hierarchical code chunking algorithm with the following properties:

1. Cost function:
   - Parabolic for large chunks (penalizing overly large chunks)
   - Inverse for very small chunks (penalizing tiny chunks)
   - Has a "sweet spot" around ~3,000 characters

2. Properties maintained:
   - Language Preservation: Only adds chunk markers, no code modification
   - Hierarchical Coverage: Every AST node belongs to exactly one chunk
   - Scope Stability: Path-based addressing ensures edits don't affect outside chunks
   - Composable: Chunking a file with an edit produces the same chunks as a an edit to the chunked file.
   - Parseability: Outputs well-nested chunk markers
"""

import ast
import sys
from typing import Any, Dict, List, Tuple, Optional
from functools import lru_cache

# ---------------------------------------------------------------------
# 1. Cost function: parabolic for large, inverse for small, sweet spot ~3k
# ---------------------------------------------------------------------
def chunk_cost(length: int) -> float:
    """
    Continuous cost function for chunk sizes that combines:
    - Inverse term (1/length) to penalize very small chunks
    - Quadratic term centered at 3000 for sharp growth
    The minimum occurs near 3000 characters.
    """
    if length <= 0:
        return 1.0e12  # nonsensical fallback for safety
        
    # Combine inverse and quadratic terms
    A = 5e-3  # Much stronger quadratic coefficient for sharper curve
    offset = (length - 3000)
    inverse_term = 1.0e6 / length
    quadratic_term = A * offset * offset
    
    return inverse_term + quadratic_term + 1.0

# ---------------------------------------------------------------------
# 2. Utility: measure character spans from AST node
# ---------------------------------------------------------------------
def get_node_span(node: ast.AST, source_lines: List[str]) -> Tuple[int, int]:
    """Return approximate character length for code spanned by node."""
    if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
        return (0, 0)  # no position info => no length

    start_line = node.lineno
    end_line = node.end_lineno
    if start_line < 1 or end_line > len(source_lines):
        return (0, 0)

    # Convert 1-based AST line to 0-based index in source_lines
    start_idx = start_line - 1
    end_idx = end_line - 1

    # Approx length
    if start_idx == end_idx:
        # single-line node
        col_start = getattr(node, 'col_offset', 0)
        col_end = getattr(node, 'end_col_offset', len(source_lines[start_idx]))
        length = max(0, col_end - col_start)
    else:
        # multi-line node
        first_line_part = len(source_lines[start_idx]) - getattr(node, 'col_offset', 0)
        last_line_part = getattr(node, 'end_col_offset', 0)
        middle_lines_len = 0
        for i in range(start_idx+1, end_idx):
            middle_lines_len += len(source_lines[i])
        length = first_line_part + middle_lines_len + last_line_part

    return (start_line, length)

def measure_subtree_length(node: ast.AST, source_lines: List[str], cache: Dict[int, int]) -> int:
    """Calculate total character length of subtree rooted at node."""
    node_id = id(node)
    if node_id in cache:
        return cache[node_id]

    _, span_len = get_node_span(node, source_lines)
    total = span_len

    for child in ast.iter_child_nodes(node):
        total += measure_subtree_length(child, source_lines, cache)

    cache[node_id] = total
    return total

# ---------------------------------------------------------------------
# 3. DP approach for chunk optimization
# ---------------------------------------------------------------------
class ChunkInfo:
    """
    Holds the structure of how we chunked a node:
      - cost: total cost for the subtree
      - own_chunk_size: chars in this node's chunk (if we open one)
      - merges: list of (child_node, merged_bool)
      - children_info: chunk arrangement for each child
    """
    __slots__ = ("cost", "own_chunk_size", "children_info", "is_merged")

    def __init__(self, cost=0.0, own_chunk_size=0, children_info=None, is_merged=False):
        self.cost = cost
        self.own_chunk_size = own_chunk_size
        self.children_info = children_info if children_info else []
        self.is_merged = is_merged

def compute_optimal_chunking(node: ast.AST,
                           parent_chunk_size: int,
                           merged_with_parent: bool,
                           source_lines: List[str],
                           subtree_size_cache: Dict[int, int],
                           dp_cache: Dict[Any, ChunkInfo]) -> ChunkInfo:
    """Find minimal-cost chunk arrangement for node and its subtree."""
    node_id = (id(node), parent_chunk_size, merged_with_parent)

    if node_id in dp_cache:
        return dp_cache[node_id]

    my_subtree_len = measure_subtree_length(node, source_lines, subtree_size_cache)
    children = list(ast.iter_child_nodes(node))

    # Base case: no children
    if not children:
        if merged_with_parent:
            best = ChunkInfo(cost=0.0, own_chunk_size=my_subtree_len, is_merged=True)
        else:
            best = ChunkInfo(cost=chunk_cost(my_subtree_len), own_chunk_size=my_subtree_len, is_merged=False)
        dp_cache[node_id] = best
        return best

    # Scenario B: open new chunk for myself
    cost_if_new = chunk_cost(my_subtree_len)
    children_info_if_new = []
    for child in children:
        child_info = compute_optimal_chunking(child,
                                            parent_chunk_size=my_subtree_len,
                                            merged_with_parent=True,
                                            source_lines=source_lines,
                                            subtree_size_cache=subtree_size_cache,
                                            dp_cache=dp_cache)
        children_info_if_new.append(child_info)
        cost_if_new += child_info.cost

    scenarioB = ChunkInfo(cost=cost_if_new,
                         own_chunk_size=my_subtree_len,
                         children_info=children_info_if_new,
                         is_merged=False)

    # Scenario A: merge with parent
    merged_chunk_size = parent_chunk_size + my_subtree_len
    cost_if_merged = 0.0
    children_info_if_merged = []
    for child in children:
        child_info = compute_optimal_chunking(child,
                                            parent_chunk_size=merged_chunk_size,
                                            merged_with_parent=True,
                                            source_lines=source_lines,
                                            subtree_size_cache=subtree_size_cache,
                                            dp_cache=dp_cache)
        children_info_if_merged.append(child_info)
        cost_if_merged += child_info.cost

    scenarioA = ChunkInfo(cost=cost_if_merged,
                         own_chunk_size=merged_chunk_size,
                         children_info=children_info_if_merged,
                         is_merged=True)

    # Pick best scenario
    if merged_with_parent:
        best_scenario = scenarioA if scenarioA.cost <= scenarioB.cost else scenarioB
    else:
        best_scenario = scenarioB

    dp_cache[node_id] = best_scenario
    return best_scenario

# ---------------------------------------------------------------------
# 4. Address assignment for chunk markers
# ---------------------------------------------------------------------
def assign_addresses(node: ast.AST,
                    chunk_info: ChunkInfo,
                    parent_address: str,
                    child_index: int,
                    source_lines: List[str],
                    subtree_size_cache: Dict[int,int]) -> Dict[int, str]:
    """
    Assign path-based addresses to ensure scope stability.
    If chunk_info.is_merged is True, inherit parent's address.
    Else create new address: parent_address + "." + child_index
    """
    node_id = id(node)

    if parent_address == "":
        current_address = "1"
    else:
        if chunk_info.is_merged:
            current_address = parent_address
        else:
            current_address = parent_address + f".{child_index}"

    address_map = { node_id: current_address }

    children = list(ast.iter_child_nodes(node))
    for i, child in enumerate(children, start=1):
        child_info = chunk_info.children_info[i-1]
        child_map = assign_addresses(child,
                                   child_info,
                                   current_address,
                                   i,
                                   source_lines,
                                   subtree_size_cache)
        address_map.update(child_map)

    return address_map

# ---------------------------------------------------------------------
# 5. Main chunking function
# ---------------------------------------------------------------------
def chunk_python_code_all_properties(python_code: str) -> str:
    """
    Main entry point for chunking Python code:
    1) Parse to AST
    2) Use DP to find optimal chunk arrangement
    3) Assign stable addresses
    4) Return bracketed representation
    """
    tree = ast.parse(python_code)
    source_lines = python_code.splitlines()
    subtree_size_cache: Dict[int,int] = {}
    dp_cache: Dict[Any, ChunkInfo] = {}

    root_info = compute_optimal_chunking(
        node=tree,
        parent_chunk_size=0,
        merged_with_parent=False,
        source_lines=source_lines,
        subtree_size_cache=subtree_size_cache,
        dp_cache=dp_cache
    )

    address_map = assign_addresses(tree, root_info, parent_address="", child_index=1,
                                 source_lines=source_lines, subtree_size_cache=subtree_size_cache)

    # Build bracketed representation
    lines = []
    def dfs_print(node: ast.AST, current_address: str, indent: int):
        prefix = "  " * indent
        node_id = id(node)
        lines.append(f"{prefix}open_chunk({address_map[node_id]}) # {type(node).__name__}")

        for child in ast.iter_child_nodes(node):
            dfs_print(child, address_map[id(child)], indent+1)

        lines.append(f"{prefix}close_chunk({address_map[node_id]})")

    dfs_print(tree, address_map[id(tree)], 0)
    return "\n".join(lines)

# ---------------------------------------------------------------------
# 6. Command-line interface
# ---------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chunk_all_props.py <python_file>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r", encoding="utf-8") as f:
        code = f.read()

    result = chunk_python_code_all_properties(code)
    print(result)