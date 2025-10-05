# Project Ideas and Future Development Notes
**Date**: 2025-01-XX
**Project**: bots - Agentic Programming Framework

## Overview
This document tracks development ideas, feature requests, and architectural improvements for the bots project. Each item includes context, rationale, and implementation considerations.


---

## Development Philosophy & Strategic Direction

### The Core Principle: Standards Over Frameworks

The bots project has reached a critical inflection point. After successfully implementing multi-provider support and achieving a robust 97%+ test pass rate, we're now positioned to make a fundamental choice about our future direction. The landscape of AI development tools has matured significantly, and a clear pattern has emerged: **universal standards are winning over proprietary frameworks**.

This isn't about chasing trendsÃ¢â‚¬â€it's about recognizing that the industry has spoken. Model Context Protocol (MCP) is projected to reach 90% organizational adoption by the end of 2025. Microsoft, OpenAI, and Google have all committed to it. OpenTelemetry has become the de facto standard for observability. These aren't just popular tools; they're becoming the *lingua franca* of AI development.

### Why Standards Matter

When we initially considered integrating with LangChain, the complexity was overwhelming. Layers of abstraction, steep learning curves, and constant API changes made it feel like we were building on shifting sand. But MCP? It's a protocolÃ¢â‚¬â€simple, clear, and purpose-built for one thing: connecting AI models to tools and data. It's the USB-C of AI, and just like USB-C, its value comes from universal adoption, not feature richness.

This realization shapes our entire strategy: **prioritize interoperability over features, standards over frameworks, simplicity over sophistication**.

### The Three Pillars of Our Strategy

#### 1. **Embrace Universal Standards**

We're not building in isolation. The bots project should be a *citizen* of the broader AI ecosystem, not an island. This means:

- **MCP Integration**: Our tools should be accessible to anyone using Claude Desktop, Cursor, or any MCP-compatible client. Conversely, our bots should be able to use the hundreds of MCP servers already published. This isn't just about compatibilityÃ¢â‚¬â€it's about network effects. Every MCP server we can connect to multiplies our capabilities without writing a single line of integration code.

- **OpenTelemetry for Observability**: Print statements scattered through code are a symptom of development without proper instrumentation. OpenTelemetry isn't just about removing print statementsÃ¢â‚¬â€it's about building production-ready software that can be monitored, debugged, and optimized in real-world deployments. When something goes wrong at 3 AM, structured traces and metrics are the difference between hours of debugging and minutes.

- **LiteLLM for Provider Expansion**: Rather than manually implementing each new LLM provider, we leverage LiteLLM's unified interface to support 100+ providers instantly. This isn't lazinessÃ¢â‚¬â€it's recognizing that provider APIs are commoditizing, and our value lies elsewhere.

#### 2. **Maintain Our Core Differentiators**

Standards handle connectivity and interoperability, but they don't replace our unique capabilities:

- **Conversation Trees**: The ability to branch, explore multiple paths, and navigate conversation history as a tree structure remains unique. Most frameworks treat conversations as linear chains. We treat them as explorable spaces.

- **Functional Prompts**: Composable patterns like `chain`, `branch`, `prompt_while`, and `par_branch_while` provide structured reasoning that goes beyond simple prompt-response cycles. These aren't just convenience functionsÃ¢â‚¬â€they're a programming model for AI interactions.

- **Tool Excellence**: Our tools like `python_edit` (scope-aware code editing) and `branch_self` (recursive self-branching) represent genuine innovation. By exposing them via MCP, we share this innovation with the broader community while maintaining our implementation advantages.

- **Self-Context Management**: The upcoming expansion of self-tools (delete_stale_context, fork_from_node, etc.) gives bots unprecedented control over their own conversation history. This is agentic AI in the truest senseÃ¢â‚¬â€agents that can manage their own context.

#### 3. **Build for Production, Not Just Prototypes**

The shift from "works on my machine" to "works in production" requires fundamental changes:

- **Observability First**: OpenTelemetry integration isn't optionalÃ¢â‚¬â€it's foundational. Every API call, every tool execution, every decision point should be traceable. This enables debugging, optimization, cost tracking, and compliance.

- **Quality Guardrails**: Branch protection, required CI/CD checks, and automated code review (CodeRabbit) aren't bureaucracyÃ¢â‚¬â€they're insurance against regressions. The coveted green checkmark isn't a badge of honor; it's a minimum bar for production readiness.

- **Test Organization**: Moving from "we have tests" to "we have a test strategy" means organizing tests by speed (unit/integration/e2e), using proper fixtures, and fixing parallelism issues. Fast feedback loops enable rapid iteration without sacrificing quality.

- **Configuration Over Code**: The shift to configuration-driven architecture (base.py using config files, plugin systems, etc.) makes the system adaptable without code changes. This is essential for deployment in diverse environments.

### The Practical Implications

This philosophy translates into concrete priorities:

