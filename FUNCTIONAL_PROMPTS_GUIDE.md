# Functional Prompts Guide
## Overview
Functional prompts are composable functions that orchestrate bot interactions in structured patterns. They enable sophisticated reasoning approaches while maintaining clear structure and reproducibility. Think of them as higher-level building blocks for complex AI workflows.
## Core Concepts
### What is a Functional Prompt?
A functional prompt is a function that sends a bot a prompt or sequence of prompts in a particular way. Unlike simple bot.respond() calls, functional prompts provide:
- **Structure**: Organized patterns for complex interactions
- **Composability**: Ability to combine patterns for sophisticated workflows
- **Reproducibility**: Consistent behavior across different scenarios
- **Context Management**: Intelligent handling of conversation history
### Common Parameters
Most functional prompts share these parameters:
- ot (Bot): The bot instance to use
- prompts (List[str]): List of prompts to process
- callback (Optional[Callable]): Function called after each response
- stop_condition (Condition): Function determining when to stop iteration
### Return Values
Functional prompts typically return:
- Tuple[Response, ResponseNode]: For single responses
- Tuple[List[Response], List[ResponseNode]]: For multiple responses
## Sequential Processing Patterns
### single_prompt()
The simplest functional prompt - executes one prompt and captures both response and conversation state.
**Use when:**
- You need the simplest possible bot interaction
- You want to capture both response and conversation state
- Building custom interaction patterns
`python
import bots.flows.functional_prompts as fp
# Basic usage
response, node = fp.single_prompt(bot, "What is the time complexity of quicksort?")
print(response)
# Access conversation context
response, node = fp.single_prompt(bot, "Analyze this code")
print(node.parent.content)  # See previous context
`
### chain()
Execute prompts sequentially, building context progressively.
**Use when:**
- Guiding a bot through structured steps
- Building complex reasoning through progressive stages
- Maintaining context between related prompts
`python
# Code analysis workflow
responses, nodes = fp.chain(bot, [
    "First, read and understand the codebase structure",
    "Now, identify potential security vulnerabilities", 
    "Finally, propose specific fixes for each issue"
])
# Each step builds on the previous context
for i, response in enumerate(responses):
    print(f"Step {i+1}: {response[:100]}...")
`
### prompt_while()
Repeatedly engage a bot until completion criteria are met.
**Use when:**
- Having a bot work iteratively on a task
- Continuing processing until specific criteria are met
- Handling tasks with unknown completion time
`python
# Debug code until no more tools are used
responses, nodes = fp.prompt_while(
    bot,
    "Debug this code. Fix all errors you find.",
    continue_prompt="Continue debugging. Any more issues?",
    stop_condition=fp.conditions.tool_not_used
)
# Document improvement with explicit completion
responses, nodes = fp.prompt_while(
    bot,
    "Improve this documentation. Say DONE when perfect.",
    continue_prompt="What else can be improved?",
    stop_condition=fp.conditions.said_DONE
)
`
### chain_while()
Execute ordered steps where each step can iterate until complete.
**Use when:**
- Guiding a bot through ordered steps
- Allowing each step to take multiple iterations
- Ensuring completion criteria for each step
`python
# Multi-stage code improvement
responses, nodes = fp.chain_while(
    bot,
    [
        "Analyze the code and list all issues",
        "Fix each identified issue", 
        "Add comprehensive tests",
        "Update documentation"
    ],
    stop_condition=fp.conditions.said_DONE,
    continue_prompt="Continue until this step is complete"
)
`
## Parallel Exploration Patterns
### branch()
Create multiple independent conversation paths from the current state.
**Use when:**
- Exploring multiple perspectives simultaneously
- Analyzing different aspects independently
- Comparing approaches without cross-influence
`python
# Multi-perspective code analysis
responses, nodes = fp.branch(bot, [
    "Analyze this code from a security perspective",
    "Analyze this code from a performance perspective", 
    "Analyze this code from a maintainability perspective",
    "Analyze this code from a scalability perspective"
])
# Each branch is independent
for i, response in enumerate(responses):
    print(f"Perspective {i+1}: {response}")
`
### branch_while()
Create parallel branches with independent iteration control.
**Use when:**
- Exploring multiple iterative processes independently
- Each process may require different completion times
`python
# Optimize multiple functions independently
responses, nodes = fp.branch_while(
    bot,
    [
        "Optimize sort() function until O(n log n) average case",
        "Improve search() until O(log n) worst case",
        "Reduce memory usage in cache() to O(n)"
    ],
    stop_condition=fp.conditions.said_DONE,
    continue_prompt="Continue optimization"
)
`
### par_branch()
Parallel processing version of branch() using multiple CPU cores.
**Use when:**
- Processing multiple prompts simultaneously
- Leveraging multiple CPU cores for faster execution
`python
# Fast parallel analysis
responses, nodes = fp.par_branch(bot, [
    "Analyze code structure and architecture",
    "Review documentation completeness",
    "Check test coverage and quality", 
    "Audit dependencies for security"
])
`
### par_branch_while()
Parallel processing version of branch_while().
**Use when:**
- Multiple iterative processes need to run simultaneously
- Performance is critical for long-running tasks
`python
# Parallel optimization with iteration
responses, nodes = fp.par_branch_while(
    bot,
    [
        "Optimize database queries until response time < 100ms",
        "Reduce API latency until < 50ms",
        "Improve cache hit rate until > 95%"
    ],
    stop_condition=fp.conditions.said_DONE,
    continue_prompt="Continue optimization"
)
`
## Advanced Reasoning Patterns
### tree_of_thought()
Implement tree-of-thought reasoning: branch, explore, then synthesize.
**Use when:**
- Breaking down complex problems into multiple perspectives
- Exploring different aspects in parallel then combining insights
- Making decisions requiring multiple factors
`python
# Define a synthesis function
def combine_analysis(responses, nodes):
    insights = "\n".join(f"- {r}" for r in responses)
    return f"Technical Analysis Summary:\n{insights}", nodes[0]
# Complex technical decision
response, node = fp.tree_of_thought(
    bot,
    [
        "Analyze performance implications of this architecture",
        "Consider security aspects and potential vulnerabilities", 
        "Evaluate maintenance and operational complexity",
        "Assess scalability and future growth requirements"
    ],
    combine_analysis
)
`
### prompt_for()
Generate and process prompts dynamically from data.
**Use when:**
- Processing collections where each item needs custom prompts
- Data-driven conversation flows
`python
# Define prompt generator
def review_prompt(file_path):
    return f"Review {file_path} for security issues and best practices"
# Process multiple files
files = ["auth.py", "api.py", "database.py"]
responses, nodes = fp.prompt_for(
    bot,
    files,
    review_prompt,
    should_branch=True  # Process in parallel
)
`
### par_dispatch()
Execute functional prompts across multiple bots in parallel.
**Use when:**
- Comparing different LLM providers
- Testing multiple bot configurations
- Benchmarking performance
`python
# Compare different models
results = fp.par_dispatch(
    [anthropic_bot, openai_bot, claude_bot],
    fp.chain,
    prompts=[
        "Analyze the problem space",
        "Propose three solutions", 
        "Recommend the best approach"
    ]
)
# Compare results
for bot, (response, node) in zip([anthropic_bot, openai_bot, claude_bot], results):
    print(f"{bot.__class__.__name__}: {response[:100]}...")
`
## Broadcasting Patterns
### broadcast_to_leaves()
Send prompts to all conversation endpoints in parallel.
**Use when:**
- Applying operations to all conversation branches
- Gathering results from multiple conversation paths
`python
# Debug all conversation branches
responses, nodes = fp.broadcast_to_leaves(
    bot,
    "Review and fix any issues in this conversation branch",
    skip=["draft", "incomplete"],  # Skip certain labels
    continue_prompt="Continue fixing",
    stop_condition=fp.conditions.tool_not_used
)
`
### broadcast_fp()
Execute functional prompts on all leaf nodes.
**Use when:**
- Applying complex patterns to all conversation endpoints
- Scaling sophisticated operations across conversation trees
`python
# Apply tree-of-thought to all leaves
responses, nodes = fp.broadcast_fp(
    bot,
    fp.tree_of_thought,
    prompts=["Consider approach A", "Consider approach B"],
    recombinator_function=my_recombinator,
    skip=["incomplete"]
)
`
## Stop Conditions
The conditions class provides predefined functions for controlling iteration:
`python
# Stop when bot stops using tools
fp.conditions.tool_not_used
# Stop when bot says "DONE"
fp.conditions.said_DONE
# Stop when bot says "READY"  
fp.conditions.said_READY
# Stop after 5 iterations
fp.conditions.five_iterations
# Stop on errors
fp.conditions.error_in_response
# Custom condition
def custom_condition(bot):
    return "COMPLETE" in bot.conversation.content
responses, nodes = fp.prompt_while(
    bot,
    "Work on this task until COMPLETE",
    stop_condition=custom_condition
)
`
## Chaining Functional Prompts
Functional prompts are composable - you can chain them together for sophisticated workflows:
`python
# Stage 1: Parallel analysis
analysis_responses, analysis_nodes = fp.par_branch(bot, [
    "Analyze code structure",
    "Review security aspects", 
    "Check performance characteristics"
])
# Stage 2: Synthesize findings
def combine_findings(responses, nodes):
    combined = "\n\n".join(f"**{i+1}.** {r}" for i, r in enumerate(responses))
    return f"Analysis Summary:\n{combined}", nodes[0]
synthesis_response, synthesis_node = fp.tree_of_thought(
    bot,
    [
        "Prioritize the most critical issues",
        "Recommend implementation order",
        "Estimate effort and timeline"
    ],
    combine_findings
)
# Stage 3: Iterative implementation
implementation_responses, implementation_nodes = fp.chain_while(
    bot,
    [
        "Implement the highest priority fixes",
        "Test the changes thoroughly",
        "Update documentation"
    ],
    stop_condition=fp.conditions.said_DONE
)
`
## Callbacks and Monitoring
Use callbacks to monitor progress and implement custom logic:
`python
def progress_callback(responses, nodes):
    print(f"Completed {len(responses)} steps")
    # Log to file, update UI, etc.
def error_callback(responses, nodes):
    if any("error" in r.lower() for r in responses if r):
        print("Error detected, implementing fallback...")
# Use with any functional prompt
responses, nodes = fp.chain(
    bot,
    ["Step 1", "Step 2", "Step 3"],
    callback=progress_callback
)
`
## Best Practices
### 1. Choose the Right Pattern
- **Sequential tasks**: Use chain() or chain_while()
- **Independent exploration**: Use ranch() or par_branch()
- **Complex reasoning**: Use 	ree_of_thought()
- **Iterative refinement**: Use prompt_while() or *_while() variants
### 2. Design Effective Prompts
`python
# Good: Clear, specific, actionable
prompts = [
    "Read the main.py file and understand its structure",
    "Identify any security vulnerabilities in the authentication logic",
    "Propose specific code changes to fix each vulnerability"
]
# Poor: Vague, overlapping, unclear
prompts = [
    "Look at the code",
    "Find problems", 
    "Make it better"
]
`
### 3. Use Appropriate Stop Conditions
`python
# For tool-based tasks
stop_condition=fp.conditions.tool_not_used
# For explicit completion
stop_condition=fp.conditions.said_DONE
# For custom criteria
def quality_check(bot):
    return "high quality" in bot.conversation.content.lower()
`
### 4. Handle Errors Gracefully
`python
def safe_recombinator(responses, nodes):
    try:
        # Your synthesis logic
        return synthesize_responses(responses), nodes[0]
    except Exception as e:
        return f"Synthesis failed: {e}", nodes[0]
`
### 5. Optimize Performance
`python
# Use parallel versions for independent tasks
responses, nodes = fp.par_branch(bot, prompts)  # Instead of branch()
# Use broadcasting for tree-wide operations
responses, nodes = fp.broadcast_fp(bot, fp.single_prompt, prompt="Review this")
`
## Common Patterns and Recipes
### Code Review Workflow
`python
# Multi-stage code review
def code_review_workflow(bot, files):
    # Stage 1: Individual file analysis
    file_analyses, _ = fp.prompt_for(
        bot, files,
        lambda f: f"Thoroughly review {f} for issues",
        should_branch=True
    )
    # Stage 2: Cross-file analysis
    integration_response, _ = fp.single_prompt(
        bot, "Analyze how these files work together and identify integration issues"
    )
    # Stage 3: Prioritized recommendations
    final_response, _ = fp.chain(bot, [
        "Prioritize all identified issues by severity",
        "Create an implementation plan",
        "Estimate effort for each fix"
    ])
    return final_response
`
### Research and Analysis
`python
def research_workflow(bot, topic):
    # Parallel research from different angles
    research_responses, _ = fp.par_branch(bot, [
        f"Research {topic} from a technical perspective",
        f"Research {topic} from a business perspective", 
        f"Research {topic} from a user perspective"
    ])
    # Synthesize findings
    def combine_research(responses, nodes):
        sections = ["Technical", "Business", "User"]
        combined = "\n\n".join(
            f"## {section} Perspective\n{response}" 
            for section, response in zip(sections, responses)
        )
        return f"# {topic} Research Report\n\n{combined}", nodes[0]
    return fp.tree_of_thought(
        bot,
        [
            "Identify key themes across all perspectives",
            "Highlight potential conflicts or synergies",
            "Recommend next steps based on findings"
        ],
        combine_research
    )
`
### Iterative Development
`python
def iterative_development(bot, requirements):
    return fp.chain_while(bot, [
        f"Implement initial version based on: {requirements}",
        "Test the implementation and identify issues",
        "Refactor and improve based on test results",
        "Add comprehensive error handling",
        "Optimize performance and add documentation"
    ], stop_condition=fp.conditions.said_DONE)
`
This guide provides a comprehensive foundation for using functional prompts effectively. Experiment with different patterns and combinations to build sophisticated AI workflows tailored to your specific needs.
