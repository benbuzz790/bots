import bots


def main():
    claude = bots.AnthropicBot()
    claude.set_system_message(_prompts.context)
    claude.add_tools(bots.tools.code_tools)
    response = claude.respond(_prompts.first_msg)
    print(response)
    claude.chat()


class _prompts:
    template_instructions = """
# Technical Specification Template Instructions
## Core Philosophy
This template is inseparable from its underlying design principles of KISS
(Keep It Simple, Stupid) and YAGNI (You Aren't Gonna Need It). Every section
you complete must be evaluated against these principles. The template is not
a checklist to fill out - it's a framework for documenting necessary
complexity while actively resisting unnecessary complexity.
## Before You Begin
Before adding any item to your specification, ask yourself:
1. "Do we need this NOW?" (YAGNI)
2. "Is this the simplest possible solution?" (KISS)
3. "What would happen if we removed this?"
If you can't strongly justify an item's immediate necessity, exclude it.
## Section-by-Section Guidelines
### Problem Statement
- Focus only on the current, proven problem
- Avoid speculating about future use cases
- Include only background information essential for understanding the core
  problem
### Design Principles
- KISS and YAGNI are non-negotiable
- Additional principles must earn their place through demonstrated necessity
- Each added principle increases complexity - be extremely selective
### Technical Requirements
- Include only requirements that solve the current problem
- Future requirements belong in "Future Considerations"
- Every requirement should have a clear, immediate purpose
### System Architecture
- Start with the simplest possible architecture
- Each component must justify its existence
- Defer optimization-focused components to "Future Considerations"
### Performance Requirements
- Include only if performance is a current, proven bottleneck
- Prefer "none" over speculative requirements
- Document only measurable, necessary criteria
### Monitoring and Logging
- Start with minimal or no monitoring
- Add only when operational need is demonstrated
- Prefer "none" over speculative requirements
### Testing Requirements
- Focus on critical path testing
- Avoid premature test coverage goals
- Include only tests that verify current functionality
### Security Requirements
- Include only security measures protecting against current, known risks
- Defer advanced security features unless immediately necessary
- Start with fundamental security practices
### Development Guidelines
- Keep guidelines minimal and focused
- Include only what's needed for current development
- Avoid premature optimization rules
### Future Considerations
- Use this section aggressively
- Document features you actively decided not to implement
- Include rationale for deferment when helpful
### Definition of Done
- Include only criteria essential for current functionality
- Each criterion should be testable
- Avoid future-facing completion criteria
- A full system demo is ALWAYS a requirement.
## Common Pitfalls to Avoid
1. **Requirements Creep**
   - Adding "nice to have" features
   - Including speculative requirements
   - Over-engineering for future scenarios
2. **Excessive Detail**
   - Adding documentation requirements beyond immediate needs
   - Over-specifying implementation details
   - Including non-essential monitoring or logging
3. **Premature Optimization**
   - Adding performance requirements without evidence
   - Including caching layers "just in case"
   - Over-architecting for scalability
4. **Security Theater**
   - Adding security features without threat models
   - Including complex authentication too early
   - Over-specifying security requirements
## Final Checklist
Before finalizing your specification, verify:
1. Every item included solves a current problem
2. No speculative features made it through
3. The architecture is as simple as possible
4. You've actively moved non-essential items to "Future Considerations"
5. You can justify every single requirement with current needs
Remember: The best technical specification is often the shortest one that
fully solves the current problem. When in doubt, leave it out.
"""
    template = """
# [Project Name] Technical Specification
Version [X.Y]
## 1. Problem Statement
### 1.1 Background
[Describe the problem being solved and its context. Include:
- Current pain points
- Why this solution is needed
- Who will benefit from this solution]
### 1.2 Design Principles
0. "LLM - implementable". These principles are designed to keep this project
specification implementable by LLMs that exist as of 18Dec2024. LLMs tend to
both add unecessary complexity AND fail on complex projects, the combination
of which means llms need some design principles to keep them on the right
track.
1. KISS: Keep solutions simple and focused
2. YAGNI: Only implement proven necessary features
3. SOLID: Design modular, maintainable components
4. flat: All program files shall be in a single directory
5. [Additional project-specific principles]
## 2. Technical Requirements
### 2.1 Input Requirements
- [Supported protocols/formats]
- [Processing limitations]
- [Required format specifications]
- [Required headers/metadata]
### 2.2 Output Format
```
[Provide example of expected output format]
```
## 3. System Architecture
### 3.1 Core Components
```
[Component Flow Diagram]
```
### 3.2 Component Specifications
#### 3.2.1 [Component Name]
- Framework: [Selected framework/technology]
- [Component-specific details]
## 4. Performance Requirements
[Define specific, measurable performance criteria or explicitly state if none]
## 5. Monitoring and Logging
[Define monitoring and logging requirements or explicitly state if none]
## 6. Testing Requirements
### 6.1 Core Testing
- [Required test types]
- [Test coverage expectations]
- [Acceptance criteria]
## 7. Security Requirements
### 7.1 Authentication
- [Authentication methods]
- [Security protocols]
### 7.2 Data Protection
- [Data handling requirements]
- [Security measures]
## 8. Development Guidelines
### 8.1 Code Quality
- [Coding standards]
- [Best practices]
- [Design principles to follow]
### 8.2 Documentation
- [Required documentation]
- [Documentation standards]
## 9. Future Considerations
Features intentionally deferred (DO NOT IMPLEMENT):
1. [Feature 1]
2. [Feature 2]
[Add explanation if needed for why these are deferred]
## 10. Definition of Done
[Project] is complete when:
1. [Criterion 1]
2. [Criterion 2]
3. [Criterion 3]
4. A full system demonstration
## 11. Special Instructions
[Any specific implementation notes or requirements]
## 12. Version History
- Version: [Current version number]
- Date: [Date]
- Previous: [Previous version info]
- Approved By: [Name/Role]
"""
    context = """
You are a project specification making bot. Your job is
to interview the user until you have a clear view of the
project at hand. Then you will fill out a template and save
it as a .md file."""
    first_msg = f"""
Here is the template and instructions for filling it in:
---
{template}
---
{template_instructions}
---
Your next message will be from the user. Begin the interview
process after that message. Don't save the template, just
the filled in version at the end of the interview.
"""


if __name__ == "__main__":
    main()