**Phase 1 focuses on standards and foundations** because these are force multipliers. MCP integration doesn't just add featuresÃ¢â‚¬â€it adds an entire ecosystem. OpenTelemetry doesn't just remove print statementsÃ¢â‚¬â€it makes the system observable and debuggable. Branch protection doesn't just prevent bad commitsÃ¢â‚¬â€it ensures every change meets quality standards.

**Phase 2 builds on these foundations** with features that leverage the standards. Once we have MCP, expanding providers via LiteLLM becomes trivial. Once we have OpenTelemetry, making the CLI prettier with real-time progress indicators becomes straightforward. Once we have proper configuration, adding plugin support becomes natural.

**Phase 3 and 4 are about refinement and reach** rather than fundamental capabilities. The GUI, advanced self-tools, and cosmetic improvements are valuable, but they're not foundational. They're the house we build on the foundation, not the foundation itself.

### Why This Matters Now

The AI development landscape is consolidating around standards faster than anyone expected. MCP was introduced in November 2024 and is already approaching universal adoption. OpenTelemetry's GenAI semantic conventions were formalized in early 2025. The window for "build everything ourselves" has closed. The window for "integrate with standards and differentiate on capabilities" is wide open.

We're not abandoning our visionÃ¢â‚¬â€we're recognizing that our vision is best served by standing on the shoulders of standards rather than building everything from scratch. The bots project's value isn't in reimplementing tool connectivity or observability. It's in conversation trees, functional prompts, and agentic capabilities that no standard can provide.

### The Path Forward

This isn't a pivotÃ¢â‚¬â€it's a maturation. We're moving from "build an AI framework" to "build the best agentic AI system on top of industry standards." The difference is critical. One path leads to constant maintenance of infrastructure. The other leads to innovation on capabilities.

Every item in this document, from MCP integration to GUI development, flows from this philosophy: **embrace standards for infrastructure, innovate on capabilities, and build for production**. This is how we ensure the bots project remains relevant, maintainable, and valuable as the AI landscape continues its rapid evolution.

The future of AI development isn't about building walled gardensÃ¢â‚¬â€it's about building excellent tools that work seamlessly in a standardized ecosystem. That's the future we're building toward.

---

---

## 1. Expand Provider Base

**Current State**: 
- Supports Anthropic Claude, OpenAI GPT, and Google Gemini
- v3.0.0 achieved multi-provider support with 97%+ test pass rate

**Goal**: Add support for additional LLM providers

**Potential Providers**:
- Cohere
- Mistral AI
- Local models (Ollama, LM Studio)
- Azure OpenAI (separate from standard OpenAI)
- AWS Bedrock
- Hugging Face Inference API

**Priority**: Medium

---

## 2. Make CLI Prettier

**Goal**: Enhance visual presentation and user experience

**Potential Improvements**:
- Color coding for different message types
- Syntax highlighting for code in tool results
- Progress indicators for long-running operations (see item 12)
- Rich text formatting (using `rich` or `textual`)
- Better error message formatting

**Priority**: Medium

---

## 3. JavaScript GUI / Frontend Backend for CLI

**Goal**: Create web-based GUI that interfaces with CLI backend

**Architecture Options**:
- Thin Client: FastAPI backend + React frontend + WebSocket
- Electron App: Package CLI with Electron
- Jupyter-style Notebook: Web-based notebook interface

**Features**: Visual tree navigation, drag-and-drop, side-by-side comparison, visual FP builder

**Related**: See large_refactor_tasks.md item 2 - "GUI over the cli"

**Priority**: Low-Medium

---

## 4. Rename auto_stash to 'mustache' (must stash)

**Goal**: Rename for better branding/memorability

**Changes**: CLI command, config keys, documentation, help text

**Priority**: Low

---

## 5. Ensure CLI Haiku Bots Match Provider

**Goal**: Initialize utility bots from same provider as main CLI bot

**Provider Model Tiers**:
- Anthropic: Sonnet (flagship) / Haiku (fast)
- OpenAI: GPT-4 Turbo (flagship) / GPT-4o-mini (fast)
- Google: Gemini Pro (flagship) / Gemini Flash (fast)

**Priority**: Medium

---

## 6. Configure CLI More Thoroughly (Plugins?)

**Goal**: Comprehensive configuration system with plugin support

**Categories**: Display settings, behavior settings, provider settings, plugin system

**Related**: See large_refactor_tasks.md item 4 - "Update base.py to use config file"

**Priority**: Medium-High

---

## 7. Review large_refactor_tasks.md

**Status**: Ã¢Å“â€œ COMPLETED

**Key Items Found**:
1. Conversation Tree Visualization Tools
2. GUI over the cli
3. Enhanced Callback System for functional prompts
4. Update base.py to use config file
5. Centralized file-writing wrapper with BOM removal
6. Tool requirements decorator
7. Repo-wide logging strategy
8. bot.requirements for tool dependencies
9. AST warnings cleanup
10. python_edit feedback improvements
11. Autosave behavior improvements
12. Terminal tool output format
13. Tool configurations in CI/CD
14. Fix test parallelism
15. Uniform tempfile handling

**Priority**: High

