
# diff_edit Investigation Memo

## Context
We rebuilt the test suite for the diff_edit tool to better understand and document its behavior, particularly around indentation handling and git-style diff support. This investigation was motivated by LLMs frequently misusing the tool due to assumptions about how indentation and diff formats would be handled.

### Common LLM Mistakes

1. Indentation Assumptions
   - Assuming indentation from source file would be preserved
   - Not specifying intended indentation in the diff spec
   - Inconsistent indentation between removal and addition blocks

2. Format Confusion
   - Including context lines without +/- markers
   - Expecting git-style behavior for unchanged lines
   
3. Line Number Staleness
   - Any system using line numbers as a way to edit inevitably fails due to line number staleness

## What We've Implemented

### Core Behaviors

1. Indentation Handling
   - The tool preserves indentation from the diff spec in the output
   - Can match blocks regardless of indentation in the source file
   - Both removal (-) and addition (+) lines need to show the intended final indentation
   - Relative indentation within blocks is maintained

2. Git-style Support
   - Accepts but ignores @@ headers (e.g., `@@ -1,4 +1,4 @@`)
   - Accepts but ignores context lines (lines starting with space)
   - Handles multiple diff hunks in a single spec
   - Works with both strict +/- format and git-style diffs

3. Block Matching
   - Matches blocks even with different indentation levels
   - Preserves nested structure indentation
   - Supports flexible matching while maintaining precision in output
