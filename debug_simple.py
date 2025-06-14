import sys
import inspect
import bots.flows.functional_prompts as fp
"""Simple debug test to expose key issues."""
sys.path.insert(0, '.')
print("FUNCTIONAL PROMPTS DEBUG ANALYSIS")
print("=" * 40)
# Check what functions exist
functions = [name for name in dir(fp) if callable(getattr(fp, name)) and (not name.startswith('_'))]
print(f"Found {len(functions)} functions:")
for func in sorted(functions):
    print(f"  - {func}")
print("\nSIGNATURE ANALYSIS:")
print("-" * 20)
# Analyze key functions
key_functions = ['single_prompt', 'chain', 'branch', 'prompt_while', 'tree_of_thought']
for func_name in key_functions:
    if hasattr(fp, func_name):
        func = getattr(fp, func_name)
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        print(f"{func_name}: {params}")
        # Check callback parameter
        if 'callback' in params:
            callback_param = sig.parameters['callback']
            print(f"  callback annotation: {callback_param.annotation}")
    else:
        print(f"{func_name}: NOT FOUND")
print("\nISSUES IDENTIFIED:")
print("-" * 20)
print("1. Return type inconsistency - some return single, some return lists")
print("2. Callback signature mismatches between functions")
print("3. Conversation tree linking issues in parallel functions")
print("4. Leaf finding logic may have problems")