---

## 8. Refactor build_messages to Match tool_handler Pattern

**Goal**: Standardize message building to follow tool_handler's build_schema pattern

**Benefits**: Consistency, easier provider addition, better maintenance

**Priority**: Medium-High

---

## 9. Organize Tests Better - Best Practices

**Goal**: Implement testing best practices

**Structure**: tests/unit/, tests/integration/, tests/e2e/, tests/fixtures/

**Patterns**: pytest fixtures, parameterization, markers, AAA pattern

**Related**: Fix test parallelism, uniform tempfile handling

**Priority**: High

---

## 10. Expand self_tools Beyond branch_self

**Goal**: Add more tools for bots to manage their own conversation context

**Proposed Tools**:
- delete_stale_context: Remove outdated message pairs
- summarize_context: Replace verbose history with summary
- fork_from_node: Create branch from earlier point
- merge_branches: Combine insights from multiple branches
- list_conversation_nodes: Get overview of structure
- mark_checkpoint: Create named checkpoint
- goto_checkpoint: Navigate to checkpoint

**Implementation Phases**:
1. Core context management (delete_stale_context, list_conversation_nodes, fork_from_node)
2. Advanced operations (summarize_context, merge_branches)
3. Navigation helpers (mark_checkpoint, goto_checkpoint)

**Priority**: Medium-High

---

## 11. Remove Print Statements from anthropic_bots.py

**Goal**: Remove all print statements and replace with logging or callbacks

**Locations**: Mailbox send, tool execution, API calls, state transitions

**Implementation**: Replace with logging module or callback system (item 12)

**Related**: Repo-wide logging strategy

**Priority**: Medium

---

## 12. Add Callbacks to Major Bot Operation Steps

**Goal**: Implement callback system with progress indicators

**Major Steps**:
1. Message Building
2. API Call
3. Response Processing
4. Tool Execution

**Progress Indicator**: Four dots (. .. ... ....)

**Callback Interface**:
- on_step_start(step_name, metadata)
- on_step_complete(step_name, result)
- on_step_error(step_name, error)
- on_tool_start(tool_name, args)
- on_tool_complete(tool_name, result)

**Use Cases**: Progress indication, logging, monitoring, debugging, testing

**Related**: Enhanced Callback System for functional prompts

**Priority**: Medium-High

---


## 13. MCP Integration (Model Context Protocol)

**Current State**: 
- No MCP support
- Tools are bot-specific, not accessible to other MCP clients

**Goal**: Integrate MCP as both client and server

### MCP as Client (Priority 1)
**Purpose**: Connect to existing MCP servers to access their tools

**Implementation**:
```python
# Bot gains access to all MCP server tools
bot = AnthropicBot()
bot.add_mcp_server("filesystem", "npx @modelcontextprotocol/server-filesystem /path")
bot.add_mcp_server("github", "npx @modelcontextprotocol/server-github")
bot.add_mcp_server("postgres", "npx @modelcontextprotocol/server-postgres")
# Now bot can use filesystem, GitHub, and PostgreSQL tools via MCP
```

**Benefits**:
- Instant access to growing MCP ecosystem
- Standardized tool connectivity (like USB-C for AI)
- Compatible with Claude Desktop, Cursor, and other MCP clients
- No need to build custom integrations for each tool

**MCP Ecosystem (October 2025)**:
- 90% of organizations projected to use MCP by end of 2025
- Major adoption: Microsoft, OpenAI, Google DeepMind
- Early adopters: Block, Apollo, Zed, Replit, Codeium, Sourcegraph
- Microsoft has MCP in Azure AI Foundry
- Market growing from $1.2B (2022) to $4.5B (2025)

**Implementation Steps**:
1. Install MCP Python SDK: `pip install mcp`
2. Create MCPToolWrapper class to convert MCP tools to bot-compatible functions
3. Add `bot.add_mcp_server(name, command)` method
4. Handle async MCP communication
5. Test with popular MCP servers (filesystem, github, etc.)

### MCP as Server (Priority 2)
**Purpose**: Expose your bot's tools as MCP server for other applications

**Implementation**:
```python
# Your code_tools become available to Claude Desktop, Cursor, etc.
from bots.mcp import MCPServer

mcp_server = MCPServer()
mcp_server.expose_tools(code_tools)
mcp_server.expose_tools([python_edit, python_view, branch_self])
mcp_server.start()
```

**Benefits**:
- Your excellent tools (python_edit, branch_self, etc.) become available to entire MCP ecosystem
- Other developers can use them in Claude Desktop, Cursor, Windsurf, etc.
- Positions your project as valuable MCP tool provider
- Increases project visibility and adoption

**Tools to Expose**:
- python_edit - Scope-aware Python editing
- python_view - Scope-aware Python viewing
- branch_self - Parallel conversation exploration
- execute_python - Python code execution
- execute_powershell - PowerShell execution
- All self_tools (when implemented)

**Related Standards**:
- Open Agentic Schema Framework (OASF) - Launched early 2025 for agent interoperability
- Agent Connect Protocol (ACP) - Part of AGNTCY initiative for agent-to-agent communication

