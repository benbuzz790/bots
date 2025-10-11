# Project Ideas and Future Development Notes
**Date**: 09-Oct-2025
**Project**: bots - Agentic Programming Framework

## Overview
This document tracks development ideas, feature requests, and architectural improvements for the bots project. Each item includes context, rationale, and implementation considerations.


---


## Recent Development Activity (Since v3.0.0 - Oct 2025)

### PR #111 - PR Comment Parser Utility (04-Oct-2025)
**Type**: Development Tooling

**Description**: Added utility to extract CodeRabbit AI prompts from GitHub PR comments
- Tool: `bots/dev/pr_comment_parser.py`
- Extracts actionable AI prompts from CodeRabbit review comments
- Supports both regular and inline review comments
- Filters outdated comments
- CLI usage: `python -m bots.dev.pr_comment_parser owner/repo PR_NUMBER [output_file]`

**Impact**: Improves developer workflow when addressing CodeRabbit feedback

**Roadmap Status**: Not a planned roadmap item - ancillary development tooling

---

## Development Philosophy & Strategic Direction

### The Core Principle: Standards Over Frameworks

The bots project has reached a critical inflection point. After successfully implementing multi-provider support and achieving a robust 97%+ test pass rate, we're now positioned to make a fundamental choice about our future direction. The landscape of AI development tools has matured significantly, and a clear pattern has emerged: **universal standards are winning over proprietary frameworks**.

This isn't about chasing trends--it's about recognizing that the industry has spoken. Model Context Protocol (MCP) is projected to reach 90% organizational adoption by the end of 2025. Microsoft, OpenAI, and Google have all committed to it. OpenTelemetry has become the de facto standard for observability. These aren't just popular tools; they're becoming the *lingua franca* of AI development.

### Why Standards Matter

When we initially considered integrating with LangChain, the complexity was overwhelming. Layers of abstraction, steep learning curves, and constant API changes made it feel like we were building on shifting sand. But MCP? It's a protocol--simple, clear, and purpose-built for one thing: connecting AI models to tools and data. It's the USB-C of AI, and just like USB-C, its value comes from universal adoption, not feature richness.

This realization shapes our entire strategy: **prioritize interoperability over features, standards over frameworks, simplicity over sophistication**.

### The Three Pillars of Our Strategy

#### 1. **Embrace Universal Standards**

We're not building in isolation. The bots project should be a *citizen* of the broader AI ecosystem, not an island. This means:

- **MCP Integration**: Our tools should be accessible to anyone using Claude Desktop, Cursor, or any MCP-compatible client. Conversely, our bots should be able to use the hundreds of MCP servers already published. This isn't just about compatibility--it's about network effects. Every MCP server we can connect to multiplies our capabilities without writing a single line of integration code.

- **OpenTelemetry for Observability**: Print statements scattered through code are a symptom of development without proper instrumentation. OpenTelemetry isn't just about removing print statements--it's about building production-ready software that can be monitored, debugged, and optimized in real-world deployments. When something goes wrong at 3 AM, structured traces and metrics are the difference between hours of debugging and minutes.

- **LiteLLM for Provider Expansion**: Rather than manually implementing each new LLM provider, we leverage LiteLLM's unified interface to support 100+ providers instantly. This isn't laziness--it's recognizing that provider APIs are commoditizing, and our value lies elsewhere.

#### 2. **Maintain Our Core Differentiators**

Standards handle connectivity and interoperability, but they don't replace our unique capabilities:

- **Conversation Trees**: The ability to branch, explore multiple paths, and navigate conversation history as a tree structure remains unique. Most frameworks treat conversations as linear chains. We treat them as explorable spaces.

- **Functional Prompts**: Composable patterns like `chain`, `branch`, `prompt_while`, and `par_branch_while` provide structured reasoning that goes beyond simple prompt-response cycles. These aren't just convenience functions--they're a programming model for AI interactions.

- **Tool Excellence**: Our tools like `python_edit` (scope-aware code editing) and `branch_self` (recursive self-branching) represent genuine innovation. By exposing them via MCP, we share this innovation with the broader community while maintaining our implementation advantages.

- **Self-Context Management**: The upcoming expansion of self-tools (delete_stale_context, fork_from_node, etc.) gives bots unprecedented control over their own conversation history. This is agentic AI in the truest sense--agents that can manage their own context.

#### 3. **Build for Production, Not Just Prototypes**

The shift from "works on my machine" to "works in production" requires fundamental changes:

- **Observability First**: OpenTelemetry integration isn't optional--it's foundational. Every API call, every tool execution, every decision point should be traceable. This enables debugging, optimization, cost tracking, and compliance.

- **Quality Guardrails**: Branch protection, required CI/CD checks, and automated code review (CodeRabbit) aren't bureaucracy--they're insurance against regressions. The coveted green checkmark isn't a badge of honor; it's a minimum bar for production readiness.

- **Test Organization**: Moving from "we have tests" to "we have a test strategy" means organizing tests by speed (unit/integration/e2e), using proper fixtures, and fixing parallelism issues. Fast feedback loops enable rapid iteration without sacrificing quality.

- **Configuration Over Code**: The shift to configuration-driven architecture (base.py using config files, plugin systems, etc.) makes the system adaptable without code changes. This is essential for deployment in diverse environments.

### The Practical Implications

This philosophy translates into concrete priorities:

**Phase 1 focuses on standards and foundations** because these are force multipliers. MCP integration doesn't just add features-- it adds an entire ecosystem. OpenTelemetry doesn't just remove print statements-- it makes the system observable and debuggable. Branch protection doesn't just prevent bad commits--it ensures every change meets quality standards.

**Phase 2 builds on these foundations** with features that leverage the standards. Once we have MCP, expanding providers via LiteLLM becomes trivial. Once we have OpenTelemetry, making the CLI prettier with real-time progress indicators becomes straightforward. Once we have proper configuration, adding plugin support becomes natural.

**Phase 3 and 4 are about refinement and reach** rather than fundamental capabilities. The GUI, advanced self-tools, and cosmetic improvements are valuable, but they're not foundational. They're the house we build on the foundation, not the foundation itself.

### Why This Matters Now

The AI development landscape is consolidating around standards faster than anyone expected. MCP was introduced in November 2024 and is already approaching universal adoption. OpenTelemetry's GenAI semantic conventions were formalized in early 2025. The window for "build everything ourselves" has closed. The window for "integrate with standards and differentiate on capabilities" is wide open.

We're not abandoning our vision--we're recognizing that our vision is best served by standing on the shoulders of standards rather than building everything from scratch. The bots project's value isn't in reimplementing tool connectivity or observability. It's in conversation trees, functional prompts, and agentic capabilities that no standard can provide.

