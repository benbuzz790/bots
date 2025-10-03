# Changelog
All notable changes to this project will be documented in this file.
## [3.0.0] - 2025-10-03
### Major Release - 248 commits since v2.0.0
This is a significant release representing months of development, testing, and refinement.
### Highlights
- **Multi-Provider Support**: Full support for Anthropic Claude, OpenAI GPT, and Google Gemini
- **Enhanced Testing**: Comprehensive test suite with 97%+ pass rate across all providers
- **CLI Improvements**: Updated CLI with latest models and improved functional prompts
- **Tool Ecosystem**: Expanded tool library including web search, python_edit, and self-tools
- **CI/CD Stability**: Fixed encoding issues, improved workflow reliability
### Added (25+ new features)
- Google Gemini API integration
- MockBot testing infrastructure
- Web search tool with structured output
- Enhanced python_edit tool with comprehensive documentation
- Branch_self tool for parallel conversation exploration
- Functional prompts system (par_branch, par_branch_while, etc.)
- Tutorial and getting started guides
### Fixed (71+ bug fixes)
- CI/CD pipeline encoding (BOM) issues
- Test reliability across all providers
- Tool execution and result integration
- Function calling formats for all APIs
- Save/load functionality for all bot types
- Infinite loop prevention in tool calls
- CLI parameter handling and error messages
### Improved (24+ updates)
- Test coverage and stability
- Error handling and reporting
- Code formatting (Black 25.9.0)
- Documentation and guides
- Model support (Claude 4.5 Sonnet, GPT-4, Gemini 2.5)
### Technical Details
- 248 commits since v2.0.0
- Upgraded to Black 25.9.0 for code formatting
- Fixed actionlint workflow configuration
- Added comprehensive test matrix for all providers
- Improved tool serialization and deserialization
## [2.0.0] - Previous Release
Initial tagged release.