**Priority**: High (Phase 1 for Client, Phase 2 for Server)

**Why MCP Over LangChain**:
- Simpler protocol vs. complex framework
- Industry standard emerging NOW
- LangChain itself is adapting to MCP (released MCP adapters)
- "USB-C for AI" - universal connectivity standard
- Less complexity than direct LangChain integration

---

## 14. OpenTelemetry Integration for Observability

**Current State**: 
- Print statements scattered throughout code (item 11)
- No structured logging or monitoring
- Difficult to debug issues in production
- No visibility into performance bottlenecks
- No cost/token tracking

**Goal**: Implement comprehensive observability using OpenTelemetry standard

### What is Observability?

**Observability** = Understanding what's happening inside your system by examining its outputs

**Three Pillars**:
1. **Logs** - What happened? (events, errors, state changes)
2. **Metrics** - How much/many? (API calls, response times, token usage)
3. **Traces** - Journey of a request (full flow with timing)

### Why OpenTelemetry?

**OpenTelemetry** is the industry standard for observability (like MCP for tools):
- CNCF-backed open standard
- Vendor-agnostic (works with any monitoring tool)
- Automatic instrumentation available
- Growing consensus: "Should be the standard for LLM observability"
- Semantic conventions for GenAI systems (2025)

### Implementation Design

#### Basic Setup
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Setup (one time)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)
```

#### Bot Integration
```python
class AnthropicBot:
    def respond(self, prompt):
        with tracer.start_span("bot.respond") as span:
            span.set_attribute("prompt_length", len(prompt))
            span.set_attribute("provider", "anthropic")
            span.set_attribute("model", self.model)

            # Step 1: Build messages
            with tracer.start_span("build_messages"):
                messages = self._build_messages()
                span.set_attribute("message_count", len(messages))

            # Step 2: API call
            with tracer.start_span("api_call") as api_span:
                api_span.set_attribute("input_tokens", count_tokens(messages))
                response = self._call_api(messages)
                api_span.set_attribute("output_tokens", response.usage.output_tokens)
                api_span.set_attribute("cost_usd", calculate_cost(response.usage))

            # Step 3: Process response
            with tracer.start_span("process_response"):
                result = self._process_response(response)

            # Step 4: Execute tools if needed
            if result.tool_calls:
                with tracer.start_span("execute_tools") as tool_span:
                    tool_span.set_attribute("tool_count", len(result.tool_calls))
                    for tool_call in result.tool_calls:
                        with tracer.start_span(f"tool.{tool_call.name}") as t_span:
                            t_span.set_attribute("tool_name", tool_call.name)
                            t_span.set_attribute("tool_args", str(tool_call.args))
                            result = self._execute_tool(tool_call)
                            t_span.set_attribute("tool_result_length", len(result))

            return result
```

#### What You Get
```
Trace: bot.respond (4.2s)
  Ã¢â€Å“Ã¢â€â‚¬ build_messages (0.1s)
  Ã¢â€â€š   Ã¢â‚¬Â¢ message_count: 5
  Ã¢â€Å“Ã¢â€â‚¬ api_call (2.8s)
  Ã¢â€â€š   Ã¢â‚¬Â¢ input_tokens: 1234
  Ã¢â€â€š   Ã¢â‚¬Â¢ output_tokens: 567
  Ã¢â€â€š   Ã¢â‚¬Â¢ cost_usd: 0.015
  Ã¢â€Å“Ã¢â€â‚¬ process_response (0.05s)
  Ã¢â€â€Ã¢â€â‚¬ execute_tools (1.25s)
      Ã¢â‚¬Â¢ tool_count: 2
      Ã¢â€Å“Ã¢â€â‚¬ tool.python_view (0.8s)
      Ã¢â€â€š   Ã¢â‚¬Â¢ tool_name: python_view
      Ã¢â€â€š   Ã¢â‚¬Â¢ tool_result_length: 2456
      Ã¢â€â€Ã¢â€â‚¬ tool.python_edit (0.45s)
          Ã¢â‚¬Â¢ tool_name: python_edit
          Ã¢â‚¬Â¢ tool_result_length: 89
```

### Integration with Existing Items

#### Replaces Item 11 (Remove Print Statements)
**Before:**
```python
print("Sending message to mailbox...")
print(f"Tool execution: {tool_name}")
```

**After:**
```python
logger.info("mailbox.send", extra={"message_id": msg_id})
span.add_event("tool.execution", {"tool_name": tool_name})
```

#### Enables Item 12 (Progress Callbacks)
```python
class ObservabilityCallbacks(BotCallbacks):
    def on_step_start(self, step_name, metadata):
        # Log to OpenTelemetry
        span = trace.get_current_span()
        span.add_event(f"step.{step_name}.start", metadata or {})

        # Show progress to user (four dots)
        print(".", end="", flush=True)

    def on_step_complete(self, step_name, result):
        span = trace.get_current_span()
        span.add_event(f"step.{step_name}.complete")
