# Context Management Enhancement Ideas
## Current Behavior
The emove_context tool currently deletes bot-user message pairs from the conversation tree, stitching the tree back together. This provides:
- Intentional, traceable removal (labels shift)
- Clean memory reduction
- Auditability through the two-step process (list then remove)
## Proposed Enhancements
### Idea 1: Archive Branch
**Concept**: Rather than deleting nodes completely, create a new "archive" branch and move the selected nodes there.
**Pros**:
- Preserves all conversation history
- Can potentially "restore" archived context if needed
- Clear separation between active and archived context
- Could implement a "view_archive" tool
**Cons**:
- Archive branch still exists in memory (may not reduce token usage much)
- More complex tree structure
- Need to handle where the archive branch attaches (root? current node?)
### Idea 2: New Branch with Removal
**Concept**: Create a new branch from root with selected context removed, but leave the original branch intact.
**Pros**:
- Non-destructive - original conversation preserved
- Can switch between "full" and "pruned" views
- Safe experimentation with context removal
- Could have multiple pruned branches with different removals
**Cons**:
- Doesn't actually reduce memory - both branches exist
- Could lead to confusion about which branch is "active"
- Complexity in managing multiple branches
- May not solve the core problem (reducing token usage)
### Idea 3: Ignore Flags (RECOMMENDED)
**Concept**: Add ignore flags at each node that specify which ancestor nodes to skip when traversing upward. New nodes inherit parent's ignore flags.
**Pros**:
- **Truly non-destructive** - all data remains in tree
- **Effective context reduction** - ignored nodes don't contribute to context
- **Reversible** - can clear ignore flags to "restore" context
- **Flexible** - different branches can ignore different nodes
- **Inheritance works naturally** - child nodes automatically respect parent's ignores
- **Tied to node identity, not labels** - robust as tree changes
- **Could implement "unignore" tool** for restoration
**Cons**:
- Requires modification to conversation traversal logic
- Need to ensure all context-building code respects ignore flags
- Slightly more complex implementation
- Need to handle edge cases (ignoring root, circular ignores, etc.)
## Implementation Notes for Idea 3
### Data Structure
`python
class ConversationNode:
    def __init__(self):
        self.ignore_set = set()  # Set of node IDs to ignore when building context
        # ... existing attributes
`
### Key Functions to Modify
1. Context building/traversal functions must check ignore_set
2. New node creation must inherit parent's ignore_set
3. emove_context becomes ignore_context - adds node IDs to ignore_set
4. New unignore_context tool to remove IDs from ignore_set
5. list_context should show ignored nodes differently (e.g., "[A] (ignored)")
### Advantages Over Current Implementation
- User gets the "amnesia" effect they want (ignored nodes don't appear in context)
- But with full reversibility and data preservation
- Traceable: can see what's ignored
- Intentional: explicit ignore/unignore operations
- Clean: ignored nodes simply don't contribute to token count
## Recommendation
**Idea 3 (Ignore Flags)** is the best approach because it:
1. Achieves the desired behavior (context reduction with traceability)
2. Is fully reversible (can unignore if needed)
3. Doesn't actually delete data (safer)
4. Works naturally with tree inheritance
5. Provides the "selective amnesia" effect the user wants
