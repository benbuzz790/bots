from bots.flows.flows import resolve_issue_flow
import pytest
from unittest.mock import Mock, patch
from bots.foundation.base import Bot, ToolHandler
from bots.foundation.anthropic_bots import AnthropicBot

def test_resolve_mechanics_issue():
    """
    Integration test for resolve_issue_flow using mechanics library.
    
    This test:
    1. Creates a fresh copy of the broken mechanics repo
    2. Creates a local issue file about the kinetic energy calculation bug
    3. Uses resolve_issue_flow to fix it
    4. Verifies the fix matches the working version
    """
    import os
    import shutil
    from pathlib import Path
    
    # Setup test directories
    test_dir = Path("benbuzz790/private_tests")
    broken_repo = test_dir / "test_repo_broken"
    working_repo = test_dir / "test_repo"
    test_copy = test_dir / "test_repo_copy"
    
    # Create fresh copy of broken repo
    if test_copy.exists():
        shutil.rmtree(test_copy)
    shutil.copytree(broken_repo, test_copy)
    
    # Create local issue file
    issue_file = test_copy / "ISSUE.md"
    test_issue_content = """Bug: Kinetic Energy Calculation Incorrect for 3D Motion

The kinetic energy calculation in mechanics.py appears to be incorrect for objects moving in multiple dimensions.

Example that demonstrates the bug:
```python
from mechanics import State, calculate_kinetic_energy

# Object moving at 3 m/s in x and 4 m/s in y (5 m/s total speed)
state = State(velocity=(3, 4, 0), mass=2.0)
ke = calculate_kinetic_energy(state)
print(ke)  # Outputs wrong value
```

Expected behavior:
- For a 2kg mass moving at 5 m/s total speed, KE should be 25 joules (1/2 * 2kg * (5m/s)^2)

Actual behavior:
- Function only considers x-component of velocity
- Gives 9 joules (1/2 * 2kg * (3m/s)^2)

Please fix the kinetic energy calculation to properly handle 3D motion.
"""
    issue_file.write_text(test_issue_content)
    
    # Create test bot
    bot = AnthropicBot(
        max_tokens=4096,
        temperature=0.7,
        name="mechanics_test_bot"
    )
    
    # Use resolve_issue_flow to fix the bug
    result = resolve_issue_flow(
        bot,
        repo=str(test_copy),
        issue_number="1"  # Local issue file
    )
    
    # Verify the fix by comparing with working version
    import sys
    sys.path.append(str(test_copy))
    sys.path.append(str(working_repo))
    
    from mechanics import State, calculate_kinetic_energy as fixed_ke
    test_state = State(velocity=(3, 4, 0), mass=2.0)
    
    sys.path.pop()
    sys.path.pop()
    
    import importlib
    working_mechanics = importlib.import_module("test_repo.mechanics")
    working_ke = working_mechanics.calculate_kinetic_energy
    
    # Create identical state for working version
    working_state = working_mechanics.State(velocity=(3, 4, 0), mass=2.0)
    
    # Compare results
    fixed_result = fixed_ke(test_state)
    expected_result = working_ke(working_state)
    
    assert fixed_result == expected_result, f"Fixed KE {fixed_result} != Expected KE {expected_result}"
    
    # Cleanup
    shutil.rmtree(test_copy)