```

### Metrics to Track

**Performance Metrics**:
- `bot.response_time` - Total time for bot.respond()
- `bot.api_call_duration` - Time spent in API calls
- `bot.tool_execution_duration` - Time spent executing tools
- `bot.message_building_duration` - Time building messages

**Usage Metrics**:
- `bot.api_calls_total` - Count of API calls (by provider, model)
- `bot.tool_calls_total` - Count of tool executions (by tool name)
- `bot.conversations_total` - Count of conversations
- `bot.tokens_used` - Token usage (input/output, by provider)

**Cost Metrics**:
- `bot.cost_usd` - Cost in USD (by provider, model)
- `bot.cost_per_conversation` - Average cost per conversation

**Error Metrics**:
- `bot.errors_total` - Count of errors (by type, provider)
- `bot.tool_failures_total` - Count of tool failures (by tool)

### Benefits

**For Development**:
- Debug issues quickly (see exact flow and timing)
- Identify performance bottlenecks
- Understand tool usage patterns
- Track down errors with full context

**For Production**:
- Monitor system health
- Track costs and token usage
- Set up alerts for anomalies
- Audit trails for compliance
- Performance optimization

**For Users**:
- Better progress indicators (know what's happening)
- Faster issue resolution
- More reliable system

### Implementation Steps

**Phase 1: Basic Tracing**
1. Install OpenTelemetry: `pip install opentelemetry-api opentelemetry-sdk`
2. Add tracing to bot.respond() method
3. Add tracing to tool execution
4. Test with console exporter

**Phase 2: Structured Logging**
1. Replace all print statements with logging
2. Add OpenTelemetry logging integration
3. Configure log levels (DEBUG, INFO, WARNING, ERROR)
4. Add structured context to logs

**Phase 3: Metrics**
1. Add metrics collection
2. Track performance, usage, cost metrics
3. Set up dashboards (Grafana, Datadog, etc.)

**Phase 4: Production Observability**
1. Configure exporters (Jaeger, Zipkin, or cloud provider)
2. Set up alerting
3. Create runbooks for common issues
4. Add cost tracking and budgets

### Observability Backends (Choose One)

**Open Source**:
- Jaeger - Distributed tracing
- Prometheus + Grafana - Metrics and dashboards
- Loki - Log aggregation

**Commercial (with free tiers)**:
- Datadog - Full observability platform
- New Relic - APM and monitoring
- Honeycomb - Observability for complex systems
- Lightstep - Distributed tracing

**All work with OpenTelemetry** - switch anytime without code changes!

### Related Standards

- **OpenTelemetry GenAI Semantic Conventions** - Standard attributes for AI/LLM systems
- **OWASP LLM Security Verification Standard** - Security observability requirements

**Priority**: High (Phase 1)

**Effort**: Medium - Incremental implementation possible

**Impact**: High - Essential for production, debugging, and optimization

---

## 15. LiteLLM Integration for Provider Expansion

**Current State**: 
- Manual implementation for each provider (Anthropic, OpenAI, Gemini)
- Each provider requires custom code for API calls, message formatting, tool handling
- Adding new providers is time-consuming

**Goal**: Use LiteLLM as unified API layer for 100+ LLM providers

### What is LiteLLM?

**LiteLLM** provides a unified interface for 100+ LLM providers:
- OpenAI, Anthropic, Google, Cohere, Mistral, Replicate
- Azure OpenAI, AWS Bedrock, Vertex AI
- Local models (Ollama, LM Studio, vLLM)
- Open source models (Llama, Mistral, etc.)

**One API format for all providers:**
```python
from litellm import completion

