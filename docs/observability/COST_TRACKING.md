# Cost Tracking Guide

Complete guide for tracking and optimizing LLM API costs using the bots framework.

## Table of Contents

- [Overview](#overview)
- [How Cost Calculation Works](#how-cost-calculation-works)
- [Pricing Data](#pricing-data)
- [Tracking Costs](#tracking-costs)
- [Querying Cost Metrics](#querying-cost-metrics)
- [Dashboard Setup](#dashboard-setup)
- [Cost Optimization](#cost-optimization)
- [Provider-Specific Details](#provider-specific-details)

---

## Overview

The bots framework includes built-in cost tracking for all LLM API calls. Costs are calculated based on:

- **Token usage** (input and output tokens)
- **Model pricing** (per million tokens)
- **Special features** (caching, batch API)
- **Provider** (Anthropic, OpenAI, Google)

**Key Features:**

- ✅ Automatic cost calculation for every API call
- ✅ Real-time cost metrics via OpenTelemetry
- ✅ Support for caching discounts (up to 90% savings)
- ✅ Support for batch API discounts (50% savings)
- ✅ Accurate pricing data (updated October 2025)

---

## How Cost Calculation Works

### Basic Formula

```
cost = (input_tokens / 1_000_000) * input_price + 
       (output_tokens / 1_000_000) * output_price
```

### Cache Discounts by Provider

| Provider | Cache Discount | Savings |
|----------|---------------|---------||
| Anthropic | 90% | $3.00 → $0.30 per 1M tokens |
| OpenAI | 50% | $3.00 → $1.50 per 1M tokens |
| Google | 75% | $1.25 → $0.31 per 1M tokens |

### Batch API Discounts

All providers offer 50% discount for batch API usage.

---

## Pricing Data

### Current Pricing (as of October 2025)

All prices are per 1 million tokens.

#### Anthropic (Claude)

| Model | Input | Output | Cache Discount |
|-------|-------|--------|----------------|
| claude-3-5-sonnet-latest | $3.00 | $15.00 | 90% |
| claude-3-5-haiku-latest | $0.80 | $4.00 | 90% |
| claude-3-haiku-20240307 | $0.25 | $1.25 | 90% |
| claude-3-opus-20240229 | $15.00 | $75.00 | 90% |
| claude-opus-4-latest | $20.00 | $80.00 | 90% |
| claude-sonnet-4-latest | $5.00 | $25.00 | 90% |

#### OpenAI (GPT)

| Model | Input | Output | Cache Discount |
|-------|-------|--------|----------------|
| gpt-4o | $3.00 | $10.00 | 50% |
| gpt-4o-mini | $0.15 | $0.60 | 50% |
| gpt-4-turbo | $10.00 | $30.00 | 50% |
| gpt-4 | $30.00 | $60.00 | 50% |
| gpt-3.5-turbo | $0.50 | $1.50 | 50% |

#### Google (Gemini)

| Model | Input | Output | Cache Discount |
|-------|-------|--------|----------------|
| gemini-2.5-pro | $1.25 | $10.00 | 75% |
| gemini-2.5-flash | $0.30 | $2.50 | 75% |
| gemini-2.0-flash | $0.15 | $0.60 | 75% |
| gemini-1.5-pro | $1.25 | $10.00 | 75% |
| gemini-1.5-flash | $0.30 | $2.50 | 75% |

---

## Tracking Costs

### Automatic Tracking

Costs are automatically tracked when observability is enabled:

```python
from bots import AnthropicBot

# Costs tracked automatically
bot = AnthropicBot()
response = bot.respond("Write a short story")
# Cost metrics recorded to OpenTelemetry
```

### Manual Cost Calculation

```python
from bots.observability.cost_calculator import calculate_cost

cost = calculate_cost(
    provider="anthropic",
    model="claude-3-5-sonnet-latest",
    input_tokens=10_000,
    output_tokens=5_000
)
print(f"Estimated cost: ${cost:.4f}")
# Output: Estimated cost: $0.1050
```

---

## Querying Cost Metrics

### Metric Names

- `bot.cost_usd` - Histogram of individual costs
- `bot.cost_total_usd` - Counter of cumulative costs

### Prometheus/Grafana Queries

**Total cost in last hour:**

```promql
sum(rate(bot_cost_total_usd[1h])) * 3600
```

**Cost by provider:**

```promql
sum by (provider) (rate(bot_cost_total_usd[5m]))
```

**Average cost per API call:**

```promql
rate(bot_cost_total_usd[5m]) / rate(bot_api_calls_total[5m])
```

---

## Dashboard Setup

### Quick Start

For complete dashboard examples with importable JSON templates, see [DASHBOARDS.md](DASHBOARDS.md).

### Essential Panels

#### Total Cost (Today)

```promql
sum(increase(bot_cost_total_usd[24h]))
```

**Panel type:** Stat | **Unit:** USD ($)

#### Cost Rate (per minute)

```promql
sum(rate(bot_cost_total_usd[5m])) * 60
```

**Panel type:** Graph | **Unit:** USD/min

#### Cost by Provider

```promql
sum by (provider) (increase(bot_cost_total_usd[1h]))
```

**Panel type:** Pie chart | **Unit:** USD ($)

### Alert Rules

```yaml
groups:
  - name: cost_alerts
    rules:
      - alert: HighCostRate
        expr: rate(bot_cost_total_usd[5m]) * 60 > 1.0
        for: 5m
        annotations:
          summary: "High cost rate detected"
```

For more alert examples, see the [SETUP.md alerting section](SETUP.md#alerting).

---

## Cost Analysis Queries

### Advanced Prometheus Queries

#### Cost Breakdown by Model

```promql
sum by (model) (increase(bot_cost_total_usd[24h]))
```

**Use case:** Identify which models are driving costs

#### Cost Efficiency (Cost per Token)

```promql
increase(bot_cost_total_usd[1h]) / 
  (increase(bot_tokens_used{token_type="input"}[1h]) + 
   increase(bot_tokens_used{token_type="output"}[1h]))
```

**Use case:** Compare actual cost efficiency across providers

#### Hourly Cost Trend

```promql
sum(increase(bot_cost_total_usd[1h]))
```

**Use case:** Identify peak usage hours for cost optimization

#### Cost per Conversation

```promql
increase(bot_cost_total_usd[24h]) / increase(bot_api_calls_total[24h])
```

**Use case:** Track average conversation cost over time

#### Cache Effectiveness (Cost Savings)

```promql
# Estimated savings from caching
sum(rate(bot_tokens_used{token_type="cached"}[5m])) * 0.0000027  # Anthropic cache savings ($2.70 per 1M tokens = $0.0000027 per token)
```

**Use case:** Measure ROI of prompt caching

#### Provider Cost Comparison

```promql
topk(3, sum by (provider) (increase(bot_cost_total_usd[7d])))
```

**Use case:** Weekly cost comparison across providers

### Cost Anomaly Detection

#### Sudden Cost Spike

```promql
(rate(bot_cost_total_usd[5m]) - rate(bot_cost_total_usd[5m] offset 1h)) > 0.5
```

**Alert threshold:** Cost rate increased by $0.50/min

#### Unusual Model Usage

```promql
sum by (model) (rate(bot_api_calls_total[5m])) > 10
```

**Alert threshold:** More than 10 calls/min to expensive models

### Budget Tracking

#### Daily Budget Burn Rate

```promql
sum(increase(bot_cost_total_usd[24h])) / 10.0  # Assuming $10 daily budget
```

**Use case:** Track percentage of daily budget consumed

#### Projected Monthly Cost

```promql
sum(increase(bot_cost_total_usd[24h])) * 30
```

**Use case:** Forecast monthly costs based on current usage

### Dashboard Integration

All these queries can be visualized in Grafana. See [DASHBOARDS.md](DASHBOARDS.md) for:

- Pre-built dashboard JSON templates
- Panel configuration examples
- Visualization best practices
- Cost tracking dashboard screenshots

---

## Cost Optimization

### 1. Use Smaller Models

**Cost comparison for 1M input + 500K output tokens:**

| Model | Cost | Use Case |
|-------|------|----------|
| claude-3-5-haiku | $2.80 | Simple tasks, high volume |
| claude-3-5-sonnet | $10.50 | Balanced performance |
| claude-opus-4 | $60.00 | Complex reasoning |
| gpt-4o-mini | $0.45 | Simple tasks, cost-sensitive |
| gpt-4o | $8.00 | General purpose |

### 2. Leverage Caching

Prompt caching can save up to 90% on repeated input:

```python
bot = AnthropicBot()

# First call - no cache (full cost)
response1 = bot.respond("Analyze this document...")
# Cost: $3.00 for 1M input tokens

# Second call - 90% cached
response2 = bot.respond("Now summarize the key points")
# Cost: $0.30 for 1M cached tokens
# Savings: $2.70 (90%)
```

**Best practices:**

- ✅ Reuse conversation context
- ✅ Keep system prompts consistent
- ✅ Use long-lived bot instances

**Monitoring cache effectiveness:**

```promql
# Cache hit rate
sum(rate(bot_tokens_used{token_type="cached"}[5m])) / 
  sum(rate(bot_tokens_used{token_type="input"}[5m]))
```

### 3. Use Batch API

50% discount for non-urgent requests (24-hour turnaround).

**Cost comparison:**

- Real-time API: $3.00/1M input tokens
- Batch API: $1.50/1M input tokens
- **Savings: 50%**

### 4. Optimize Token Usage

**Reduce input tokens:**

```python
# Bad: Verbose prompt (1000 tokens)
prompt = "Please analyze the following code..."

# Good: Concise prompt (200 tokens)
prompt = "Analyze this code and explain key functions:"
```

**Limit output tokens:**

```python
bot = AnthropicBot(max_tokens=500)  # Limit output length
```

**Monitor token efficiency:**

```promql
# Average tokens per API call
rate(bot_tokens_used[5m]) / rate(bot_api_calls_total[5m])
```

### 5. Cost-Aware Model Selection

```python
from bots import AnthropicBot
from bots.foundation.base import Engines

def get_bot_for_task(complexity):
    if complexity == "simple":
        return AnthropicBot(model_engine=Engines.CLAUDE_3_5_HAIKU)
    elif complexity == "medium":
        return AnthropicBot(model_engine=Engines.CLAUDE_3_5_SONNET)
    else:
        return AnthropicBot(model_engine=Engines.CLAUDE_OPUS_4)
```

**Track model selection effectiveness:**

```promql
# Cost per model
sum by (model) (rate(bot_cost_total_usd[1h]))
```

---

### 6. Set Cost Budgets and Alerts

**Daily budget alert:**

```yaml
- alert: DailyBudgetExceeded
  expr: sum(increase(bot_cost_total_usd[24h])) > 10.0
  annotations:
    summary: "Daily cost budget of $10 exceeded"
```

**Per-conversation cost alert:**

```yaml
- alert: ExpensiveConversation
  expr: bot_cost_usd > 1.0
  annotations:
    summary: "Single conversation cost exceeded $1"
```

---

## Provider-Specific Details

### Anthropic

**Best for cost optimization:**

- ✅ Highest cache discount (90%)
- ✅ Competitive pricing on Sonnet models
- ✅ Haiku is extremely cost-effective

**Cost tracking:**

```python
from bots import AnthropicBot
from bots.observability.cost_calculator import calculate_cost

bot = AnthropicBot()
response = bot.respond("Hello")

cost = calculate_cost(
    provider="anthropic",
    model=bot.model_engine.value,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens
)
```

### OpenAI

**Best for:**

- ✅ GPT-4o-mini is cheapest option ($0.15/$0.60)
- ✅ Good balance of cost and performance

### Google (Gemini)

**Best for:**

- ✅ Gemini 2.0 Flash is very cost-effective ($0.15/$0.60)
- ✅ Good cache discount (75%)
- ✅ Long context windows

---

## Real-World Examples

### Example 1: Documentation Generation

**Task:** Generate documentation for 100 Python files

```python
from bots import AnthropicBot
from bots.foundation.base import Engines

# Use Haiku for cost efficiency
bot = AnthropicBot(model_engine=Engines.CLAUDE_3_5_HAIKU)

total_cost = 0
for file in python_files:
    response = bot.respond(f"Document this code: {file.read()}")
    total_cost += 0.01  # Approximate cost per file

print(f"Total cost: ${total_cost:.2f}")
# Output: Total cost: $1.00
```

**Cost comparison:**

| Model | Cost per file | Total (100 files) |
|-------|--------------|-------------------|
| Haiku | $0.01 | $1.00 |
| Sonnet | $0.04 | $4.00 |
| Opus | $0.20 | $20.00 |

### Example 2: Customer Support Bot

**Task:** Handle 1000 support queries per day

```python
bot = AnthropicBot()

# First query - full cost
response = bot.respond("How do I reset my password?")
# Cost: $0.003

# Subsequent queries - 90% cached
for query in queries:
    response = bot.respond(query)
    # Cost: ~$0.0003 (90% cached)

# Daily cost: $0.30
# Monthly cost: $9.00 (vs $90 without caching)
```

### Example 3: Code Review Service

**Task:** Review 50 PRs per day

```python
bot = AnthropicBot(model_engine=Engines.CLAUDE_3_5_SONNET)

for pr in pull_requests:
    response = bot.respond(f"Review this code: {pr.diff}")
    # Cost per review: $0.05

# Daily cost: $2.50
# Monthly cost: $75
```

**Optimization:** Use Haiku for simple PRs, Sonnet for complex ones

- **Savings:** ~40% ($45/month)

---

## Next Steps

- [Dashboard Examples](DASHBOARDS.md) - Pre-built Grafana dashboards and templates
- [Setup Guide](SETUP.md) - Configure OpenTelemetry exporters and alerting
- [Callbacks Guide](CALLBACKS.md) - Implement custom callbacks for cost tracking

---

**Last Updated**: October 2025
**Pricing Data**: October 2025
