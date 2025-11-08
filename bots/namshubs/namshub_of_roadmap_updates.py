"""Roadmap updates namshub - updates roadmap after PR completion.

This namshub transforms the bot into a roadmap maintenance specialist that:
1. Analyzes merged PRs to understand what was delivered
2. Identifies which roadmap items are affected
3. Verifies completeness by comparing PR deliverables against full item scope
4. Updates roadmap files (phase files, archives, item index)
5. Commits changes with clear messages

The bot is equipped with terminal tools, code viewing, and file editing
capabilities to analyze PRs and update roadmap documentation.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    chain_workflow,
    create_toolkit,
    format_final_summary,
    validate_required_params,
)
from bots.tools.code_tools import patch_edit, view, view_dir
from bots.tools.python_execution_tool import execute_python
from bots.tools.self_tools import branch_self
from bots.tools.terminal_tools import execute_powershell


def _set_roadmap_system_message(bot: Bot, pr_number: str = None) -> None:
    """Set specialized system message for roadmap update workflow.

    Parameters:
        bot (Bot): The bot to configure
        pr_number (str, optional): The PR number being analyzed
    """
    pr_context = f" for PR #{pr_number}" if pr_number else ""
    system_message = f"""You are a roadmap maintenance specialist for the bots project.

Your task: Update the roadmap after the most recent pull requests were merged{pr_context}.

ROADMAP STRUCTURE:

roadmap/
├── ROADMAP.md              # Strategic planning document
├── README.md               # Navigation hub
├── ITEM_INDEX.md           # Searchable index of all items
├── PHILOSOPHY.md           # Development philosophy
├── MONETIZATION.md         # Business strategy
├── active/                 # Current work items
│   ├── phase1_foundation.md
│   ├── phase2_features.md
│   ├── phase3_enhancement.md
│   ├── phase4_revenue.md
│   └── unscheduled.md
├── completed/              # Finished items
│   ├── 2025-10_foundation.md
│   └── 2025-11_infrastructure.md
└── initiatives/            # Major multi-item efforts
    ├── observability.md
    ├── cross_platform.md
    ├── mcp_integration.md
    ├── documentation_service.md
    ├── cli_improvements.md
    └── test_infrastructure.md

WORKFLOW:

1. ANALYZE PR
   - Identify recent PRs
   - Get PR details: gh pr view <number> --json title,body,mergedAt,files
   - Understand what was delivered
   - Identify key features, fixes, and tests added
   - Note any remaining work mentioned

2. IDENTIFY ROADMAP ITEMS
   - Read roadmap/ITEM_INDEX.md to see all items
   - Read relevant phase files (active/phase*.md)
   - Find which items this PR relates to
   - For each item: note current status and how PR affects it

3. VERIFY COMPLETENESS
   - Read FULL item description from roadmap
   - Compare PR deliverables against complete item scope
   - Determine correct status:
     * DONE ✅: 100% of scope delivered
     * PARTIAL ⚠️: Significant progress, major work remains
     * IN PROGRESS 🚧: Some progress, mostly incomplete
   - Be conservative: only mark DONE if truly complete

4. UPDATE FILES
   For DONE items:
   - Update status in active/phase*.md
   - Add completion entry to completed/YYYY-MM_*.md
   - Update ITEM_INDEX.md status and counts

   For PARTIAL items:
   - Update status and add notes about done vs remaining
   - Update ITEM_INDEX.md

5. COMMIT CHANGES
   - Review all changes
   - Stage files: git add roadmap/
   - Commit: git commit -m "docs: Update roadmap for PR #s - [item titles]"
   - Provide summary of updates

IMPORTANT:
- Read FULL item descriptions before marking complete
- Only mark DONE if 100% of scope is delivered
- Update counts in ITEM_INDEX.md (total completed, partial, etc.)
- Update "Last Updated" dates
- Use proper status markers: ✅ ⚠️ 🚧 ❌
"""
    bot.set_system_message(system_message.strip())


def invoke(bot: Bot, pr_number: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the roadmap update workflow.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        pr_number (str, optional): The PR number that was merged.
                                   If not provided, attempts to extract from conversation.
        **kwargs: Additional parameters (unused, for compatibility)

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # If pr_number not provided, try to extract from conversation context
    if not pr_number:
        if bot.conversation.parent and bot.conversation.parent.content:
            content = bot.conversation.parent.content
            import re

            pr_patterns = [
                r"#(\d+)",
                r"PR\s*#?(\d+)",
                r"pull request\s*#?(\d+)",
            ]
            for pattern in pr_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    pr_number = match.group(1)
                    break

    # Validate required parameters
    valid, error = validate_required_params(pr_number=pr_number)
    if not valid:
        return (
            error + "\nUsage: invoke_namshub('namshub_of_roadmap_updates', pr_number='125')",
            bot.conversation,
        )

    # Configure the bot for roadmap updates
    create_toolkit(bot, execute_powershell, view, view_dir, execute_python, patch_edit, branch_self)
    _set_roadmap_system_message(bot, pr_number)

    # Define the roadmap update workflow
    workflow_prompts = [
        f"Find recent PRs, then analyze PR #{pr_number}. Run: gh pr view {pr_number} --json title,body,mergedAt,files "
        "to get the PR details. Summarize: What was the main goal? What specific features/fixes "
        "were delivered? What tests were added? Any remaining work mentioned?",
        "Identify related roadmap items. Read roadmap/ITEM_INDEX.md to see all items, then read "
        "relevant phase files from roadmap/active/. List which items this PR relates to and how "
        "it affects each one (complete, partial, or just progress).",
        "Verify completeness for each affected item. Read the FULL item description from the roadmap "
        "files. Compare PR deliverables against the complete item scope. Determine the correct status: "
        "DONE (100% complete), PARTIAL (significant progress but major work remains), or IN PROGRESS. "
        "Be conservative - only mark DONE if truly complete.",
        "Update the roadmap files. For DONE items: update status in active/phase*.md, add completion "
        "entry to completed/YYYY-MM_*.md, update ITEM_INDEX.md. For PARTIAL items: update status and "
        "add notes about what's done vs remaining. Use view and python_view to read files, then describe "
        "what changes need to be made.",
        "Update ITEM_INDEX.md counts and dates. Update the total counts (completed, partial, active), "
        "update status tables, and set 'Last Updated' to today's date.",
        f"Commit the changes. Stage files with: git add roadmap/ "
        f'Then commit with: git commit -m "docs: Update roadmap for PR #{pr_number} - [list item titles]" '
        "Provide a summary of all updates made.",
    ]

    # Execute the workflow using chain_workflow with INSTRUCTION pattern
    responses, nodes = chain_workflow(bot, workflow_prompts)

    # Return the final response
    final_summary = format_final_summary(f"Roadmap Update for PR #{pr_number}", len(responses), responses[-1])

    return final_summary, nodes[-1]