### The Path Forward

This isn't a pivot-- it's a maturation. We're moving from "build an AI framework" to "build the best agentic AI system on top of industry standards." The difference is critical. One path leads to constant maintenance of infrastructure. The other leads to innovation on capabilities.

Every item in this document, from MCP integration to GUI development, flows from this philosophy: **embrace standards for infrastructure, innovate on capabilities, and build for production**. This is how we ensure the bots project remains relevant, maintainable, and valuable as the AI landscape continues its rapid evolution.

The future of AI development isn't about building walled gardens--it's about building excellent tools that work seamlessly in a standardized ecosystem. That's the future we're building toward.



## Monetization Strategy

**Strategic Direction**: Documentation-First Revenue Path

### Overview

The bots project has unique competitive advantages that position it for commercial success:
1. **Conversation trees** - Explore multiple documentation angles simultaneously
2. **branch_self** - Parallel exploration with n*log(n) scaling vs competitors' n^2
3. **Self-context management** - Handle large codebases efficiently
4. **Functional prompts** - Composable patterns for complex documentation workflows

### Primary Monetization Target: Automated Technical Documentation Generator

**Why Documentation First:**
- Real pain point with proven willingness to pay
- Does NOT require GUI (faster time to revenue)
- Leverages our core strengths (branching, trees, parallel exploration)
- Revenue funds future development (GUI, other services)
- Demonstrates competitive advantage (scaling efficiency)

**Target Market:**
- B2B SaaS companies with poor documentation
- Open source projects needing comprehensive docs
- Enterprise teams with large codebases

**Pricing Model:**
- $200-500/month per repository (based on size/complexity)
- Free tier for open source projects (marketing)
- Usage-based pricing for large enterprises

