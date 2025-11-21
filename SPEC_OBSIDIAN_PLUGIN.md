# Specification: Obsidian Vault Agent Plugin
## Overview
An Obsidian plugin that embeds the bots CLI, providing an AI agent with vault-specific tools that maintain vault integrity through contract-based validation.
## Motivation
Obsidian users want AI assistance for vault management, but need guarantees that the AI won't break their carefully organized knowledge base. By using contract-based tools, the agent can be creative and autonomous while operating within user-defined constraints.
## Architecture
### High-Level Design
```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Obsidian Plugin (TypeScript)      Ã¢â€â€š
Ã¢â€â€š                                      Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  Chat UI Component             Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Message display             Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Input box                   Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Tree navigation controls    Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ Ã¢â€â€š
Ã¢â€â€š              Ã¢â€â€š                       Ã¢â€â€š
Ã¢â€â€š              Ã¢â€“Â¼                       Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  Python Subprocess Manager     Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Start/stop bots CLI         Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Send messages               Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - Receive responses           Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
              Ã¢â€â€š
              Ã¢â€“Â¼
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Python Process (bots CLI)         Ã¢â€â€š
Ã¢â€â€š                                      Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  Bot with Obsidian Tools       Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - create_note()               Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - update_note()               Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - add_link()                  Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - search_vault()              Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - etc.                        Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ Ã¢â€â€š
Ã¢â€â€š              Ã¢â€â€š                       Ã¢â€â€š
Ã¢â€â€š              Ã¢â€“Â¼                       Ã¢â€â€š
Ã¢â€â€š  Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  Contract Validators           Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - is_valid_markdown()         Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - no_orphaned_notes()         Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - valid_frontmatter()         Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€š  - etc.                        Ã¢â€â€š Ã¢â€â€š
Ã¢â€â€š  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
              Ã¢â€â€š
              Ã¢â€“Â¼
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š   Obsidian Vault (Filesystem)       Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```
### Components
#### 1. Obsidian Plugin (TypeScript)
- **Chat UI**: Renders conversation tree, handles user input
- **Subprocess Manager**: Spawns Python process running bots CLI
- **IPC**: Communicates with Python process via stdin/stdout
#### 2. Python Bot Module
- **Bot Instance**: AnthropicBot (or other provider) with Obsidian tools
- **Obsidian Tools**: Vault manipulation functions wrapped with `@toolify`
- **Contract Validators**: Pure functions that check vault invariants
#### 3. Vault Interface
- **Read Operations**: Search, query metadata, extract links
- **Write Operations**: Create/update/delete notes, modify frontmatter
## Obsidian Tools
### Design Philosophy
The toolset is designed for **efficient exploration and safe modification** of the vault:
- **Navigation tools** provide structural overview without overwhelming context
- **Search tools** enable precise content discovery
- **Editing tools** reuse proven code_tools (view, patch_edit) with vault-specific contracts
- **Meta tools** enable parallel work and external information gathering
### Tool Categories
#### Navigation & Discovery
```python
@toolify(
    description="Display vault link structure as a tree from a starting note"
)
def link_view(start_note: str, max_depth: int = 3, max_nodes: int = 100) -> str:
    """
    Show the link structure of the vault as a tree, starting from start_note.
    Uses scope-aware truncation similar to python_view and view_dir:
    - Shows note titles and their connections
    - Truncates at max_depth or max_nodes to prevent context overflow
    - Clips cycles (shows note only once in tree)
    - Indicates truncation with "..." when limits reached
    Returns a tree-like text representation:
        Start Note
            → Linked Note 1
                → Sub-linked Note A
                → Sub-linked Note B
            → Linked Note 2
                ...
    """
    pass
@toolify(
    description="Find the most connected/central notes in the vault"
)
def rootiest_nodes(n: int = 10) -> str:
    """
    Find the N most connected notes in the vault.
    Uses link analysis (similar to PageRank) to identify:
    - Hub notes (many outgoing links)
    - Authority notes (many incoming links)
    - Bridge notes (connect different clusters)
    Returns list of note titles with connection counts.
    Useful for finding entry points into the vault.
    """
    pass
@toolify(
    description="Search vault content using regex patterns"
)
def regex_search(pattern: str, folder: str = "", max_results: int = 50) -> str:
    """
    Search vault for notes matching the regex pattern.
    Searches note content (not just titles) and returns:
    - Note title
    - Matching line with context
    - Line number
    Supports full Python regex syntax.
    For simple keyword search, just use the keyword as pattern.
    """
    pass
```
#### Content Operations
```python
# Reuse proven tools from bots.tools.code_tools with vault-specific contracts
@toolify(
    description="View the content of a note",
    # Imported from code_tools, no contracts needed for read-only
)
def view(filepath: str, start_line: int = None, end_line: int = None) -> str:
    """
    Display note content with line numbers.
    Supports optional line range for large notes.
    """
    pass
@toolify(
    description="Edit a note using unified diff format",
    postconditions=[is_valid_markdown, has_valid_frontmatter, no_broken_links]
)
def patch_edit(filepath: str, patch: str) -> str:
    """
    Edit a note using unified diff format.
    Contracts ensure:
    - Result is valid markdown
    - Frontmatter remains valid YAML
    - No broken wikilinks are created
    This is the primary editing tool - proven reliable from code_tools.
    """
    pass
```
#### Meta Tools
```python
@toolify(
    description="Create parallel branches to work on multiple notes simultaneously"
)
def branch_self(self_prompts: str, allow_work: str = "True", parallel: str = "True") -> str:
    """
    Create parallel instances of the bot to work on different notes.
    Example use cases:
    - Update multiple related notes in parallel
    - Explore different sections of the vault simultaneously
    - Compare different approaches to organizing content
    Each branch has independent context and can use all vault tools.
    """
    pass
@toolify(
    description="Search the web for information"
)
def web_search(question: str) -> str:
    """
    Perform web search to gather external information.
    Useful for:
    - Fact-checking note content
    - Finding sources to link
    - Researching topics for new notes
    """
    pass
```
### Removed Tools
The following tools were considered but removed for efficiency:
- ~~ollow_links(note, depth)~~ - Replaced by link_view() which provides better overview
- ~~ind_path(source, target)~~ - Too specific, link_view() shows paths naturally
- ~~get_neighborhood(note, radius)~~ - Redundant with link_view()
- ~~keyword_search()~~ - Replaced by more powerful
egex_search()
- ~~create_note(), update_note(), delete_note()~~ - Replaced by patch_edit() which is more flexible and proven
- ~~dd_link(), update_frontmatter(), dd_tags()~~ - All handled by patch_edit()
### Tool Design Rationale
**Why reuse code_tools?**
- iew() and patch_edit() are battle-tested in the bots framework
- They handle edge cases (encoding, line endings, etc.) correctly
- No need to reimplement reliable functionality
- Contracts add vault-specific safety on top of proven tools
**Why link_view() over multiple navigation tools?**
- Single tool provides comprehensive structural overview
- Scope-aware truncation prevents context overflow
- Agent can request different starting points and depths as needed
- Simpler mental model than multiple specialized tools
**Why regex_search() over keyword_search()?**
- Strictly more powerful (keyword search is just a regex without special chars)
- Enables sophisticated queries (word boundaries, alternation, etc.)
- No additional complexity for simple searches
## Contract Validators
### Markdown Validation
```python
def is_valid_markdown(title: str, content: str) -> tuple[bool, str]:
    """Ensure content is valid markdown."""
    # Could use markdownlint or similar
    issues = check_markdown_syntax(content)
    if issues:
        return False, f"Markdown validation failed: {issues}"
    return True, ""
```
### Link Integrity
```python
def no_broken_links(title: str, content: str) -> tuple[bool, str]:
    """Ensure all wikilinks point to existing notes."""
    links = extract_wikilinks(content)
    broken = [link for link in links if not note_exists(link)]
    if broken:
        return False, f"Would create broken links: {broken}"
    return True, ""
def no_orphaned_notes(title: str, content: str) -> tuple[bool, str]:
    """Ensure note has at least one link in or out."""
    has_outgoing = bool(extract_wikilinks(content))
    has_incoming = bool(get_backlinks_for(title))
    if not (has_outgoing or has_incoming):
        return False, f"Note '{title}' would be orphaned (no links in/out)"
    return True, ""
```
### Frontmatter Validation
```python
def has_valid_frontmatter(title: str, content: str) -> tuple[bool, str]:
    """Ensure frontmatter is valid YAML."""
    frontmatter = extract_frontmatter(content)
    if frontmatter is None:
        return True, ""  # No frontmatter is okay
    try:
        yaml.safe_load(frontmatter)
        return True, ""
    except yaml.YAMLError as e:
        return False, f"Invalid YAML frontmatter: {e}"
```
### Path and Naming
```python
def title_is_valid(title: str, **kwargs) -> tuple[bool, str]:
    """Ensure title is valid for filesystem."""
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in title:
            return False, f"Title contains invalid character: {char}"
    return True, ""
def path_is_valid(folder: str, **kwargs) -> tuple[bool, str]:
    """Ensure folder path exists in vault."""
    if folder and not folder_exists(folder):
        return False, f"Folder does not exist: {folder}"
    return True, ""
```
## Plugin Configuration
### Settings
- **API Key**: Anthropic/OpenAI API key
- **Model**: Which LLM to use
- **Vault Invariants**: Enable/disable specific validators
- **Python Path**: Path to Python executable with bots installed
### User-Configurable Invariants
Future enhancement: Allow users to enable/disable specific validators:
```json
{
  "validators": {
    "markdown_lint": true,
    "no_orphans": false,
    "frontmatter_required": false,
    "no_broken_links": true
  }
}
```
## Communication Protocol
### Plugin Ã¢â€ â€™ Python
```json
{
  "type": "message",
  "content": "Create a note about quantum computing"
}
```
### Python Ã¢â€ â€™ Plugin
```json
{
  "type": "response",
  "content": "I'll create a note about quantum computing...",
  "tool_calls": [
    {
      "name": "create_note",
      "args": {"title": "Quantum Computing", "content": "..."}
    }
  ]
}
```
### Error Responses
```json
{
  "type": "error",
  "content": "Contract validation failed:\nPostconditions:\n  - Note would be orphaned"
}
```
## Implementation Phases
### Phase 1: Core Infrastructure
- [ ] Basic Obsidian plugin scaffold
- [ ] Python subprocess management
- [ ] Simple chat UI
- [ ] Basic IPC (stdin/stdout)
### Phase 2: Tool Implementation
- [ ] Implement core vault tools (create, update, delete, search)
- [ ] Implement contract validators
- [ ] Integrate with enhanced toolify
### Phase 3: UI Enhancement
- [ ] Tree navigation visualization
- [ ] Tool execution feedback
- [ ] Error display
- [ ] Settings panel
### Phase 4: Polish
- [ ] User-configurable validators
- [ ] Performance optimization
- [ ] Documentation
- [ ] Example workflows
## Technical Requirements
### Dependencies
- **Obsidian**: Plugin API
- **Python**: 3.10+ with bots framework installed
- **Node.js**: For plugin development
### File Structure
```
obsidian-vault-agent/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ manifest.json
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ main.ts                 # Plugin entry point
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ src/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ ui/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ ChatView.ts    # Chat interface
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ python/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ subprocess.ts  # Python process management
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ types.ts           # TypeScript types
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ python/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ vault_bot.py       # Bot initialization
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ vault_tools.py     # Obsidian tools
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ validators.py      # Contract validators
```
## Success Criteria
- [ ] Plugin installs and activates in Obsidian
- [ ] Chat interface appears and is usable
- [ ] Agent can create/update/delete notes
- [ ] Contract violations prevent invalid operations
- [ ] Error messages are clear and actionable
- [ ] Tree-based conversation navigation works
- [ ] No vault corruption under any circumstances
## Future Enhancements
- **Custom Validators**: User-defined contract functions
- **Batch Operations**: Apply changes to multiple notes
- **Undo/Redo**: Rollback agent changes
- **Workflow Templates**: Pre-built namshubs for common tasks
- **Graph View Integration**: Visualize agent's impact on vault structure
- **Conflict Resolution**: Handle concurrent edits gracefully
## Security Considerations
- **No Code Execution Tools**: The bot has NO tools for executing Python, shell commands, or arbitrary code. Only vault-specific tools (create_note, update_note, etc.)
- **Contract-Enforced Boundaries**: All vault operations are guarded by preconditions and postconditions that prevent invalid states
- **Filesystem Isolation**: Python process only has access to the vault directory, no system-wide operations
- **API Key Storage**: Secure storage in Obsidian settings (encrypted if possible)
- **Rate Limiting**: Prevent runaway tool execution loops
- **Audit Log**: Track all vault modifications by agent for transparency and debugging
- **Read-Only by Default**: Tools that modify the vault require explicit user confirmation (future enhancement)
- **Sandbox Python Process**: Limit filesystem access to vault directory
- **API Key Storage**: Secure storage in Obsidian settings
- **Rate Limiting**: Prevent runaway tool execution
- **Audit Log**: Track all vault modifications by agent
