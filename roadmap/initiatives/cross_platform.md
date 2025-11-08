# Cross-Platform Support Initiative
**Status:** Not Started ❌  
**Last Updated:** November 8, 2025
## Overview
Enable full cross-platform compatibility for Windows, Linux, and macOS. Currently, the bots framework is Windows-centric with PowerShell-only terminal tools, limiting the addressable market to Windows users only.
## Related Items
- **Item 38:** Unix/Mac Compatibility - ❌ NOT STARTED
- **Item 39:** Multi-OS Testing Infrastructure - ❌ NOT STARTED
See also: [Phase 1: Foundation](../active/phase1_foundation.md#item-38)
## Current State
**Windows-Only Limitations:**
- Terminal tools use PowerShell exclusively (execute_powershell)
- CI/CD runs only on windows-latest
- No testing on Linux or macOS
- Unix/Mac users cannot use terminal execution features
**Impact:**
- Excludes Mac/Linux developers (significant market segment)
- Limits adoption in Unix-heavy environments
- No validation of cross-platform bugs
## Technical Approach
### Phase 1: Shell Abstraction Layer
**Goal:** Unified shell interface that routes to appropriate shell per OS
**Implementation:**
1. Detect OS using sys.platform or os.name
2. Create BashSession class (mirror of PowerShellSession)
3. Implement execute_shell(command) unified interface
4. Route to execute_powershell() on Windows, execute_bash() on Unix/Mac
**Files to Modify:**
- ots/tools/terminal_tools.py - Add bash support
- CLI help text - Change "execute powershell" to "execute shell commands"
### Phase 2: Unix Shell Support
**Goal:** Full bash/sh support for Unix/Mac systems
**Implementation:**
1. Create BashSession class with stateful execution
2. Handle bash-specific syntax and behavior
3. Test on Linux and macOS
4. Ensure feature parity with PowerShell version
**Challenges:**
- Different command syntax (PowerShell vs bash)
- Path handling (backslash vs forward slash)
- File encoding differences (UTF-8 BOM vs clean UTF-8)
- Line endings (CRLF vs LF)
- File permissions (chmod vs Windows ACLs)
### Phase 3: Multi-OS CI/CD
**Goal:** Test on Windows, Linux, and macOS with multiple Python versions
**Implementation:**
1. Update .github/workflows/pr-checks.yml with OS matrix:
   `yaml
   strategy:
     matrix:
       os: [ubuntu-latest, windows-latest, macos-latest]
       python-version: ['3.10', '3.11', '3.12']
   `
2. Add OS-specific test fixtures
3. Implement conditional test skipping for OS-specific features
4. Platform-specific mocking strategies
**Current CI/CD:**
- All jobs run on windows-latest only
- Python 3.12 only
- Heavy Windows-specific UTF-8 encoding configuration
### Phase 4: Cross-Platform Testing
**Goal:** Validate all features work across platforms
**Implementation:**
1. OS-specific test fixtures
2. Conditional test skipping (@pytest.mark.skipif)
3. OS detection in tests
4. Platform-specific mocking
## Challenges
### Technical Challenges
1. **Shell Differences:**
   - PowerShell: Get-ChildItem, Select-String, Out-File
   - Bash: ls, grep, >
   - Need abstraction or translation layer
2. **Path Handling:**
   - Windows: C:\Users\... (backslash)
   - Unix: /home/... (forward slash)
   - Python's pathlib helps but not complete solution
3. **File Encoding:**
   - Windows: UTF-8 with BOM common
   - Unix: Clean UTF-8 standard
   - Need consistent handling
4. **Terminal Behavior:**
   - Different escape sequences
   - Different environment variables
   - Different process spawning
### Testing Challenges
1. **CI/CD Complexity:**
   - 3 OS × 3 Python versions = 9 test matrix combinations
   - Longer CI/CD run times
   - More complex failure diagnosis
2. **Environment Differences:**
   - Different default tools available
   - Different file system behaviors
   - Different permission models
## Benefits
**Market Reach:**
- 3x addressable market (Windows + Mac + Linux)
- Better adoption in Unix-heavy environments (web dev, data science)
- Enterprise compatibility (many enterprises use Linux servers)
**Quality:**
- Catch OS-specific bugs before users encounter them
- More robust, production-ready codebase
- Better testing coverage
**Community:**
- Broader contributor base
- More diverse testing scenarios
- Better bug reports from varied environments
## Success Metrics
- ✅ Shell abstraction layer implemented
- ✅ Bash support complete with feature parity
- ✅ CI/CD matrix testing on 3 OS × 3 Python versions
- ✅ All tests pass on Windows, Linux, macOS
- ✅ Terminal tools work on all platforms
- ✅ Documentation updated for cross-platform usage
## Implementation Plan
### Week 1-2: Shell Abstraction
- Create BashSession class
- Implement execute_shell() unified interface
- Add OS detection logic
- Update CLI help text
### Week 3-4: Unix Shell Support
- Implement bash-specific features
- Handle path and encoding differences
- Test on Linux and macOS
- Fix platform-specific issues
### Week 5-6: CI/CD Updates
- Update workflow files with OS matrix
- Add OS-specific test fixtures
- Implement conditional test skipping
- Validate all tests pass on all platforms
### Week 7-8: Documentation & Polish
- Update all documentation for cross-platform
- Add platform-specific notes where needed
- Create troubleshooting guide
- Final testing and bug fixes
**Total Estimated Time:** 6-8 weeks
## Dependencies
- None (can start immediately)
- Recommended: Complete after Phase 1 foundation items
## Risks
**Risk 1: Platform-Specific Bugs**
- Mitigation: Comprehensive testing on all platforms
- Contingency: Document platform-specific workarounds
**Risk 2: CI/CD Complexity**
- Mitigation: Start with 2 OS (Windows + Linux), add macOS later
- Contingency: Use conditional CI/CD (only run full matrix on main branch)
**Risk 3: Maintenance Burden**
- Mitigation: Good abstraction layer reduces platform-specific code
- Contingency: Focus on most popular platforms first
## Next Steps
1. Create shell abstraction layer design document
2. Implement BashSession class
3. Add OS detection and routing logic
4. Update CI/CD with Linux testing
5. Test and iterate on Linux
6. Add macOS support
7. Full cross-platform validation
---
**Initiative Owner:** TBD  
**Priority:** HIGH (blocks significant user base)  
**Estimated Effort:** 6-8 weeks  
**Related Initiatives:** [Test Infrastructure](test_infrastructure.md)