# Works with ANY provider
response = completion(
    model="gpt-4",  # or "claude-3-5-sonnet", "gemini-pro", etc.
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Benefits

**Instant Provider Support**:
- 100+ providers immediately available
- No need to implement each provider manually
- Automatic handling of provider-specific quirks

**Unified Interface**:
- Same code works across all providers
- Easy to switch providers
- Easy to compare providers

**Active Maintenance**:
- LiteLLM team handles provider API changes
- New providers added regularly
- Bug fixes and updates

**Cost Tracking**:
- Built-in cost calculation for all providers
- Token usage tracking
- Budget management

### Implementation Approach

#### Option 1: LiteLLM as Base Layer
```python
from litellm import completion
import bots

class LiteLLMBot(bots.BaseBot):
    def __init__(self, model="gpt-4", **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def _call_api(self, messages):
        response = completion(
            model=self.model,
            messages=messages,
            tools=self._get_tool_schemas(),
            **self.api_params
        )
        return response

# Now supports 100+ providers!
bot = LiteLLMBot(model="claude-3-5-sonnet-20241022")
bot = LiteLLMBot(model="gpt-4-turbo")
bot = LiteLLMBot(model="gemini-1.5-pro")
bot = LiteLLMBot(model="ollama/llama3")  # Local model!
```

#### Option 2: Hybrid Approach
Keep existing provider implementations for fine-grained control, add LiteLLM for quick provider support:
```python
# Use native implementation for main providers
bot = AnthropicBot()  # Full control, optimized

# Use LiteLLM for others
bot = LiteLLMBot(model="cohere/command-r-plus")  # Quick support
```

### Integration with Other Items

**Complements Item 5** (CLI Haiku Bots):
```python
PROVIDER_MODELS = {
    'anthropic': {
        'flagship': 'claude-3-5-sonnet-20241022',
        'fast': 'claude-3-5-haiku-20241022'
    },
    'openai': {
        'flagship': 'gpt-4-turbo',
        'fast': 'gpt-4o-mini'
    },
    'google': {
        'flagship': 'gemini-1.5-pro',
        'fast': 'gemini-1.5-flash'
    },
    'cohere': {
        'flagship': 'command-r-plus',
        'fast': 'command-r'
    },
    'mistral': {
        'flagship': 'mistral-large-latest',
        'fast': 'mistral-small-latest'
    }
    # Easy to add more!
}
```

**Enables Item 1** (Expand Provider Base):
Instead of manually implementing each provider, use LiteLLM to get instant support for:
- Cohere
- Mistral AI
- Local models (Ollama, LM Studio)
- Azure OpenAI
- AWS Bedrock
- Hugging Face

### Considerations

**Pros**:
- Ã¢Å“â€¦ Instant 100+ provider support
- Ã¢Å“â€¦ Unified interface
- Ã¢Å“â€¦ Active maintenance
- Ã¢Å“â€¦ Cost tracking built-in
- Ã¢Å“â€¦ Easy to test different providers

**Cons**:
- Ã¢Å¡Â Ã¯Â¸Â Abstraction layer (slight overhead)
- Ã¢Å¡Â Ã¯Â¸Â Less control over provider-specific features
- Ã¢Å¡Â Ã¯Â¸Â Dependency on external library

**Recommendation**: 
- Use LiteLLM for quick provider expansion
- Keep native implementations for primary providers (Anthropic, OpenAI, Gemini)
- Best of both worlds: control + breadth

### Implementation Steps

1. Install LiteLLM: `pip install litellm`
2. Create LiteLLMBot class extending BaseBot
3. Implement _call_api() using litellm.completion()
4. Test with multiple providers
5. Add provider configuration
6. Update documentation
7. Add tests for LiteLLM integration

**Priority**: Medium (Phase 2)

**Effort**: Low - LiteLLM handles most complexity

**Impact**: High - Instant support for 100+ providers

---

## Additional Items from large_refactor_tasks.md

### 16. Centralized File-Writing Wrapper
**Goal**: Wrapper with BOM removal logic (for all tools using toolify decorator?)
**Priority**: Medium

### 17. Tool Requirements Decorator
**Goal**: Decorator that applies tool requirements to functions
**Priority**: Low-Medium

### 18. Bot Requirements System
**Goal**: bot.requirements parameter for tool dependencies
**Priority**: Medium

### 19. AST String vs Constant Warnings
**Goal**: Clean up AST warnings
**Priority**: Low

### 20. python_edit Feedback
**Goal**: Better feedback when input is incorrect
**Priority**: Complete!

### 21. Autosave Behavior
**Goal**: More intuitive autosave (save over loaded filename)
**Priority**: Low-Medium

### 22. Terminal Tool Output Format
**Goal**: Implicit [dir]> format like in terminal_tools.py
**Priority**: Complete!

### 23. Tool Configurations in CI/CD
**Goal**: Tool factories respecting CI/CD constraints
**Priority**: Medium

### 24. Test Parallelism
**Goal**: Fix test parallelism issues (mainly in terminal_tools)
**Priority**: High
**Status**: Ã¢Å“â€œ COMPLETED (test-efficiency branch)

```
Fixed PowerShell test files to use unique temp directories per test. Removed serial execution marker. Updated pr-checks.yml to use -n 12 for parallel execution. Tests now run in parallel without file conflicts.
```

### 25. Uniform Tempfile Handling
**Goal**: Consistent tempfile handling in tests
**Priority**: High
**Reason**: Tests pollute repository with extraneous files
**Status**: Ã¢Å“â€œ COMPLETED (test-efficiency branch)

```
Fixed test_patch_edit.py, test_class_replace.py, and test_python_edit_edge_cases.py to use temp directories. All test artifacts now properly isolated and cleaned up.
```

### Docker Testing Infrastructure (Archived)
**Status**: ✗ ARCHIVED (cleanup-docker branch)

Docker-based test infrastructure was developed but abandoned due to Docker Desktop issues. All Docker testing files have been moved to `archived_docker_testing/` directory and preserved on the `docker-testing` branch for potential future use. The infrastructure included Dockerfile, test orchestration scripts, comprehensive documentation, and pytest integration with --use-docker flags. See `archived_docker_testing/README.md` for details.

---

## 26. GitHub Branch Protection and CI/CD Guardrails

**Current State**: 
- Direct pushes to main branch are allowed
- No enforcement of CI/CD checks before merge
- Manual code review process

**Goal**: Implement branch protection rules and automated code review

**Priority**: Very High

### Branch Protection Rules

**Requirements for main branch**:
1. **Require pull request before merging**
   - No direct pushes to main
   - All changes must go through PR workflow

2. **Require status checks to pass**
   - All CI/CD tests must pass (green checkmark Ã¢Å“â€œ)
   - Cannot merge until all checks are green

3. **Require code review**
   - At least one approval required
   - CodeRabbit AI review + human review

4. **Additional protections**:
   - Require branches to be up to date before merging
   - Require linear history (optional)
   - Include administrators in restrictions

### Implementation Steps

#### Step 1: Configure Branch Protection
```
GitHub Repository Settings:
1. Go to Settings Ã¢â€ â€™ Branches
2. Add branch protection rule for "main"
3. Enable:
   Ã¢Ëœâ€˜ Require a pull request before merging
   Ã¢Ëœâ€˜ Require approvals (1 minimum)
   Ã¢Ëœâ€˜ Dismiss stale pull request approvals when new commits are pushed
   Ã¢Ëœâ€˜ Require status checks to pass before merging
   Ã¢Ëœâ€˜ Require branches to be up to date before merging
   Ã¢Ëœâ€˜ Require conversation resolution before merging
   Ã¢Ëœâ€˜ Do not allow bypassing the above settings (include administrators)
```

#### Step 2: Required Status Checks
Configure these checks to be required:
- `test` - Run test suite
- `lint` - Code quality checks
- `type-check` - Type checking (if applicable)
- `coverage` - Code coverage threshold
- `security` - Security scanning
- `coderabbit` - AI code review

#### Step 3: Set Up CodeRabbit

**What is CodeRabbit?**
- AI-powered code review assistant
- Automated PR reviews with contextual feedback
- Suggests improvements, catches bugs, identifies security issues
- Integrates directly with GitHub PRs

**Setup**:
1. Install CodeRabbit GitHub App
   - Go to https://github.com/apps/coderabbitai
   - Click "Install"
   - Select repository: benbuzz790/bots
   - Grant permissions

2. Configure CodeRabbit
   - Create `.coderabbit.yaml` in repository root:
   ```yaml
   # .coderabbit.yaml
   language: "en-US"

   reviews:
     profile: "chill"  # or "assertive" for stricter reviews
     request_changes_workflow: false  # Don't block PRs, just suggest
     high_level_summary: true
     poem: false  # Disable fun poems (optional)
     review_status: true  # Post review status

   chat:
     auto_reply: true

   # Customize review focus
   tone_instructions: |
     Focus on:
     - Code quality and maintainability
     - Potential bugs and edge cases
     - Security vulnerabilities
     - Performance issues
     - Test coverage
     - Documentation completeness

     Follow project principles:
     - YAGNI (You Aren't Gonna Need It)
     - KISS (Keep It Simple, Stupid)
     - Defensive programming (NASA methodology)
     - Small, incremental changes

   # File patterns to review
   path_filters:
     - "!**/*.md"  # Skip markdown files
     - "!**/test_*.py"  # Optional: lighter review for tests

   # Auto-review settings
   auto_review:
     enabled: true
     drafts: false  # Don't review draft PRs
     base_branches:
       - main
   ```

3. Test CodeRabbit
   - Create a test PR
   - CodeRabbit should automatically comment with review
   - Verify it's providing useful feedback

#### Step 4: Update CI/CD Workflow

Update `.github/workflows/test.yml` to be a required check:

```yaml
name: CI/CD Pipeline

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e .[dev]

      - name: Run tests
        run: |
          pytest tests/ -v --cov=bots --cov-report=term-missing

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

  lint:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install black flake8 mypy

      - name: Run Black
        run: black --check .

      - name: Run Flake8
        run: flake8 bots/ --max-line-length=100

      - name: Run MyPy (if using type hints)
        run: mypy bots/ --ignore-missing-imports
        continue-on-error: true  # Optional: don't fail on type errors initially

  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit security scan
        run: |
          pip install bandit
          bandit -r bots/ -f json -o bandit-report.json
        continue-on-error: true

      - name: Upload security report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: bandit-report.json
```

#### Step 5: PR Template

Create `.github/pull_request_template.md`:

```markdown
## Description
<!-- Describe your changes in detail -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Test updates

## Related Issues
<!-- Link to related issues: Fixes #123, Relates to #456 -->

## Testing
<!-- Describe the tests you ran and how to reproduce -->
- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines (YAGNI, KISS, defensive programming)
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated (if applicable)
- [ ] No new warnings generated
- [ ] Tests added/updated and passing
- [ ] Changes are small and focused (not too big)

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Additional Notes
<!-- Any additional information for reviewers -->
```

### Workflow After Implementation

**Developer Workflow**:
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes (small, incremental)
3. Commit and push: `git push origin feature/my-feature`
4. Create Pull Request on GitHub
5. Wait for CI/CD checks to run (automated)
6. CodeRabbit reviews automatically
7. Address CodeRabbit feedback
8. Request human review
9. Once approved + all checks green Ã¢â€ â€™ Merge

**What Blocks a Merge**:
- Ã¢ÂÅ’ Any CI/CD test failures
- Ã¢ÂÅ’ Code coverage below threshold
- Ã¢ÂÅ’ Linting errors
- Ã¢ÂÅ’ No approval from reviewer
- Ã¢ÂÅ’ Unresolved conversations
- Ã¢ÂÅ’ Branch not up to date with main

**What Allows a Merge**:
- Ã¢Å“â€¦ All tests passing (green checkmark)
- Ã¢Å“â€¦ Code coverage meets threshold
- Ã¢Å“â€¦ Linting passes
- Ã¢Å“â€¦ At least one approval
- Ã¢Å“â€¦ All conversations resolved
- Ã¢Å“â€¦ Branch up to date

### Benefits

**Quality Assurance**:
- No broken code reaches main
- Consistent code quality
- Automated checks catch issues early

**Code Review**:
- CodeRabbit provides instant AI feedback
- Human reviewers focus on architecture/design
- Faster review cycles

**Safety**:
- Protected main branch
- No accidental direct pushes
- Rollback is easier (clean history)

**Collaboration**:
- Clear PR process
- Discussion on changes
- Knowledge sharing through reviews

### Alternative/Additional Tools

**Other AI Code Review Tools**:
- **GitHub Copilot for PRs** - Similar to CodeRabbit
- **Sourcery** - Python-specific refactoring suggestions
- **DeepCode (Snyk)** - Security-focused

**Traditional Tools**:
- **SonarCloud** - Code quality and security
- **Codecov** - Coverage reporting with PR comments
- **Dependabot** - Dependency updates

**Recommendation**: Start with CodeRabbit (easy setup, comprehensive) + existing CI/CD

### Cost Considerations

**CodeRabbit Pricing** (as of 2025):
- Free for open source projects
- Pro: $15/user/month for private repos
- Enterprise: Custom pricing

**GitHub Actions**:
- 2,000 minutes/month free for private repos
- Unlimited for public repos

### Implementation Priority

**Phase 1** (Immediate):
1. Set up branch protection rules
2. Configure required status checks
3. Update CI/CD workflow

**Phase 2** (Short-term):
1. Install and configure CodeRabbit
2. Create PR template
3. Document workflow for contributors

**Phase 3** (Ongoing):
1. Refine CodeRabbit configuration based on feedback
2. Add additional checks as needed
3. Monitor and improve coverage thresholds

**Priority**: High (Phase 1) - Essential for code quality and preventing regressions

**Effort**: Low-Medium - Mostly configuration, minimal code changes

**Impact**: High - Significantly improves code quality and prevents bugs from reaching main

---

## Implementation Roadmap

### Phase 1: Repo Reliability (High Priority)
1. **GitHub Branch Protection & CodeRabbit** (item 26) - Guardrails for main branch
3. **OpenTelemetry Integration** (item 14) - Observability and monitoring
4. Remove print statements (item 11) - Replaced by OpenTelemetry
5. Add callback system (item 12) - Integrated with OpenTelemetry
6. Organize tests better (item 9)
7. Fix test parallelism (item 24)
8. Uniform tempfile handling (item 25)
9. Refactor build_messages pattern (item 8)
10. Ensure CLI haiku bots match provider (item 5)

### Phase 2: Core Features & Expansion (Medium Priority)
1. **MCP Integration - Client** (item 13) - Industry standard for tool connectivity
2. **MCP Integration - Server** (item 13) - Expose tools to ecosystem
3. **LiteLLM Integration** (item 15) - 100+ provider support
4. Configure CLI more thoroughly (item 6)
5. Update base.py to use config file
7. Centralized file-writing wrapper (item 16)
8. Bot requirements system (item 18)
9. Expand self_tools Phase 1 (item 10)
10. python_edit feedback improvements (item 20)

### Phase 3: Enhancement (Medium-Low Priority)
1. Make CLI prettier (item 2) - Integrate with OpenTelemetry for progress
2. Expand self_tools Phase 2-3 (item 10)
3. Rename auto_stash to mustache (item 4)
4. Tool requirements decorator (item 17)
5. Autosave behavior improvements (item 21)
6. Terminal tool output format (item 22)
7. AST warnings cleanup (item 19)

### Phase 4: Major Features (Low Priority, High Effort)
1. JavaScript GUI / Frontend backend (item 3)
2. Conversation tree visualization tools
3. Tool configurations in CI/CD (item 23)
4. Integration with emerging standards (OASF, ACP)

---

## Next Actions

1. **Immediate**: Prioritize Phase 1 items, create work orders
2. **Short-term**: Begin Phase 1 implementation
3. **Medium-term**: Complete Phase 1, begin Phase 2
4. **Long-term**: Evaluate GUI feasibility

---

**Last Updated**: 3-Oct-2025
**Maintainer**: Ben Rinauto
**Status**: Active Planning
