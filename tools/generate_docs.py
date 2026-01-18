"""
Documentation Generation Script for Bots Project

This script generates comprehensive documentation for the bots project by leveraging
the github-docs-app documentation tools locally. It scans the bots project structure,
analyzes Python files, generates docstrings, and creates professional module documentation.

Usage:
    python tools/generate_docs.py [options]

Options:
    --modules <module1,module2>  Generate docs for specific modules only
    --output <dir>               Output directory (default: docs/modules)
    --format <style>             Documentation style (default: github-docs-app)
    --dry-run                    Show what would be generated without writing files
    --verbose                    Enable verbose logging

Examples:
    # Generate docs for all modules
    python tools/generate_docs.py

    # Generate docs for specific modules
    python tools/generate_docs.py --modules foundation,tools

    # Dry run to preview changes
    python tools/generate_docs.py --dry-run --verbose
"""

import argparse
import ast
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add github-docs-app to path for importing documentation tools
GITHUB_DOCS_APP_PATH = Path(__file__).parent.parent.parent / "github-docs-app"
if GITHUB_DOCS_APP_PATH.exists():
    sys.path.insert(0, str(GITHUB_DOCS_APP_PATH / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a module to document."""

    name: str
    path: Path
    description: str
    python_files: List[Path]
    submodules: List[str]
    priority: int = 5  # 1-10, higher = more important


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation."""

    bots_root: Path
    github_docs_app_root: Path
    output_dir: Path
    modules_to_document: Optional[List[str]] = None
    style: str = "github-docs-app"
    dry_run: bool = False
    verbose: bool = False


class BotsProjectScanner:
    """Scans the bots project to identify modules and files to document."""

    def __init__(self, bots_root: Path):
        """
        Initialize the scanner.

        Args:
            bots_root: Root directory of the bots project
        """
        self.bots_root = bots_root
        self.bots_package = bots_root / "bots"

    def scan_project(self) -> List[ModuleInfo]:
        """
        Scan the bots project and identify all modules to document.

        Returns:
            List of ModuleInfo objects for each module
        """
        modules = []

        # Define core modules to document
        module_definitions = {
            "foundation": {"description": "Core bot implementations and model registry", "priority": 10},
            "tools": {"description": "Bot tools for code editing, execution, and terminal operations", "priority": 9},
            "flows": {"description": "Functional prompts and recombination strategies", "priority": 8},
            "dev": {"description": "Development tools, CLI, and bot session management", "priority": 7},
            "observability": {"description": "Tracing, metrics, and cost tracking", "priority": 6},
            "namshubs": {"description": "Specialized bot workflows and automation", "priority": 6},
            "utils": {"description": "Utility functions and helpers", "priority": 5},
            "testing": {"description": "Testing utilities and mock implementations", "priority": 4},
        }

        for module_name, info in module_definitions.items():
            module_path = self.bots_package / module_name
            if module_path.exists() and module_path.is_dir():
                python_files = self._find_python_files(module_path)
                submodules = self._find_submodules(module_path)

                modules.append(
                    ModuleInfo(
                        name=module_name,
                        path=module_path,
                        description=info["description"],
                        python_files=python_files,
                        submodules=submodules,
                        priority=info["priority"],
                    )
                )
                logger.info(f"Found module: {module_name} ({len(python_files)} files)")

        # Sort by priority (highest first)
        modules.sort(key=lambda m: m.priority, reverse=True)
        return modules

    def _find_python_files(self, module_path: Path) -> List[Path]:
        """
        Find all Python files in a module directory.

        Args:
            module_path: Path to the module directory

        Returns:
            List of Python file paths
        """
        python_files = []
        for py_file in module_path.rglob("*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" not in str(py_file) and not py_file.name.startswith("test_"):
                python_files.append(py_file)
        return sorted(python_files)

    def _find_submodules(self, module_path: Path) -> List[str]:
        """
        Find submodules within a module directory.

        Args:
            module_path: Path to the module directory

        Returns:
            List of submodule names
        """
        submodules = []
        for item in module_path.iterdir():
            if item.is_dir() and not item.name.startswith("_") and (item / "__init__.py").exists():
                submodules.append(item.name)
        return sorted(submodules)


class DocumentationGenerator:
    """Generates documentation for bots modules using github-docs-app tools."""

    def __init__(self, config: DocumentationConfig):
        """
        Initialize the documentation generator.

        Args:
            config: Documentation configuration
        """
        self.config = config
        self.parser = None
        self.docstring_generator = None
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize documentation tools from github-docs-app."""
        try:
            # Add github-docs-app src to path
            github_docs_src = self.config.github_docs_app_root / "src"
            if str(github_docs_src) not in sys.path:
                sys.path.insert(0, str(github_docs_src))

            # Import github-docs-app tools
            from docs_bot.docstring_generator import DocstringGenerator
            from documentation_analyzer.parsers.python_parser import PythonParser

            self.parser = PythonParser(repo_path=str(self.config.bots_root))
            self.docstring_generator = DocstringGenerator(model="claude-sonnet-4-20250514")
            logger.info("✅ Documentation tools initialized successfully")

        except ImportError as e:
            logger.warning(f"⚠️  Could not import github-docs-app tools: {e}")
            logger.warning("   Falling back to basic documentation generation")
            self.parser = None
            self.docstring_generator = None

    def generate_module_documentation(self, module: ModuleInfo) -> str:
        """
        Generate comprehensive documentation for a module.

        Args:
            module: ModuleInfo object containing module details

        Returns:
            Markdown documentation string
        """
        logger.info(f"📝 Generating documentation for module: {module.name}")

        # Build documentation structure
        doc_parts = []

        # Header
        doc_parts.append(f"# {module.name.title()} Module")
        doc_parts.append(f"\n**Module**: `bots/{module.name}/`")
        doc_parts.append("**Version**: 3.0.0\n")

        # Overview
        doc_parts.append("## Overview\n")
        doc_parts.append(f"{module.description}\n")

        # Architecture
        doc_parts.append("## Architecture\n")
        doc_parts.append("```")
        doc_parts.append(f"{module.name}/")
        for py_file in module.python_files[:10]:  # Show first 10 files
            rel_path = py_file.relative_to(module.path)
            indent = "    " * (len(rel_path.parts) - 1)
            doc_parts.append(f"{indent}├── {rel_path.name}")
        if len(module.python_files) > 10:
            doc_parts.append(f"    └── ... ({len(module.python_files) - 10} more files)")
        doc_parts.append("```\n")

        # Key Components
        doc_parts.append("## Key Components\n")
        doc_parts.append(self._generate_components_section(module))

        # Usage Examples
        doc_parts.append("\n## Usage Examples\n")
        doc_parts.append(self._generate_usage_examples(module))

        # API Reference
        doc_parts.append("\n## API Reference\n")
        doc_parts.append(self._generate_api_reference(module))

        return "\n".join(doc_parts)

    def _generate_components_section(self, module: ModuleInfo) -> str:
        """Generate the key components section."""
        components = []

        # Analyze main files in the module
        for py_file in module.python_files[:5]:  # Top 5 files
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the file to find classes and functions
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            components.append(f"### {node.name}\n")
                            components.append(f"{docstring.split(chr(10))[0]}\n")
                            break  # One class per file for brevity

            except Exception as e:
                logger.warning(f"⚠️  Could not parse {py_file.name}: {e}")

        return "\n".join(components) if components else "*Documentation in progress*\n"

    def _generate_usage_examples(self, module: ModuleInfo) -> str:
        """Generate usage examples section."""
        examples = []

        # Module-specific examples
        if module.name == "foundation":
            examples.append("```python")
            examples.append("from bots.foundation import ClaudeBot")
            examples.append("")
            examples.append("# Create a bot instance")
            examples.append('bot = ClaudeBot(model="claude-sonnet-4-20250514")')
            examples.append("")
            examples.append("# Send a message")
            examples.append('response = bot("What is the capital of France?")')
            examples.append("print(response)")
            examples.append("```")

        elif module.name == "tools":
            examples.append("```python")
            examples.append("from bots.foundation import ClaudeBot")
            examples.append("from bots.tools import python_view, python_edit")
            examples.append("")
            examples.append("# Create a bot with tools")
            examples.append("bot = ClaudeBot(tools=[python_view, python_edit])")
            examples.append("")
            examples.append("# Bot can now view and edit Python files")
            examples.append('response = bot("Show me the main function in app.py")')
            examples.append("```")

        else:
            examples.append("```python")
            examples.append(f"from bots.{module.name} import *")
            examples.append("")
            examples.append("# Usage examples coming soon")
            examples.append("```")

        return "\n".join(examples)

    def _generate_api_reference(self, module: ModuleInfo) -> str:
        """Generate API reference section."""
        api_docs = []

        api_docs.append("### Classes and Functions\n")
        api_docs.append("| Name | Type | Description |")
        api_docs.append("|------|------|-------------|")

        # Scan files for classes and functions
        for py_file in module.python_files[:10]:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        if not node.name.startswith("_"):  # Skip private
                            docstring = ast.get_docstring(node) or "No description"
                            desc = docstring.split("\n")[0][:60]
                            node_type = "Class" if isinstance(node, ast.ClassDef) else "Function"
                            api_docs.append(f"| `{node.name}` | {node_type} | {desc} |")

            except Exception as e:
                logger.warning(f"⚠️  Could not parse {py_file.name}: {e}")

        return "\n".join(api_docs)

    def write_documentation(self, module: ModuleInfo, content: str):
        """
        Write documentation to file.

        Args:
            module: ModuleInfo object
            content: Documentation content
        """
        output_file = self.config.output_dir / f"{module.name}.md"

        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would write to: {output_file}")
            logger.info(f"[DRY RUN] Content preview:\n{content[:500]}...")
            return

        # Create output directory if needed
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Written: {output_file}")


def main():
    """Main entry point for the documentation generation script."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive documentation for the bots project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--modules", type=str, help="Comma-separated list of modules to document (default: all)")
    parser.add_argument(
        "--output", type=str, default="docs/modules", help="Output directory for documentation (default: docs/modules)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="github-docs-app",
        choices=["github-docs-app", "simple"],
        help="Documentation style (default: github-docs-app)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine paths
    bots_root = Path(__file__).parent.parent
    github_docs_app_root = bots_root.parent / "github-docs-app"
    output_dir = bots_root / args.output

    # Create configuration
    config = DocumentationConfig(
        bots_root=bots_root,
        github_docs_app_root=github_docs_app_root,
        output_dir=output_dir,
        modules_to_document=args.modules.split(",") if args.modules else None,
        style=args.format,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    logger.info("=" * 80)
    logger.info("Bots Project Documentation Generator")
    logger.info("=" * 80)
    logger.info(f"Bots root: {config.bots_root}")
    logger.info(f"GitHub docs app: {config.github_docs_app_root}")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info(f"Dry run: {config.dry_run}")
    logger.info("=" * 80)

    # Scan project
    scanner = BotsProjectScanner(config.bots_root)
    modules = scanner.scan_project()

    # Filter modules if specified
    if config.modules_to_document:
        modules = [m for m in modules if m.name in config.modules_to_document]

    logger.info(f"\n📚 Found {len(modules)} modules to document:")
    for module in modules:
        logger.info(f"   • {module.name} ({len(module.python_files)} files, priority: {module.priority})")

    # Generate documentation
    generator = DocumentationGenerator(config)

    logger.info("\n🚀 Starting documentation generation...\n")

    for i, module in enumerate(modules, 1):
        logger.info(f"[{i}/{len(modules)}] Processing: {module.name}")
        try:
            content = generator.generate_module_documentation(module)
            generator.write_documentation(module, content)
        except Exception as e:
            logger.error(f"❌ Failed to generate docs for {module.name}: {e}")
            if config.verbose:
                import traceback

                traceback.print_exc()

    logger.info("\n" + "=" * 80)
    logger.info("✅ Documentation generation complete!")
    logger.info(f"📁 Output directory: {config.output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