**Competitive Advantage:**
- n*log(n) scaling through parallel branching (vs competitors' n^2)
- Multi-perspective documentation (explore architecture, API, deployment simultaneously)
- Incremental updates (only regenerate changed sections)
- Conversation tree audit trail (show reasoning process)

### Secondary Targets (Revenue-Funded)

**AI Code Review Service** (Item 1 synergy):
- Leverage same GitHub integration infrastructure
- Use branching to explore multiple review angles
- Show exploration paths in review comments
- $50-200/month per repo or $0.10-0.50 per PR

**Conversation as a Service API** (Item 4):
- Expose conversation trees and branching as API
- Premium visual GUI as reference implementation
- Usage-based pricing: $0.01-0.05 per API call + LLM costs + 20% margin

**Bot Marketplace** (Item 2):
- Sell pre-trained specialized bots
- Documentation bots, review bots, domain experts
- $20-100 per bot or $10-30/month subscription

### Revenue Timeline

**Months 1-2**: Complete Phase 1 (foundation)
- OpenTelemetry cost tracking (essential for pricing)
- Callback system (progress indicators)
- Build messages refactor (clean architecture)

**Months 3-4**: Build Documentation Service (Phase 2)
- GitHub integration
- Documentation output system
- Automated workflows
- Usage tracking and metrics

**Month 5**: Launch MVP (Phase 3)
- Simple authentication/billing
- Basic multi-tenancy
- Early customer acquisition
- Target: 10-20 paying customers

**Month 6+**: Scale & Expand (Phase 4)
- Use revenue to fund GUI development
- Add code review service
- Build API offering
- Target: $10k+ MRR

### Success Metrics

**Technical:**
- Prove n*log(n) scaling advantage with OpenTelemetry metrics
- Document generation time < 5 minutes for typical repo
- Cost per documentation run < $2 (maintain 80%+ margin at $10/run)

**Business:**
- 10 paying customers by Month 5
- $5k MRR by Month 6
- $10k MRR by Month 9
- 90%+ customer retention

**Strategic:**
- GUI development funded by Month 6
- Code review service launched by Month 8
- API service beta by Month 10

---

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

**Status**: [DONE] COMPLETED

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

**Status**: DONE (WO012, 09-Oct-2025)

**Delivered**:
- Reorganized tests into unit/, integration/, e2e/ structure
- Created centralized fixtures/ directory
- Implemented proper pytest fixtures and markers
- Applied AAA (Arrange-Act-Assert) pattern consistently
- Fixed test parallelism issues
- Uniform tempfile handling implemented

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

**Status**: [DONE] COMPLETED (PR #114 - 06-Oct-2025)

---

## 12. Add Callbacks to Major Bot Operation Steps

**Status**: DONE (WO015 - 10-Oct-2025)

**Delivered**:
- Complete callback system (BotCallbacks base class)
- OpenTelemetryCallbacks for observability integration
- ProgressCallbacks for user-facing progress indicators
- Full integration with all bot providers (AnthropicBot, OpenAIBot, GeminiBot)
- Callback support in ToolHandler for tool execution tracking
- Comprehensive documentation (docs/observability/CALLBACKS.md)
- 19 callback tests (100% passing)

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
  |-- build_messages (0.1s)
       * message_count: 5
  |-- api_call (2.8s)
       * input_tokens: 1234
       * output_tokens: 567
       * cost_usd: 0.015
  |-- process_response (0.05s)
  +-- execute_tools (1.25s)
        * tool_count: 2
      |-- tool.python_view (0.8s)
           * tool_name: python_view
           * tool_result_length: 2456
      +-- tool.python_edit (0.45s)
            * tool_name: python_edit
            * tool_result_length: 89
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

**Status**: DONE (WO015 - 10-Oct-2025)

**All 4 Phases Complete**:
- [DONE] Phase 1: Basic Tracing - COMPLETE (PR #114)
- [DONE] Phase 2: Structured Logging - COMPLETE (PR #114)
- [DONE] Phase 3: Metrics - COMPLETE (WO015)
- [DONE] Phase 4: Production Observability - COMPLETE (WO015)

**Delivered in PR #114 (Phases 1-2)**:
- New /bots/observability module with tracing support
- Configuration system with environment variables
- Full instrumentation of all bot providers (Anthropic, OpenAI, Gemini)
- Structured logging replaces print statements
- enable_tracing parameter for per-bot control
- 57 tests added (100% passing)
- 100% backward compatibility

**Delivered in WO015 (Phases 3-4)**:
- Cost calculator for all providers (27 models: Anthropic, OpenAI, Google)
- Metrics infrastructure (11 instruments: 4 histograms, 7 counters)
  - Performance: response_time, api_call_duration, tool_execution_duration, message_building_duration
  - Usage: api_calls_total, tool_calls_total, tokens_used
  - Cost: cost_usd (histogram), cost_total_usd (counter)
  - Errors: errors_total, tool_failures_total
- Callback system (BotCallbacks, OpenTelemetryCallbacks, ProgressCallbacks)
- Production exporters (Console, OTLP, Jaeger)
- 119 new tests (118 passing, 99.2% pass rate)
- Complete documentation (4 guides: SETUP.md, COST_TRACKING.md, DASHBOARDS.md, CALLBACKS.md)
- Total: 176 observability tests, 173 passing (98.3%)

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
- [x] Instant 100+ provider support
- [x] Unified interface
- [x] Active maintenance
- [x] Cost tracking built-in
- [x] Easy to test different providers

**Cons**:
-   Abstraction layer (slight overhead)
-   Less control over provider-specific features
-   Dependency on external library

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
**Status**: [DONE] COMPLETED (PR #112, 05-Oct-2025)

```
Fixed PowerShell test files to use unique temp directories per test. Removed serial execution marker. Updated pr-checks.yml to use -n 12 for parallel execution. Tests now run in parallel without file conflicts.
```

### 25. Uniform Tempfile Handling
**Goal**: Consistent tempfile handling in tests
**Priority**: High
**Reason**: Tests pollute repository with extraneous files
**Status**: [DONE] COMPLETED (PR #112, 05-Oct-2025)

```
Fixed test_patch_edit.py, test_class_replace.py, and test_python_edit_edge_cases.py to use temp directories. All test artifacts now properly isolated and cleaned up.
```

### Docker Testing Infrastructure (Archived)
**Status**: [ARCHIVED] ARCHIVED (PR #113, 05-Oct-2025)

Docker-based test infrastructure was developed but abandoned due to Docker Desktop issues. All Docker testing files have been moved to `archived_docker_testing/` directory and preserved on the `docker-testing` branch for potential future use. The infrastructure included Dockerfile, test orchestration scripts, comprehensive documentation, and pytest integration with --use-docker flags. See `archived_docker_testing/README.md` for details.

**PR #113 Actions**:
- Archived all Docker files to `/archived_docker_testing/` directory
- Removed Docker-related code from conftest.py
- Created comprehensive README explaining the history
- Preserved original setup on docker-testing branch

---

## 26. GitHub Branch Protection and CI/CD Guardrails - DONE

**Status**: DONE (PR #110, 04-Oct-2025)

**Delivered**:
- CodeRabbit configuration (.coderabbit.yaml)
- PR template (.github/pull_request_template.md)
- PR validation workflow (.github/workflows/pr-checks.yml)
- Branch protection setup guide (docs/BRANCH_PROTECTION_SETUP.md)
- Updated CONTRIBUTING.md with PR workflow

**Goal**: Implement branch protection rules and automated code review

**Priority**: Very High

### Branch Protection Rules

**Requirements for main branch**:
1. **Require pull request before merging**
   - No direct pushes to main
   - All changes must go through PR workflow

2. **Require status checks to pass**
   - All CI/CD tests must pass (green checkmark [DONE])
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
1. Go to Settings -> Branches
2. Add branch protection rule for "main"
3. Enable:
   [ ] Require a pull request before merging
   [ ] Require approvals (1 minimum)
   [ ] Dismiss stale pull request approvals when new commits are pushed
   [ ] Require status checks to pass before merging
   [ ] Require branches to be up to date before merging
   [ ] Require conversation resolution before merging
   [ ] Do not allow bypassing the above settings (include administrators)
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
9. Once approved + all checks green -> Merge

**What Blocks a Merge**:
- Any CI/CD test failures
- Code coverage below threshold
- Linting errors
- No approval from reviewer
- Unresolved conversations
- Branch not up to date with main

**What Allows a Merge**:
- [x] All tests passing (green checkmark)
- [x] Code coverage meets threshold
- [x] Linting passes
- [x] At least one approval
- [x] All conversations resolved
- [x] Branch up to date

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


## 27. GitHub Integration & Webhook System

**Goal**: Enable automated repository access and event-driven workflows

**Components**:
1. **GitHub App**:
   - OAuth authentication for repo access
   - Webhook endpoint for commit/PR events
   - Permission scopes: read repo, write comments, read/write webhooks

2. **Webhook Handler**:
   - Process commit events (trigger doc regeneration)
   - Process PR events (trigger code review)
   - Queue system for async processing
   - Rate limiting and error handling

3. **Repository Access**:
   - Clone/pull repositories
   - Read file contents
   - Navigate directory structure
   - Track file changes (incremental updates)

**Implementation**:
```python
# GitHub App integration
from github import Github
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    if event == 'push':
        # Trigger documentation regeneration
        repo_url = payload['repository']['clone_url']
        changed_files = [commit['modified'] for commit in payload['commits']]
        queue_doc_generation(repo_url, changed_files)

    return {'status': 'ok'}
```

**Priority**: High (Phase 2 - Documentation Service Enablement)

**Effort**: Medium - GitHub API is well-documented

**Impact**: High - Essential for automated documentation service

**Related**: Enables items 28, 29 (documentation workflow)

---

## 28. Documentation Output System

**Goal**: Generate high-quality documentation from conversation trees

**Components**:
1. **Markdown Generator**:
   - Convert conversation trees to structured markdown
   - Generate README.md, API docs, architecture docs
   - Cross-reference linking
   - Code snippet extraction and formatting

2. **HTML/Static Site Generator**:
   - Convert markdown to static site (MkDocs, Docusaurus, etc.)
   - Custom themes and styling
   - Search functionality
   - Version control for docs

3. **Multi-Format Support**:
   - README.md for GitHub
   - Wiki pages
   - API documentation (OpenAPI/Swagger)
   - Architecture diagrams (Mermaid)
   - Deployment guides

4. **Template System**:
   - Customizable doc templates
   - Company branding
   - Section ordering
   - Content filtering

**Implementation**:
```python
class DocumentationGenerator:
    def __init__(self, bot, repo_path):
        self.bot = bot
        self.repo_path = repo_path

    def generate_docs(self):
        # Use branch_self to explore multiple doc sections in parallel
        sections = [
            "Architecture overview and design decisions",
            "API documentation with examples",
            "Deployment and configuration guide",
            "Testing and development workflow"
        ]

        # Parallel exploration (n*log(n) scaling advantage!)
        results = branch_self(self.bot, sections, allow_work=True)

        # Combine into cohesive documentation
        return self._combine_sections(results)

    def _combine_sections(self, results):
        # Generate markdown from conversation trees
        markdown = self._tree_to_markdown(results)

        # Generate static site
        html = self._markdown_to_html(markdown)

        return {'markdown': markdown, 'html': html}
```

**Key Features**:
- **Tree-based structure**: Documentation hierarchy mirrors conversation tree
- **Multi-perspective**: Explore different angles simultaneously (architecture, API, deployment)
- **Incremental updates**: Only regenerate changed sections
- **Audit trail**: Conversation history shows reasoning process

**Priority**: High (Phase 2 - Documentation Service Enablement)

**Effort**: Medium-High - Complex but well-defined

**Impact**: Very High - Core product feature

**Related**: Leverages items 10 (self_tools), 13 (MCP for filesystem access)

---

## 29. Automated Documentation Workflow

**Goal**: End-to-end automated documentation generation and updates

**Components**:
1. **Scheduled Generation**:
   - Nightly/weekly full documentation regeneration
   - Configurable schedules per repository
   - Priority queue for urgent updates

2. **Commit-Triggered Updates**:
   - Detect changed files from webhook
   - Incremental documentation updates
   - Only regenerate affected sections
   - Post PR comment with doc preview

3. **Quality Checks**:
   - Validate generated documentation
   - Check for broken links
   - Verify code examples compile
   - Ensure completeness (all public APIs documented)

4. **Deployment**:
   - Automatic deployment to GitHub Pages, Netlify, etc.
   - Version tagging
   - Rollback capability
   - Change notifications

**Workflow**:
```
1. Webhook receives commit event
2. Clone/pull repository
3. Identify changed files
4. Use branch_self to explore affected doc sections in parallel
5. Generate updated documentation
6. Run quality checks
7. Deploy to hosting platform
8. Post PR comment with preview link
9. Track metrics (generation time, cost, quality score)
```

**Priority**: High (Phase 2 - Documentation Service Enablement)

**Effort**: Medium - Orchestration of existing components

**Impact**: High - Completes documentation service MVP

**Related**: Requires items 27 (GitHub integration), 28 (doc output), 14 (metrics tracking)

---

## 30. Authentication & Billing System

**Goal**: Secure access control and revenue collection

**Components**:
1. **Authentication**:
   - GitHub OAuth for user login
   - API key generation for programmatic access
   - Role-based access control (admin, user, viewer)
   - Session management

2. **Billing Integration**:
   - Stripe integration for payments
   - Subscription management (monthly/annual)
   - Usage-based pricing tiers
   - Invoice generation

3. **Pricing Tiers**:
   - **Free**: Open source projects, 1 repo, basic features
   - **Starter**: $200/month, 5 repos, standard features
   - **Professional**: $500/month, 20 repos, advanced features, priority support
   - **Enterprise**: Custom pricing, unlimited repos, dedicated support, SLA

4. **Usage Tracking**:
   - Track documentation generations per repo
   - Monitor token usage and costs
   - Set usage limits per tier
   - Alert on approaching limits

**Implementation**:
```python
from stripe import Subscription, Customer
from flask_login import login_required

@app.route('/subscribe', methods=['POST'])
@login_required
def create_subscription():
    plan = request.json['plan']  # starter, professional, enterprise

    # Create Stripe customer and subscription
    customer = Customer.create(email=current_user.email)
    subscription = Subscription.create(
        customer=customer.id,
        items=[{'price': PRICING_PLANS[plan]}]
    )

    # Update user account
    current_user.subscription_id = subscription.id
    current_user.plan = plan
    db.session.commit()

    return {'status': 'subscribed', 'plan': plan}
```

**Priority**: High (Phase 3 - Documentation Service Launch)

**Effort**: Medium - Stripe API is straightforward

**Impact**: Very High - Required for revenue

**Related**: Requires item 14 (usage metrics for billing)

---

## 31. Multi-Tenancy Support

**Goal**: Isolate customer data and resources securely

**Components**:
1. **Data Isolation**:
   - Separate database schemas per customer
   - Isolated file storage (S3 buckets per customer)
   - Conversation history isolation
   - Bot state isolation

2. **Resource Quotas**:
   - Rate limiting per customer
   - Token usage limits per tier
   - Concurrent job limits
   - Storage quotas

3. **Security**:
   - API key scoping (customer-specific)
   - Repository access controls
   - Audit logging per customer
   - Data encryption at rest and in transit

4. **Performance**:
   - Connection pooling per tenant
   - Resource allocation fairness
   - Priority queues for premium tiers
   - Monitoring per tenant

**Implementation**:
```python
class TenantContext:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.db_schema = f"customer_{customer_id}"
        self.storage_bucket = f"docs-{customer_id}"
        self.rate_limit = self._get_rate_limit()

    def _get_rate_limit(self):
        plan = self._get_customer_plan()
        return RATE_LIMITS[plan]

    @contextmanager
    def isolated_execution(self):
        # Set database schema
        db.execute(f"SET search_path TO {self.db_schema}")

        # Set storage context
        storage.set_bucket(self.storage_bucket)

        # Apply rate limiting
        rate_limiter.check(self.customer_id, self.rate_limit)

        yield

        # Cleanup
        db.execute("RESET search_path")
```

**Priority**: High (Phase 3 - Documentation Service Launch)

**Effort**: Medium-High - Security-critical

**Impact**: Very High - Required for B2B service

**Related**: Requires item 30 (authentication)

---

## 32. Documentation Service MVP

**Goal**: Launch minimal viable product for automated documentation

**Components**:
1. **Landing Page**:
   - Value proposition and features
   - Pricing tiers
   - Demo/screenshots
   - Sign-up flow

2. **GitHub App Installation**:
   - One-click installation
   - Repository selection
   - Permission grants
   - Webhook configuration

3. **Dashboard**:
   - List of connected repositories
   - Documentation generation status
   - Usage metrics (generations, tokens, cost)
   - Settings and configuration

4. **Documentation Generation**:
   - Manual trigger button
   - Automatic on commit
   - Progress indicators
   - Preview before deployment

5. **Documentation Hosting**:
   - Generated docs viewable in dashboard
   - Public URL for sharing
   - Version history
   - Download as markdown/HTML

**User Flow**:
```
1. User signs up with GitHub OAuth
2. Selects pricing tier and enters payment
3. Installs GitHub App on repositories
4. Configures documentation settings (schedule, sections, style)
5. Triggers initial documentation generation
6. Reviews generated docs in dashboard
7. Approves and deploys to public URL
8. Receives automatic updates on commits
```

**MVP Features** (Keep it simple!):
- ✅ GitHub OAuth login
- ✅ Stripe subscription (3 tiers)
- ✅ GitHub App installation
- ✅ Manual doc generation trigger
- ✅ Basic markdown output
- ✅ Simple dashboard
- ✅ Usage tracking

**Post-MVP Features** (Add later):
- Custom templates
- Advanced styling
- API access
- Webhooks for notifications
- Team collaboration
- Analytics and insights

**Priority**: High (Phase 3 - Documentation Service Launch)

**Effort**: High - Full product integration

**Impact**: Very High - First revenue!

**Related**: Integrates items 27-31

---

---


## 39. Tutorial Expansion

**Current State**:
- Single tutorial: `tutorials/01_getting_started.md` (47 lines, very minimal)
- Good documentation exists (README, CLI_PRIMER, functional_prompt_primer)
- No hands-on tutorials for key features

**Goal**: Create comprehensive tutorial series covering all major features

**Missing Tutorial Topics**:
1. **Tool Development Tutorial** - How to create custom tools (HIGH PRIORITY)
2. **Conversation Tree Navigation Tutorial** - Branching and navigation
3. **Functional Prompts Tutorial** - Practical examples with real workflows
4. **Save/Load and Bot Sharing Tutorial** - Bot persistence and collaboration
5. **CLI Deep Dive Tutorial** - Step-by-step interactive CLI usage
6. **Multi-Provider Tutorial** - Using different LLM providers
7. **Advanced Patterns Tutorial** - Real-world workflows and patterns

**Recommended Structure**:
- tutorials/01_getting_started.md (EXISTS - needs expansion)
- tutorials/02_adding_tools.md (NEW - custom tool development)
- tutorials/03_conversation_trees.md (NEW - branching and navigation)
- tutorials/04_functional_prompts.md (NEW - practical FP examples)
- tutorials/05_cli_usage.md (NEW - interactive tutorial for CLI)
- tutorials/06_save_load_share.md (NEW - bot persistence and sharing)
- tutorials/07_multi_provider.md (NEW - using different LLMs)
- tutorials/08_advanced_workflows.md (NEW - real-world patterns)

**Priority**: Medium-High (improves onboarding and adoption)

**Effort**: Medium (each tutorial 1-2 hours to write)

---

## 40. CHATME.bot - Interactive Welcome Bot

**Current State**:
- 19 .bot files exist in repo (examples, tests, dev bots)
- No standardized "welcome" or "introduction" bot
- New users must create bots from scratch

**Goal**: Create welcoming introduction bot demonstrating key features

**Purpose**:
- Greet new users with pre-loaded conversation
- Demonstrate basic bot capabilities interactively
- Provide guided tour of features
- Show tools, conversation trees, and functional prompts in action
- Can be loaded with: `python -m bots.dev.cli CHATME.bot`

**Content Should Include**:
- Pre-loaded conversation showing example interactions
- Tools already added (code_tools, terminal_tools)
- System message explaining its purpose
- Conversation history demonstrating:
  - Basic Q&A
  - Tool usage examples
  - Navigation examples
  - Functional prompt examples

**Implementation**:
1. Create bot programmatically with curated conversation history
2. Add relevant tools
3. Set helpful system message
4. Save as `CHATME.bot` in repository root
5. Reference in README.md and installation docs
6. Could be auto-generated/updated via script

**Priority**: Medium (nice-to-have for user experience)

**Effort**: Low (2-3 hours to create and test)



## 41. Unix/Linux/Mac Compatibility

**Current State**:
- Repository is **Windows-centric**
- PowerShell-only terminal tools
- Windows-only CI/CD testing
- Unix/Mac users cannot use terminal execution features

**Goal**: Full cross-platform compatibility for Windows, Linux, and macOS

**Critical Compatibility Issues**:

1. **PowerShell Dependency (HIGH PRIORITY)**
   - File: `bots/tools/terminal_tools.py`
   - Issue: Entire terminal tool system is PowerShell-only
   - `execute_powershell()` function hardcoded
   - `PowerShellSession` class spawns `powershell` process
   - **Impact**: Terminal execution completely broken on Unix/Mac
   - **Solution**: Create bash/sh alternative or unified shell abstraction

2. **CI/CD Windows-Only (HIGH PRIORITY)**
   - File: `.github/workflows/pr-checks.yml`
   - All jobs run on `windows-latest` only
   - **Impact**: No testing on Linux/Mac, Unix bugs go undetected
   - **Solution**: Multi-OS matrix testing (see item 30)

3. **Subprocess Flags (Already Handled)**
   - `subprocess.CREATE_NO_WINDOW` has proper OS detection
   - `subprocess.STARTUPINFO` has conditional handling
   - **Status**: Already cross-platform compatible

**Implementation Approach**:

**Phase 1: Shell Abstraction Layer**
- Detect OS: `sys.platform` or `os.name`
- Route to `execute_powershell()` on Windows
- Route to `execute_bash()` on Unix/Mac
- Unified interface: `execute_shell(command)`

**Phase 2: Unix Shell Support**
- Create `BashSession` class (mirror of `PowerShellSession`)
- Handle bash-specific stateful execution
- Test on Linux/Mac

**Phase 3: CLI Updates**
- Change help text from "execute powershell" to "execute shell commands"
- Auto-detect and use appropriate shell

**Related Items**:
- Item 30 (Multi-OS Testing) - Required to validate Unix compatibility
- Item 31 (.bot File Association) - Must work cross-platform

**Priority**: High (blocks Unix/Mac users from using terminal features)

**Effort**: Medium (shell abstraction + testing)

---

## 42. Multi-OS Testing Infrastructure

**Current State**:
- All CI/CD workflows run exclusively on Windows (windows-latest)
- Python 3.12 only
- No OS matrix strategy
- Heavy Windows-specific UTF-8 encoding configuration

**Goal**: Test on Windows, Linux, and macOS with multiple Python versions

**Requirements**:

**1. CI/CD Changes**:
Add OS matrix to workflows with ubuntu-latest, windows-latest, macos-latest and Python versions 3.10, 3.11, 3.12

**2. Code Challenges to Address**:
- PowerShell tools need bash/sh equivalents for Unix
- Path handling (Windows backslash vs Unix forward slash)
- File encoding (Windows UTF-8 BOM vs Unix clean UTF-8)
- Terminal/shell differences
- File permissions (Unix chmod vs Windows ACLs)
- Line endings (CRLF vs LF)

**3. Test Infrastructure Needs**:
- OS-specific test fixtures
- Conditional test skipping for OS-specific features
- OS detection and conditional tool loading
- Platform-specific mocking strategies

**Benefits**:
- Catch OS-specific bugs before users encounter them
- True cross-platform compatibility validation
- Broader user base support (Linux/Mac developers)
- More robust, production-ready codebase

**Relationship to Other Items**:
- **Directly enables**: Item 29 (Unix compatibility)
- **Complements**: Test organization efforts (WO012)
- **Foundation**: Cross-platform support strategy

**Priority**: High (foundational for cross-platform support)

**Effort**: Medium-High (requires tool refactoring + CI/CD updates)

---

## 43. .bot File Association - Open in Terminal

**Current State**:
- CLI supports loading: `python -m bots.dev.cli [filepath]`
- No file association - must manually type command
- Double-clicking .bot files doesn't work

**Goal**: Double-click .bot files to open in terminal with CLI loaded

**Cross-Platform Implementation**:

**Phase 1: Console Entry Point (Essential)**
- Add `console_scripts` entry point to setup.py
- Creates `bots-cli` command available system-wide
- Cross-platform foundation for file associations

**Phase 2: Platform-Specific File Associations**

**Windows**:
- Registry file (.reg) to associate .bot extension
- Command: `cmd.exe /k bots-cli "%1"`
- Keeps terminal open after loading bot

**macOS**:
- AppleScript wrapper or .app bundle
- Opens Terminal.app with `bots-cli` command
- Alternative: Automator workflow

**Linux**:
- XDG .desktop file for application registration
- MIME type registration for .bot files
- Command: `x-terminal-emulator -e bots-cli %f`

**Phase 3: Automated Installer (Optional)**
- Script to detect OS and install associations
- May require admin/sudo permissions
- Provide manual instructions as fallback

**Key Challenges**:
- Terminal must stay open after loading bot
- Must work with user's Python environment (entry point solves this)
- Platform-specific terminal invocation differences
- May require admin/sudo permissions

**Recommended Minimal Implementation**:
- Add entry_points to setup.py
- Provide platform-specific installation scripts/files in `docs/file_associations/`
- Document manual association steps for each OS

**Priority**: Medium (quality of life improvement)

**Effort**: Low-Medium (mostly documentation and scripts)

---

---

## 44. Repository-Level Tools

**Current State**:
- File-level tools exist (view, edit individual files)
- Meta-tools exist (coordinate multiple bots/files)
- **Gap**: No true repository-wide awareness tools

**Goal**: Tools that operate on entire codebase rather than individual files

**What "Repository-Level Tools" Means**:
- Understand repository structure (git repos, project layout, dependencies)
- Provide repository-wide context and awareness
- Enable cross-file operations (refactoring, analysis, testing)

**Proposed Tool Categories**:

**1. Repository Analysis**:
- `analyze_repository_structure()` - Map entire repo structure
- `find_dependencies()` - Analyze import graphs
- `identify_entry_points()` - Find main files, CLIs, APIs
- `analyze_test_coverage()` - Repository-wide coverage

**2. Repository Navigation**:
- `search_codebase(query)` - Search across all files
- `find_definition(symbol)` - Locate function/class definitions
- `find_usages(symbol)` - Find all usages
- `get_call_graph()` - Generate call graph

**3. Repository Operations**:
- `refactor_across_files(old, new)` - Rename across repo
- `update_imports()` - Fix imports repository-wide
- `run_repository_tests()` - Full test suite execution
- `generate_documentation()` - Create repo-wide docs

**4. Repository Context**:
- `get_repository_summary()` - High-level overview
- `get_architecture_diagram()` - Architecture visualization
- `get_recent_changes()` - Git history
- `get_project_metadata()` - Package info, dependencies

**5. Repository Management**:
- `create_module(name, spec)` - Create new module
- `remove_module(name)` - Remove module + references
- `merge_modules()` - Combine modules
- `split_module()` - Break large modules

**Implementation Phases**:
1. **Phase 1**: Basic repository context (structure, search, summary)
2. **Phase 2**: Advanced navigation (symbols, call graphs, dependencies)
3. **Phase 3**: Repository operations (refactoring, testing, docs)

**Use Cases**:
- Onboarding new bots with full repo context
- Large cross-file refactorings
- Architecture analysis and understanding
- Repository-wide code quality checks
- Auto-generating comprehensive documentation

**Priority**: Medium (enables sophisticated development workflows)

**Effort**: High (requires integration with AST, git, testing frameworks)

---

## 33. Functional Prompts on Specific Branches

**Current State**:
- Functional prompts always operate from `bot.conversation` (current node)
- No built-in way to apply FPs to specific branches in conversation tree
- Workaround requires manual conversation manipulation

**Goal**: Enable applying any functional prompt to specific nodes in conversation tree

**Feature Description**:
Apply any functional prompt (chain, branch, prompt_while, etc.) to specific nodes in the conversation tree, not just the current node.

**Use Cases**:
1. **Continue specific branch**: Apply `prompt_while` to Branch B while leaving A and C untouched
2. **Parallel branch processing**: Apply same FP to all branches (e.g., "write tests" for each file)
3. **Nested workflows**: Create complex multi-level branching with different FPs per branch
4. **Branch recovery**: Resume work on abandoned branches
5. **Selective processing**: Different FPs for different branches based on content

**Implementation Approach**:

**Phase 1: Helper Function** (Low effort, high value)
Create `apply_to_node(bot, node, fp_function, *args, **kwargs)` that temporarily sets bot.conversation to target node, executes FP, then restores original conversation.

**Phase 2: Convenience Functions** (If Phase 1 sees adoption)
- `apply_to_branches(bot, nodes, fp_function, ...)` - Apply FP to multiple nodes
- `apply_to_leaves(bot, fp_function, ...)` - Apply FP to all leaf nodes
- `apply_to_matching(bot, condition, fp_function, ...)` - Apply to nodes matching condition

**Phase 3: Context Manager** (Most elegant)
Create context manager for cleaner syntax when working with specific nodes.

**Benefits**:
- Natural extension of existing conversation tree patterns
- Enables sophisticated multi-branch reasoning
- Low implementation cost, high value
- No breaking changes (pure addition)

**Priority**: Medium-High (powerful feature, low cost)

**Effort**: Low (Phase 1), Medium (Phases 2-3)

---

## 34. Improve Save/Load Behavior

**Current State**:
- **Critical inconsistency**: `Bot.load()` uses `replies[0]` (first/oldest), but CLI overrides to `replies[-1]` (last/most recent)
- Default filename: `{bot.name}@{timestamp}.bot`
- Autosave filename: `{bot.name}.bot` (overwrites each time)
- Bot doesn't track source filename
- Inconsistent behavior between direct load and CLI load

**Goal**: Consistent, intuitive save/load behavior with better defaults

**Proposed Changes**:

**1. Load to Last Messaged Node (replies[-1])**
- **Issue**: Line 2540-2541 in `base.py` uses `replies[0]`
- **Fix**: Change to `replies[-1]` to match CLI behavior and user expectations
- **Rationale**: Users expect to continue from most recent work, not oldest branch

**2. Track Bot Filename**
- **Issue**: Bot has `self.name` but doesn't track source filename
- **Fix**: Add `self.filename` attribute to remember source file
- **Benefit**: Enables intelligent autosave to correct file

**3. Separate Quicksave from Named Save**
- **Issue**: Autosave uses `{name}.bot`, conflicts with intentional saves
- **Fix**: 
  - Autosave to `quicksave.bot` (working file, can be overwritten)
  - Manual save uses tracked filename or prompts for new name
- **Benefit**: Stable named bots + safe working quicksave

**4. Intelligent Save Behavior**
- If bot loaded from file: save back to that file by default
- If bot created fresh: prompt for filename or use `quicksave.bot`
- Autosave always uses `quicksave.bot` unless filename is tracked

**Test Coverage Gaps**:
- No tests verify which reply is selected after load
- No tests for filename tracking across save/load cycles
- No tests for autosave behavior with tracked filenames

**Priority**: High (fixes critical inconsistency, improves UX)

**Effort**: Low-Medium (code changes simple, testing important)

---

## 35. Cross-Directory Bot Loading - RESOLVED

**Status**: RESOLVED (07-Oct-2025) - NOT A BUG

**Original Report**:
Bot loading was reported to fail when bot file is loaded from a different working directory than where it was saved, if the bot contains tools loaded from relative file paths.

**Investigation Results**:
Upon thorough testing, this bug does NOT exist. The system already implements the recommended solution (Option 3).

**How It Actually Works**:
1. When tools are added via file path, the system reads and stores the FULL SOURCE CODE
2. The source code is serialized into the .bot file
3. On load, the system executes the stored source code (not re-reading from file path)
4. This makes bots truly portable and shareable across directories

**Verification**:
- Created test: `test_cross_directory_loading_with_file_tools()` in `tests/integration/test_save_load_anthropic.py`
- Test verifies: Bot with file-based tools can be saved in one directory, loaded from another, and tools remain functional
- Test result: PASSES - confirms cross-directory loading works correctly

**Test Coverage Added**:
- New test fills the gap identified in original report
- Combines file-based tools + cross-directory loading
- Provides regression protection for this functionality

**Conclusion**:
The system already stores full tool source code (not just file paths) and handles cross-directory loading correctly. Bots are truly portable and shareable as designed.

**Priority**: N/A (resolved - not a bug)

**Effort**: N/A (no fix needed, test added for coverage)
---



## 36. branch_self Loses Track of Branching Node - DONE ✅

**Status**: RESOLVED (PR #119, 08-Oct-2025) - VERIFIED (09-Oct-2025)

**Issue**: When using branch_self with multiple prompts, branches lose track of which node they branched from during save/load operations. Branches execute incorrect prompts or get confused about their original task.

**Root Cause Identified**: Bot.load() was using replies[0] (oldest branch) instead of replies[-1] (most recent). When branch_self saved/loaded bot state, it would incorrectly position at an old branch from previous operations.

**Fix Delivered in PR #119**:
- Changed Bot.load() from replies[0] to replies[-1] (line 2542 in base.py)
- This fix directly addresses the root cause of the branching node tracking issue

**Verification (WO014, 09-Oct-2025)**:
- Created comprehensive test suite: `tests/e2e/test_branch_self_tracking.py`
- 4 new tests covering save/load scenarios with branch_self
- All tests passing (8/8 branch_self tests total)
- Verified fix works correctly across multiple save/load cycles
- See: `_work_orders/WO014_VERIFICATION_COMPLETE.md` for full details

**Mechanism**:
```
Conversation Tree:
    Root
    ├─ Old Branch A (replies[0]) ← OLD: Would position here (WRONG!)
    ├─ Old Branch B
    └─ Current Position (replies[-1]) ← NEW: Positions here (CORRECT!)
```

**Related Issues**:
- Issue #118: branch_self tracking bug - CLOSED (verified fixed)
- Issue #117: flaky test - CLOSED (fixed in WO014)

**Priority**: CRITICAL (now resolved)

**Effort**: Verification completed (4-6 hours)
---

## 37. CLI /s Command Bug - DONE

**Status**: DONE (PR #119, 08-Oct-2025) - Closes Issue #115

**Delivered**:
- Added early exit for /s command in CLI (lines 1545-1548 in cli.py)
- /s command now saves without sending any prompt to LLM
- Prevents wasted API calls and confusing behavior

**Original Issue**: `/s` command was sending prompts to LLM instead of just saving

**Fix**: Implemented early exit pattern that handles /s immediately and skips message sending logic

---

## 38. Flaky Test - test_branch_self_error_handling - DONE ✅
**Status**: RESOLVED (PR #120, 09-Oct-2025) - Closed Issue #117
**Issue**: Test `test_branch_self_error_handling` was flaky/unreliable due to vague prompts causing non-deterministic LLM behavior.
**Root Cause**: Test used vague prompt "use invalid parameters" which LLM interpreted differently each time.
**Fix Delivered in PR #120**:
- Rewrote test to use MockBot for deterministic behavior
- Made prompts more specific and explicit
- Test now passes consistently
**Verification (WO014, 09-Oct-2025)**:
- Test verified stable across multiple runs
- No longer depends on LLM interpretation
- 100% confidence in fix
**Priority**: RESOLVED
**Effort**: LOW (completed)

---

## Implementation Roadmap

### Phase 1: Repo Reliability & Critical Fixes (High Priority)
1. [DONE] **branch_self Loses Track of Branching Node** (item 36) - RESOLVED (PR #119, 08-Oct-2025) ✅
   - Fix delivered: Bot.load() now uses replies[-1] instead of replies[0]
   - VERIFIED (WO014, 09-Oct-2025): All tests passing
   - Comprehensive test suite created
   - Issues #118 and #117 closed

2. [DONE] **Cross-Directory Bot Loading** (item 35) - RESOLVED (07-Oct-2025)
   - Investigation confirmed: NOT A BUG
   - System already stores full source code
   - Test added for regression protection

3. [DONE] **Improve Save/Load Behavior** (item 34) - DONE (PR #119, 08-Oct-2025)
   - Fixed replies[0] vs replies[-1] inconsistency
   - Added bot filename tracking for intelligent autosave
   - Separated quicksave from named saves
   - All 4 proposed changes delivered with full test coverage

4. [!] **OpenTelemetry Phases 3-4** (item 14) - PARTIAL
4. [DONE] **OpenTelemetry Integration** (item 14) - DONE (WO015, 10-Oct-2025) ✅
   - All 4 phases complete: Tracing, Logging, Metrics, Production Observability
   - 176 observability tests, 173 passing (98.3%)

5. [DONE] **Callback System** (item 12) - DONE (WO015, 10-Oct-2025) ✅
   - Complete callback infrastructure (BotCallbacks, OpenTelemetryCallbacks, ProgressCallbacks)
   - Full integration with all bot providers

   - Shell abstraction layer
   - Bash/sh support for terminal tools
   - Blocks Unix/Mac users

7. [...] **Multi-OS Testing Infrastructure** (item 30) - HIGH
   - CI/CD matrix for Windows, Linux, macOS
   - Enables validation of Unix compatibility
   - Foundation for cross-platform support

8. [...] **Refactor build_messages pattern** (item 8)
   - Clean architecture before adding complexity

9. [...] **Ensure CLI haiku bots match provider** (item 5)
   - Quick win, cost optimization

**Completed Phase 1 Items**:
- [DONE] GitHub Branch Protection & CodeRabbit (item 26)
- [DONE] OpenTelemetry Phases 1-2 (item 14)
- [DONE] Remove print statements (item 11)
- [DONE] Fix test parallelism (item 24)
- [DONE] Uniform tempfile handling (item 25)
- [DONE] Organize tests better (item 9)

### Phase 2: Core Features & Expansion (Medium Priority)
1. **MCP Integration - Client** (item 13) - Industry standard for tool connectivity
2. **MCP Integration - Server** (item 13) - Expose tools to ecosystem
3. **LiteLLM Integration** (item 15) - 100+ provider support
4. **Functional Prompts on Specific Branches** (item 33) - MEDIUM-HIGH
   - Low effort, high value feature
   - Enables sophisticated multi-branch workflows
5. **Repository-Level Tools** (item 32) - MEDIUM
   - Phase 1: Basic repository context
   - Enables sophisticated development workflows
6. Configure CLI more thoroughly (item 6)
7. Update base.py to use config file
8. Centralized file-writing wrapper (item 16)
9. Bot requirements system (item 18)
10. Expand self_tools Phase 1 (item 10)
11. python_edit feedback improvements (item 20)

### Phase 3: Enhancement & User Experience (Medium-Low Priority)
1. **Tutorial Expansion** (item 27) - MEDIUM-HIGH
   - Critical for onboarding and adoption
   - 7 new tutorials needed
2. **CHATME.bot** (item 28) - MEDIUM
   - Welcome bot for new users
   - Low effort, good UX improvement
3. **.bot File Association** (item 31) - MEDIUM
   - Quality of life improvement
   - Cross-platform file associations
4. Make CLI prettier (item 2) - Integrate with OpenTelemetry for progress
5. Expand self_tools Phase 2-3 (item 10)
6. Rename auto_stash to mustache (item 4)
7. Tool requirements decorator (item 17)
8. Autosave behavior improvements (item 21)
9. Terminal tool output format (item 22)
10. AST warnings cleanup (item 19)

### Phase 4: Major Features (Low Priority, High Effort)
1. JavaScript GUI / Frontend backend (item 3)
2. Conversation tree visualization tools
3. Repository-Level Tools Phases 2-3 (item 32)
4. Tool configurations in CI/CD (item 23)
5. Integration with emerging standards (OASF, ACP)

---

## Next Actions

**Strategic Priority**: Documentation-First Revenue Path

### Immediate (Weeks 1-2)
1. **Complete OpenTelemetry Phases 3-4** (item 14)
   - Implement metrics collection
   - Set up production observability
   - Track cost per operation
   - **Why**: Essential for pricing and proving competitive advantage

2. **Complete Callback System** (item 12)
   - Implement callback interface
   - Add progress indicators
   - Integrate with OpenTelemetry
   - **Why**: Better user experience, foundation for prettier CLI

### Short-term (Weeks 3-8)
1. **Build GitHub Integration** (item 27)
   - Create GitHub App
   - Implement webhook handling
   - Repository access and cloning

2. **Build Documentation Output System** (item 28)
   - Markdown generation from conversation trees
   - HTML/static site generation
   - Template system

3. **Build Automated Workflow** (item 29)
   - Scheduled and commit-triggered generation
   - Quality checks
   - Deployment automation

### Medium-term (Weeks 9-20)
1. **Launch Documentation Service MVP** (items 30-32)
   - Authentication and billing
   - Multi-tenancy
   - Dashboard and hosting
   - **Target**: First 10 paying customers

2. **Optimize and Scale**
   - Prove n*log(n) scaling advantage with metrics
   - Reduce costs and generation time
   - Improve quality and reliability

### Long-term (Month 6+)
1. **Fund GUI Development** with documentation service revenue
2. **Launch Code Review Service** (leverage same infrastructure)
3. **Build API Service** (expose conversation trees)
4. **Create Bot Marketplace** (sell specialized bots)


---

**Last Updated**: 10-Oct-2025
**Maintainer**: Ben Rinauto
**Status**: Active Planning
---

## Roadmap Maintenance Notes

**Purpose**: Guidelines for maintaining this roadmap document

### Formatting Rules

1. **ASCII Only**: No emojis or unicode characters (use "DONE", "PARTIAL", "IN PROGRESS" instead of checkmarks)
2. **Date Format**: Use DD-MON-YYYY (e.g., 06-Oct-2025) for unambiguous international dates
3. **Status Markers**: Use clear text markers at end of item titles:
   - `DONE` - Fully complete, all scope delivered
   - `PARTIAL` - Some work complete, significant work remains
   - `IN PROGRESS` - Currently being worked on
   - No marker - Not started

### Verification Process

When marking items complete based on PRs:

1. **Read the full roadmap item** - Understand complete scope, not just title
2. **Review PR deliverables** - What was actually delivered?
3. **Compare scope vs. delivery** - Does PR cover ALL aspects of roadmap item?
4. **Check sub-items** - If item has phases/steps, are ALL complete?
5. **Mark appropriately**:
   - DONE only if 100% of scope delivered
   - PARTIAL if significant work remains
   - Add notes explaining what's done vs. what remains

### Update Procedures

**When to Update**:
- After PRs are merged that complete roadmap items
- When new development directions emerge
- When priorities shift
- At least monthly review

**What to Update**:
- Status markers on completed items
- "Last Updated" date at bottom of file
- Add new items as needed
- Update Implementation Roadmap phases
- Add notes about partial completion

**How to Document Completed Items**:
```
## N. Item Title - DONE

**Status**: DONE (PR #XXX, DD-MON-YYYY)

**Delivered**:
- Specific deliverable 1
- Specific deliverable 2
- Specific deliverable 3

**Original Goal**: [keep original goal text]
```

### Maintenance Workflow

1. Review recent merged PRs
2. For each PR, identify related roadmap items
3. Verify completeness against full item scope
4. Update status markers and add completion notes
5. Update "Last Updated" date
6. Commit changes with clear message: "docs: Update ROADMAP.md - mark items X, Y, Z complete"

---
