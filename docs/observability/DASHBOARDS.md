# Dashboard Guide

Complete guide for visualizing bots framework metrics with Grafana and other tools.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Grafana Setup](#grafana-setup)
- [Connecting Data Sources](#connecting-data-sources)
- [Prometheus Queries](#prometheus-queries)
- [Cost Tracking Dashboard](#cost-tracking-dashboard)
- [Performance Dashboard](#performance-dashboard)
- [Error Tracking Dashboard](#error-tracking-dashboard)
- [Best Practices](#best-practices)

---

## Overview

The bots framework provides comprehensive metrics through OpenTelemetry that can be visualized in dashboards. This guide shows you how to set up and use these dashboards for:

**Cost Monitoring:**

- Track spending per provider (Anthropic, OpenAI, Google)
- Monitor cost per model and operation
- Identify cost optimization opportunities
- Set budget alerts

**Performance Monitoring:**

- Response time tracking (p50, p95, p99 percentiles)
- API call latency analysis
- Tool execution performance
- Bottleneck identification

**Error Tracking:**

- Error rates by provider and type
- Tool failure monitoring
- Alert on anomalies
- Root cause analysis

**Usage Analytics:**

- API call volumes
- Token consumption trends
- Tool usage patterns
- Conversation metrics

### Available Metrics

The bots framework exposes 11 OpenTelemetry metrics:

**Performance Metrics (Histograms):**

- `bot.response_time` - Total time for bot.respond()
- `bot.api_call_duration` - Time spent in API calls
- `bot.tool_execution_duration` - Time executing tools
- `bot.message_building_duration` - Time building messages

**Usage Metrics (Counters):**

- `bot.api_calls_total` - Count of API calls
- `bot.tool_calls_total` - Count of tool executions
- `bot.tokens_used` - Token usage (input/output)

**Cost Metrics:**

- `bot.cost_usd` - Cost per operation (histogram)
- `bot.cost_total_usd` - Cumulative cost (counter)

**Error Metrics (Counters):**

- `bot.errors_total` - Count of errors
- `bot.tool_failures_total` - Count of tool failures

### Metric Attributes

All metrics include relevant attributes for filtering and grouping:

- `provider` - LLM provider (anthropic, openai, google)
- `model` - Model name (e.g., claude-3-5-sonnet-latest)
- `tool_name` - Name of tool being executed
- `token_type` - Type of tokens (input, output)
- `status` - Operation status (success, error, timeout)
- `error_type` - Exception class name
- `success` - Boolean success indicator

---

## Prerequisites

Before setting up dashboards, ensure you have:

**1. Metrics Collection Enabled**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_METRICS_ENABLED=true
```

**2. Metrics Exporter Configured**

Choose one of:

- **Prometheus** (recommended for self-hosted)
- **OTLP** (recommended for cloud providers)
- **Console** (development only)

**3. Required Software**

- Grafana (v9.0+)
- Prometheus (v2.30+) OR OpenTelemetry Collector
- Docker (optional, for easy setup)

**4. Network Access**

- Grafana can reach your metrics backend
- Metrics backend can scrape/receive from your application

---

## Grafana Setup

### Option 1: Docker Compose (Recommended)

The easiest way to get started is with Docker Compose:

**1. Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8889:8889"   # Prometheus metrics
    volumes:
      - ./otel-collector-config.yml:/etc/otel-collector-config.yml
    command: ["--config=/etc/otel-collector-config.yml"]

volumes:
  prometheus-data:
  grafana-data:
```

**2. Create `prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'bots-framework'
    static_configs:
      - targets: ['host.docker.internal:8889']  # OTel Collector metrics endpoint
        labels:
          service: 'bots'
```

**3. Create `otel-collector-config.yml`:**

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: bots
    const_labels:
      service: bots-framework

  logging:
    loglevel: debug

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
```

**4. Start the stack:**

```bash
docker-compose up -d
```

**5. Verify services:**

- Grafana: <http://localhost:3000> (admin/admin)
- Prometheus: <http://localhost:9090>
- OTel Collector: <http://localhost:4317>

### Option 2: Manual Installation

**1. Install Grafana:**

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# macOS
brew install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

**2. Install Prometheus:**

```bash
# Ubuntu/Debian
sudo apt-get install prometheus

# macOS
brew install prometheus

# Start Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

**3. Install OpenTelemetry Collector:**

```bash
# Download latest release
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.88.0/otelcol-contrib_0.88.0_linux_amd64.tar.gz

# Extract
tar -xvf otelcol-contrib_0.88.0_linux_amd64.tar.gz

# Run with config
./otelcol-contrib --config=otel-collector-config.yml
```

---

## Connecting Data Sources

### Add Prometheus Data Source to Grafana

**1. Open Grafana** (<http://localhost:3000>)

**2. Navigate to Configuration > Data Sources**

**3. Click "Add data source"**

**4. Select "Prometheus"**

**5. Configure:**

```
Name: Prometheus
URL: http://prometheus:9090  (Docker) or http://localhost:9090 (local)
Access: Server (default)
```

**6. Click "Save & Test"**

You should see: "Data source is working"

### Configure Your Bot Application

**Set environment variables:**

```bash
# Enable metrics
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_METRICS_ENABLED=true

# Use OTLP exporter
export BOTS_OTEL_EXPORTER_TYPE=otlp
export BOTS_OTEL_OTLP_ENDPOINT=http://localhost:4317
```

**Run your bot:**

```python
from bots import AnthropicBot

bot = AnthropicBot()
response = bot.respond("Hello!")
```

**Verify metrics in Prometheus:**

1. Open <http://localhost:9090>
2. Go to Graph tab
3. Enter query: `bots_bot_api_calls_total`
4. Click Execute

You should see your metrics!

### Troubleshooting Connection Issues

**Metrics not appearing in Prometheus?**

1. Check OTel Collector logs:

   ```bash
   docker logs otel-collector
   ```

2. Verify metrics endpoint:

   ```bash
   curl http://localhost:8889/metrics
   ```

3. Check Prometheus targets:
   - Open <http://localhost:9090/targets>
   - Ensure target is "UP"

**Grafana can't connect to Prometheus?**

1. Verify Prometheus is running:

   ```bash
   curl http://localhost:9090/-/healthy
   ```

2. Check network connectivity (Docker networks)

3. Try using IP address instead of hostname

**No data in Grafana panels?**

1. Check time range (top right)
2. Verify query syntax in panel editor
3. Check metric names match (use Metrics Explorer)
4. Ensure bot application is running and generating metrics

---

## Prometheus Query Examples

This section provides ready-to-use PromQL queries for all metrics in the bots framework.

### Performance Metrics (Histograms)

#### 1. Response Time (bot.response_time)

**Average response time by provider:**

```promql
rate(bot_response_time_sum[5m]) / rate(bot_response_time_count[5m])
```

**95th percentile response time:**

```promql
histogram_quantile(0.95, rate(bot_response_time_bucket[5m]))
```

**Response time by provider and model:**

```promql
rate(bot_response_time_sum{provider="anthropic"}[5m]) / rate(bot_response_time_count{provider="anthropic"}[5m])
```

**Response time percentiles (p50, p95, p99):**

```promql
# p50
histogram_quantile(0.50, rate(bot_response_time_bucket[5m]))

# p95
histogram_quantile(0.95, rate(bot_response_time_bucket[5m]))

# p99
histogram_quantile(0.99, rate(bot_response_time_bucket[5m]))
```

**Successful vs failed response times:**

```promql
# Successful
rate(bot_response_time_sum{success="true"}[5m]) / rate(bot_response_time_count{success="true"}[5m])

# Failed
rate(bot_response_time_sum{success="false"}[5m]) / rate(bot_response_time_count{success="false"}[5m])
```

---

#### 2. API Call Duration (bot.api_call_duration)

**Average API call duration:**

```promql
rate(bot_api_call_duration_sum[5m]) / rate(bot_api_call_duration_count[5m])
```

**API latency by provider:**

```promql
rate(bot_api_call_duration_sum[5m]) / rate(bot_api_call_duration_count[5m]) by (provider)
```

**API latency by model:**

```promql
rate(bot_api_call_duration_sum[5m]) / rate(bot_api_call_duration_count[5m]) by (model)
```

**95th percentile API latency:**

```promql
histogram_quantile(0.95, rate(bot_api_call_duration_bucket[5m]))
```

**API call duration by status:**

```promql
rate(bot_api_call_duration_sum[5m]) / rate(bot_api_call_duration_count[5m]) by (status)
```

---

#### 3. Tool Execution Duration (bot.tool_execution_duration)

**Average tool execution time:**

```promql
rate(bot_tool_execution_duration_sum[5m]) / rate(bot_tool_execution_duration_count[5m])
```

**Tool execution time by tool name:**

```promql
rate(bot_tool_execution_duration_sum[5m]) / rate(bot_tool_execution_duration_count[5m]) by (tool_name)
```

**Slowest tools (top 5):**

```promql
topk(5, rate(bot_tool_execution_duration_sum[5m]) / rate(bot_tool_execution_duration_count[5m]) by (tool_name))
```

**95th percentile tool execution time:**

```promql
histogram_quantile(0.95, rate(bot_tool_execution_duration_bucket[5m]))
```

**Tool execution time: success vs failure:**

```promql
# Successful
rate(bot_tool_execution_duration_sum{success="true"}[5m]) / rate(bot_tool_execution_duration_count{success="true"}[5m])

# Failed
rate(bot_tool_execution_duration_sum{success="false"}[5m]) / rate(bot_tool_execution_duration_count{success="false"}[5m])
```

---

#### 4. Message Building Duration (bot.message_building_duration)

**Average message building time:**

```promql
rate(bot_message_building_duration_sum[5m]) / rate(bot_message_building_duration_count[5m])
```

**Message building time by provider:**

```promql
rate(bot_message_building_duration_sum[5m]) / rate(bot_message_building_duration_count[5m]) by (provider)
```

**95th percentile message building time:**

```promql
histogram_quantile(0.95, rate(bot_message_building_duration_bucket[5m]))
```

---

### Usage Metrics (Counters)

#### 5. API Calls Total (bot.api_calls_total)

**API calls per second:**

```promql
rate(bot_api_calls_total[5m])
```

**API calls per second by provider:**

```promql
rate(bot_api_calls_total[5m]) by (provider)
```

**API calls per second by model:**

```promql
rate(bot_api_calls_total[5m]) by (model)
```

**Total API calls in last hour:**

```promql
increase(bot_api_calls_total[1h])
```

**API call success rate:**

```promql
rate(bot_api_calls_total{status="success"}[5m]) / rate(bot_api_calls_total[5m])
```

**Most used models (top 5):**

```promql
topk(5, rate(bot_api_calls_total[5m]) by (model))
```

---

#### 6. Tool Calls Total (bot.tool_calls_total)

**Tool calls per second:**

```promql
rate(bot_tool_calls_total[5m])
```

**Tool calls by tool name:**

```promql
rate(bot_tool_calls_total[5m]) by (tool_name)
```

**Most used tools (top 10):**

```promql
topk(10, rate(bot_tool_calls_total[5m]) by (tool_name))
```

**Tool success rate:**

```promql
rate(bot_tool_calls_total{success="true"}[5m]) / rate(bot_tool_calls_total[5m])
```

**Total tool calls in last hour:**

```promql
increase(bot_tool_calls_total[1h])
```

---

#### 7. Tokens Used (bot.tokens_used)

**Tokens per second:**

```promql
rate(bot_tokens_used[5m])
```

**Input tokens per second:**

```promql
rate(bot_tokens_used{token_type="input"}[5m])
```

**Output tokens per second:**

```promql
rate(bot_tokens_used{token_type="output"}[5m])
```

**Tokens by provider:**

```promql
rate(bot_tokens_used[5m]) by (provider)
```

**Tokens by model:**

```promql
rate(bot_tokens_used[5m]) by (model)
```

**Total tokens in last hour:**

```promql
increase(bot_tokens_used[1h])
```

**Input/output token ratio:**

```promql
rate(bot_tokens_used{token_type="output"}[5m]) / rate(bot_tokens_used{token_type="input"}[5m])
```

**Most token-intensive models:**

```promql
topk(5, rate(bot_tokens_used[5m]) by (model))
```

---

### Cost Metrics

#### 8. Cost USD (bot.cost_usd - Histogram)

**Average cost per operation:**

```promql
rate(bot_cost_usd_sum[5m]) / rate(bot_cost_usd_count[5m])
```

**Cost per operation by provider:**

```promql
rate(bot_cost_usd_sum[5m]) / rate(bot_cost_usd_count[5m]) by (provider)
```

**Cost per operation by model:**

```promql
rate(bot_cost_usd_sum[5m]) / rate(bot_cost_usd_count[5m]) by (model)
```

**95th percentile cost per operation:**

```promql
histogram_quantile(0.95, rate(bot_cost_usd_bucket[5m]))
```

**Most expensive models:**

```promql
topk(5, rate(bot_cost_usd_sum[5m]) / rate(bot_cost_usd_count[5m]) by (model))
```

---

#### 9. Cost Total USD (bot.cost_total_usd - Counter)

**Cost per second:**

```promql
rate(bot_cost_total_usd[5m])
```

**Cost per minute:**

```promql
rate(bot_cost_total_usd[5m]) * 60
```

**Cost per hour:**

```promql
rate(bot_cost_total_usd[5m]) * 3600
```

**Projected daily cost:**

```promql
rate(bot_cost_total_usd[5m]) * 86400
```

**Projected monthly cost:**

```promql
rate(bot_cost_total_usd[5m]) * 2592000
```

**Total cost in last hour:**

```promql
increase(bot_cost_total_usd[1h])
```

**Total cost in last 24 hours:**

```promql
increase(bot_cost_total_usd[24h])
```

**Cost by provider:**

```promql
rate(bot_cost_total_usd[5m]) by (provider)
```

**Cost by model:**

```promql
rate(bot_cost_total_usd[5m]) by (model)
```

**Cost breakdown (percentage by provider):**

```promql
(rate(bot_cost_total_usd[5m]) by (provider) / ignoring(provider) group_left sum(rate(bot_cost_total_usd[5m]))) * 100
```

---

### Error Metrics

#### 10. Errors Total (bot.errors_total)

**Error rate (errors per second):**

```promql
rate(bot_errors_total[5m])
```

**Error rate by provider:**

```promql
rate(bot_errors_total[5m]) by (provider)
```

**Error rate by error type:**

```promql
rate(bot_errors_total[5m]) by (error_type)
```

**Error rate by operation:**

```promql
rate(bot_errors_total[5m]) by (operation)
```

**Most common errors (top 5):**

```promql
topk(5, rate(bot_errors_total[5m]) by (error_type))
```

**Total errors in last hour:**

```promql
increase(bot_errors_total[1h])
```

**Error percentage (errors / total operations):**

```promql
(rate(bot_errors_total[5m]) / rate(bot_api_calls_total[5m])) * 100
```

---

#### 11. Tool Failures Total (bot.tool_failures_total)

**Tool failure rate:**

```promql
rate(bot_tool_failures_total[5m])
```

**Tool failures by tool name:**

```promql
rate(bot_tool_failures_total[5m]) by (tool_name)
```

**Tool failures by error type:**

```promql
rate(bot_tool_failures_total[5m]) by (error_type)
```

**Most problematic tools (top 5):**

```promql
topk(5, rate(bot_tool_failures_total[5m]) by (tool_name))
```

**Tool failure percentage:**

```promql
(rate(bot_tool_failures_total[5m]) / rate(bot_tool_calls_total[5m])) * 100
```

**Total tool failures in last hour:**

```promql
increase(bot_tool_failures_total[1h])
```

---

### Composite Queries

**Cost per 1000 API calls:**

```promql
(rate(bot_cost_total_usd[5m]) / rate(bot_api_calls_total[5m])) * 1000
```

**Cost per million tokens:**

```promql
(rate(bot_cost_total_usd[5m]) / rate(bot_tokens_used[5m])) * 1000000
```

**Average tokens per API call:**

```promql
rate(bot_tokens_used[5m]) / rate(bot_api_calls_total[5m])
```

**Tool usage percentage:**

```promql
(rate(bot_tool_calls_total[5m]) / rate(bot_api_calls_total[5m])) * 100
```

**API call efficiency (successful calls / total calls):**

```promql
rate(bot_api_calls_total{status="success"}[5m]) / rate(bot_api_calls_total[5m])
```

**Cost efficiency by provider (cost per successful call):**

```promql
rate(bot_cost_total_usd[5m]) by (provider) / rate(bot_api_calls_total{status="success"}[5m]) by (provider)
```

---

### Time Range Variations

All queries above use `[5m]` as the time range. You can adjust this based on your needs:

- `[1m]` - 1 minute (high resolution, more noise)
- `[5m]` - 5 minutes (recommended default)
- `[15m]` - 15 minutes (smoother, less responsive)
- `[1h]` - 1 hour (long-term trends)
- `[24h]` - 24 hours (daily patterns)

**Example with different time ranges:**

```promql
# High resolution (1 minute)
rate(bot_cost_total_usd[1m])

# Default (5 minutes)
rate(bot_cost_total_usd[5m])

# Smooth trends (1 hour)
rate(bot_cost_total_usd[1h])
```

---

### Query Tips

1. **Use `rate()` for counters** - Converts cumulative counters to per-second rates
2. **Use `histogram_quantile()` for histograms** - Calculates percentiles (p50, p95, p99)
3. **Use `increase()` for totals** - Shows total increase over a time range
4. **Use `by (label)` for grouping** - Breaks down metrics by dimensions
5. **Use `topk()` for top N** - Shows the highest values
6. **Use `sum()` for aggregation** - Combines metrics across dimensions

---

---

## Performance Dashboard

### Overview

The Performance Dashboard provides real-time monitoring of bot response times, API latency, and tool execution performance. This dashboard helps identify bottlenecks and ensure your bots meet SLA requirements.

**Key Metrics Tracked:**

- Response time percentiles (p50, p95, p99)
- API call duration by provider
- Tool execution times
- Message building duration
- Request rates (API calls, tool calls)

### Dashboard Panels

#### 1. Response Time (p50, p95, p99)

Tracks response time percentiles across all providers and models.

**Alert Configuration:**

- **Threshold:** p99 > 5 seconds
- **Frequency:** Check every 1 minute
- **Action:** Trigger alert when p99 exceeds 5s for 5 minutes

**PromQL Query:**

```promql
# p50
histogram_quantile(0.50, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))

# p95
histogram_quantile(0.95, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))

# p99
histogram_quantile(0.99, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))
```

**Interpretation:**

- **p50 < 2s:** Excellent performance
- **p95 < 4s:** Good performance
- **p99 < 5s:** Acceptable performance
- **p99 > 5s:** Investigation needed

#### 2. API Call Duration by Provider

Compares API latency across different providers (Anthropic, OpenAI, Google).

**PromQL Query:**

```promql
histogram_quantile(0.95, sum(rate(bot_api_call_duration_bucket[5m])) by (le, provider))
```

**Use Cases:**

- Compare provider performance
- Identify slow providers
- Optimize provider selection

#### 3. Tool Execution Duration (Top 10 Tools)

Shows the slowest tools in your system.

**PromQL Query:**

```promql
topk(10, histogram_quantile(0.95, sum(rate(bot_tool_execution_duration_bucket[5m])) by (le, tool_name)))
```

**Use Cases:**

- Identify slow tools for optimization
- Track tool performance over time
- Detect tool performance regressions

#### 4. Message Building Duration

Tracks time spent constructing messages before API calls.

**PromQL Query:**

```promql
histogram_quantile(0.95, sum(rate(bot_message_building_duration_bucket[5m])) by (le, provider, model))
```

**Optimization Tips:**

- High message building time may indicate complex tool schemas
- Consider simplifying tool descriptions
- Cache tool schemas when possible

#### 5. Average Response Time by Model

Single-stat panel showing average response time per model.

**PromQL Query:**

```promql
avg(rate(bot_response_time_sum[5m]) / rate(bot_response_time_count[5m])) by (model)
```

**Color Thresholds:**

- **Green:** < 2 seconds
- **Yellow:** 2-5 seconds
- **Red:** > 5 seconds

#### 6. API Calls per Second

Shows current request rate to LLM APIs.

**PromQL Query:**

```promql
sum(rate(bot_api_calls_total[5m]))
```

**Use Cases:**

- Monitor load patterns
- Capacity planning
- Rate limit monitoring

#### 7. Tool Calls per Second

Shows tool execution rate.

**PromQL Query:**

```promql
sum(rate(bot_tool_calls_total[5m]))
```

#### 8. Response Time Heatmap

Visualizes response time distribution over time.

**PromQL Query:**

```promql
sum(rate(bot_response_time_bucket[5m])) by (le)
```

**Interpretation:**

- **Horizontal bands:** Consistent performance
- **Vertical spikes:** Performance degradation events
- **Color intensity:** Request volume

### Alert Rules

#### Critical: High Response Time

```yaml
alert: HighResponseTime
expr: histogram_quantile(0.99, sum(rate(bot_response_time_bucket[5m])) by (le)) > 5
for: 5m
labels:
  severity: critical
annotations:
  summary: "Bot response time p99 is above 5 seconds"
  description: "p99 response time is {{ $value }}s (threshold: 5s)"
```

#### Warning: Slow API Calls

```yaml
alert: SlowAPICalls
expr: histogram_quantile(0.95, sum(rate(bot_api_call_duration_bucket[5m])) by (le, provider)) > 3
for: 10m
labels:
  severity: warning
annotations:
  summary: "API calls to {{ $labels.provider }} are slow"
  description: "p95 API call duration is {{ $value }}s for {{ $labels.provider }}"
```

#### Warning: Slow Tool Execution

```yaml
alert: SlowToolExecution
expr: histogram_quantile(0.95, sum(rate(bot_tool_execution_duration_bucket[5m])) by (le, tool_name)) > 2
for: 10m
labels:
  severity: warning
annotations:
  summary: "Tool {{ $labels.tool_name }} is executing slowly"
  description: "p95 execution time is {{ $value }}s for {{ $labels.tool_name }}"
```

### Dashboard Variables

The dashboard includes template variables for filtering:

**Provider Filter:**

```promql
label_values(bot_api_calls_total, provider)
```

**Model Filter:**

```promql
label_values(bot_api_calls_total{provider=~"$provider"}, model)
```

**Usage:**

- Select specific providers to focus analysis
- Filter by model to compare performance
- Use "All" to see aggregate metrics

### Import Instructions

1. **Copy the dashboard JSON** (see below)
2. **Open Grafana** → Dashboards → Import
3. **Paste JSON** into the import dialog
4. **Select Prometheus datasource**
5. **Click Import**

### Dashboard JSON

```json
{
  "dashboard": {
    "title": "Bots Framework - Performance Monitoring",
    "tags": ["bots", "performance", "opentelemetry"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Response Time (p50, p95, p99)",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))",
            "legendFormat": "p50 - {{provider}}/{{model}}",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))",
            "legendFormat": "p95 - {{provider}}/{{model}}",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(bot_response_time_bucket[5m])) by (le, provider, model))",
            "legendFormat": "p99 - {{provider}}/{{model}}",
            "refId": "C"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Response Time"},
          {"format": "short"}
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {"params": [5], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["C", "5m", "now"]},
              "reducer": {"params": [], "type": "avg"},
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "name": "High Response Time (p99 > 5s)",
          "noDataState": "no_data",
          "notifications": []
        }
      },
      {
        "id": 2,
        "title": "API Call Duration by Provider",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(bot_api_call_duration_bucket[5m])) by (le, provider))",
            "legendFormat": "{{provider}} (p95)",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration"},
          {"format": "short"}
        ]
      },
      {
        "id": 3,
        "title": "Tool Execution Duration (Top 10 Tools)",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "topk(10, histogram_quantile(0.95, sum(rate(bot_tool_execution_duration_bucket[5m])) by (le, tool_name)))",
            "legendFormat": "{{tool_name}} (p95)",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration"},
          {"format": "short"}
        ]
      },
      {
        "id": 4,
        "title": "Message Building Duration",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(bot_message_building_duration_bucket[5m])) by (le, provider, model))",
            "legendFormat": "{{provider}}/{{model}} (p95)",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration"},
          {"format": "short"}
        ]
      },
      {
        "id": 5,
        "title": "Average Response Time by Model",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "avg(rate(bot_response_time_sum[5m]) / rate(bot_response_time_count[5m])) by (model)",
            "legendFormat": "{{model}}",
            "refId": "A"
          }
        ],
        "options": {
          "graphMode": "area",
          "colorMode": "value",
          "orientation": "auto",
          "textMode": "auto"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 2},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "API Calls per Second",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 16},
        "targets": [
          {
            "expr": "sum(rate(bot_api_calls_total[5m]))",
            "legendFormat": "Total",
            "refId": "A"
          }
        ],
        "options": {
          "graphMode": "area",
          "colorMode": "value"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "id": 7,
        "title": "Tool Calls per Second",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "sum(rate(bot_tool_calls_total[5m]))",
            "legendFormat": "Total",
            "refId": "A"
          }
        ],
        "options": {
          "graphMode": "area",
          "colorMode": "value"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "ops"
          }
        }
      },
      {
        "id": 8,
        "title": "Response Time Heatmap",
        "type": "heatmap",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 20},
        "targets": [
          {
            "expr": "sum(rate(bot_response_time_bucket[5m])) by (le)",
            "format": "heatmap",
            "legendFormat": "{{le}}",
            "refId": "A"
          }
        ],
        "options": {
          "calculate": false,
          "cellGap": 2,
          "cellRadius": 0,
          "color": {
            "exponent": 0.5,
            "fill": "dark-orange",
            "mode": "scheme",
            "reverse": false,
            "scale": "exponential",
            "scheme": "Spectral",
            "steps": 128
          },
          "exemplars": {
            "color": "rgba(255,0,255,0.7)"
          },
          "filterValues": {
            "le": 1e-9
          },
          "legend": {
            "show": true
          },
          "rowsFrame": {
            "layout": "auto"
          },
          "tooltip": {
            "show": true,
            "yHistogram": false
          },
          "yAxis": {
            "axisPlacement": "left",
            "reverse": false,
            "unit": "s"
          }
        }
      }
    ],
    "templating": {
      "list": [
        {
          "name": "provider",
          "type": "query",
          "query": "label_values(bot_api_calls_total, provider)",
          "multi": true,
          "includeAll": true,
          "current": {"text": "All", "value": "$__all"}
        },
        {
          "name": "model",
          "type": "query",
          "query": "label_values(bot_api_calls_total{provider=~\"$provider\"}, model)",
          "multi": true,
          "includeAll": true,
          "current": {"text": "All", "value": "$__all"}
        }
      ]
    },
    "annotations": {
      "list": [
        {
          "name": "Deployments",
          "datasource": "-- Grafana --",
          "enable": true,
          "iconColor": "rgba(0, 211, 255, 1)",
          "tags": ["deployment"]
        }
      ]
    }
  },
  "overwrite": true
}
```

### Performance Optimization Tips

Based on dashboard insights:

1. **High Response Times**
   - Check API call duration - is the provider slow?
   - Check tool execution - are tools taking too long?
   - Check message building - are tool schemas too complex?

2. **Slow API Calls**
   - Consider switching providers for specific models
   - Check network latency to provider endpoints
   - Verify API rate limits aren't being hit

3. **Slow Tool Execution**
   - Profile slow tools and optimize
   - Consider caching tool results
   - Use async execution where possible

4. **High Message Building Time**
   - Simplify tool descriptions
   - Reduce number of tools per bot
   - Cache tool schemas

---

---

## Cost Tracking Dashboard

### Overview

The Cost Tracking Dashboard provides real-time monitoring of LLM API costs across all providers. This dashboard is essential for:

- **Budget Management:** Track spending against budgets
- **Cost Optimization:** Identify expensive operations
- **Provider Comparison:** Compare costs across providers
- **Trend Analysis:** Monitor cost trends over time

**Key Metrics Tracked:**

- Total cost (cumulative and rate)
- Cost per provider and model
- Cost per operation
- Token usage and efficiency
- Cost projections (daily, monthly)

### Dashboard Panels

#### 1. Total Cost (Current)

Single-stat panel showing cumulative cost since metrics started.

**PromQL Query:**

```promql
sum(bot_cost_total_usd)
```

**Color Thresholds:**

- **Green:** < $10
- **Yellow:** $10-$100
- **Red:** > $100

#### 2. Cost Rate (per hour)

Shows current spending rate projected to hourly cost.

**PromQL Query:**

```promql
sum(rate(bot_cost_total_usd[5m])) * 3600
```

**Use Cases:**

- Monitor real-time spending
- Detect cost spikes
- Capacity planning

#### 3. Average Cost per API Call

Average cost per operation across all providers.

**PromQL Query:**

```promql
sum(rate(bot_cost_total_usd[5m])) / sum(rate(bot_api_calls_total[5m]))
```

**Benchmarks:**

- **Excellent:** < $0.01 per call
- **Good:** $0.01-$0.05 per call
- **Review:** > $0.05 per call

#### 4. API Calls per Second

Shows request volume to understand cost context.

**PromQL Query:**

```promql
sum(rate(bot_api_calls_total[5m]))
```

#### 5. Cost Over Time

Time series showing cost accumulation.

**PromQL Query:**

```promql
sum(rate(bot_cost_total_usd[5m]))
```

**Visualization:** Line graph with area fill
**Use Cases:**

- Identify cost spikes
- Correlate with deployments
- Track daily patterns

#### 6. Cumulative Cost

Shows total spending over time.

**PromQL Query:**

```promql
sum(increase(bot_cost_total_usd[1h]))
```

**Visualization:** Stacked area chart

#### 7. Cost by Provider (Stacked)

Compares spending across providers over time.

**PromQL Query:**

```promql
sum(rate(bot_cost_total_usd[5m])) by (provider)
```

**Visualization:** Stacked area chart
**Use Cases:**

- Provider cost comparison
- Identify most expensive provider
- Optimize provider selection

#### 8. Cost by Provider (Pie Chart)

Shows cost distribution as percentages.

**PromQL Query:**

```promql
sum(increase(bot_cost_total_usd[1h])) by (provider)
```

**Visualization:** Pie chart

#### 9. Cost by Model

Tracks spending per model over time.

**PromQL Query:**

```promql
sum(rate(bot_cost_total_usd[5m])) by (model)
```

**Visualization:** Multi-line time series
**Use Cases:**

- Identify expensive models
- Compare model costs
- Optimize model selection

#### 10. Cost per Operation (Bar Gauge)

Shows average cost per operation type.

**PromQL Query:**

```promql
sum(rate(bot_cost_usd_sum[5m])) by (provider, model) / sum(rate(bot_cost_usd_count[5m])) by (provider, model)
```

**Visualization:** Horizontal bar gauge
**Sort:** Descending by cost

#### 11. Cost per Operation (Table)

Detailed breakdown with statistics.

**Columns:**

- Provider
- Model
- Avg Cost
- p95 Cost
- Total Calls
- Total Cost

**PromQL Queries:**

```promql
# Average Cost
sum(rate(bot_cost_usd_sum[5m])) by (provider, model) / sum(rate(bot_cost_usd_count[5m])) by (provider, model)

# p95 Cost
histogram_quantile(0.95, sum(rate(bot_cost_usd_bucket[5m])) by (le, provider, model))

# Total Calls
sum(increase(bot_api_calls_total[1h])) by (provider, model)

# Total Cost
sum(increase(bot_cost_total_usd[1h])) by (provider, model)
```

#### 12. Token Usage (Input vs Output)

Compares input and output token consumption.

**PromQL Query:**

```promql
# Input tokens
sum(rate(bot_tokens_used{token_type="input"}[5m]))

# Output tokens
sum(rate(bot_tokens_used{token_type="output"}[5m]))
```

**Visualization:** Stacked bar chart or dual-axis line graph

#### 13. Cost Efficiency (Cost per 1M Tokens)

Shows cost efficiency across providers.

**PromQL Query:**

```promql
(sum(rate(bot_cost_total_usd[5m])) by (provider) / sum(rate(bot_tokens_used[5m])) by (provider)) * 1000000
```

**Use Cases:**

- Compare provider efficiency
- Validate pricing calculations
- Optimize for cost per token

### Dashboard Variables

The dashboard includes template variables for filtering:

**Provider Variable:**

```promql
label_values(bot_cost_total_usd, provider)
```

**Model Variable:**

```promql
label_values(bot_cost_total_usd{provider=~"$provider"}, model)
```

**Time Range Variable:**

- Last 1 hour
- Last 6 hours
- Last 24 hours
- Last 7 days
- Custom

### Annotations

The dashboard includes automatic annotations for:

**Cost Spikes:**

```promql
sum(rate(bot_cost_total_usd[5m])) > 0.01
```

**High-Cost Operations:**

```promql
histogram_quantile(0.95, sum(rate(bot_cost_usd_bucket[5m])) by (le)) > 0.05
```

### Import Instructions

1. **Copy the dashboard JSON** (see below)
2. **Open Grafana** → Dashboards → Import
3. **Paste JSON** into the import dialog
4. **Select Prometheus datasource**
5. **Click Import**

### Usage Examples

#### Example 1: Daily Cost Monitoring

**Goal:** Track daily spending and stay within $50/day budget

**Setup:**

1. Set time range to "Last 24 hours"
2. Monitor "Cost Rate (per hour)" panel
3. Set alert: `sum(increase(bot_cost_total_usd[24h])) > 50`

**Action:** Receive alert if daily cost exceeds $50

#### Example 2: Provider Cost Comparison

**Goal:** Determine which provider is most cost-effective

**Setup:**

1. View "Cost by Provider (Pie Chart)" panel
2. View "Cost Efficiency" panel
3. Compare cost per 1M tokens

**Analysis:**

- Provider A: $2.50 per 1M tokens (40% of total cost)
- Provider B: $3.00 per 1M tokens (35% of total cost)
- Provider C: $4.00 per 1M tokens (25% of total cost)

**Action:** Shift more traffic to Provider A

#### Example 3: Model Optimization

**Goal:** Reduce costs by optimizing model selection

**Setup:**

1. View "Cost per Operation (Table)" panel
2. Sort by "Avg Cost" descending
3. Identify expensive models

**Analysis:**

- Model X: $0.08 per call (high cost)
- Model Y: $0.02 per call (medium cost)
- Model Z: $0.005 per call (low cost)

**Action:** Replace Model X with Model Y for non-critical operations

#### Example 4: Budget Alerts

**Goal:** Get notified when approaching monthly budget

**Setup:**

1. Set alert on "Total Cost" panel
2. Threshold: $1000 (monthly budget)
3. Notification channel: Email/Slack

**Alert Rule:**

```yaml
alert: MonthlyBudgetAlert
expr: sum(increase(bot_cost_total_usd[30d])) > 1000
for: 1h
labels:
  severity: warning
annotations:
  summary: "Monthly budget exceeded"
  description: "Total cost is ${{ $value }} (budget: $1000)"
```

### Customization Tips

**Adjust Time Ranges:**

- Short-term monitoring: Use 5m-15m ranges
- Trend analysis: Use 1h-24h ranges
- Historical analysis: Use 7d-30d ranges

**Add Custom Panels:**

- Cost per user/tenant
- Cost per feature/endpoint
- Cost savings from caching
- Cost comparison: actual vs projected

**Set Budget Thresholds:**

- Daily: $10-$100
- Weekly: $50-$500
- Monthly: $200-$2000

**Color Coding:**

- Green: Under budget
- Yellow: Approaching budget (80%)
- Red: Over budget

### Troubleshooting

**No cost data showing?**

1. Verify metrics are enabled: `BOTS_OTEL_METRICS_ENABLED=true`
2. Check bot is recording costs: Look for `bot_cost_total_usd` metric
3. Verify time range includes data
4. Check Prometheus is scraping metrics

**Cost seems incorrect?**

1. Verify pricing data is up to date (see COST_TRACKING.md)
2. Check token counts in API responses
3. Verify cache discount calculations
4. Compare with provider billing dashboard

**Dashboard panels empty?**

1. Check Prometheus data source connection
2. Verify metric names (use Metrics Explorer)
3. Adjust time range
4. Check for query errors in panel editor

---

## Error Tracking Dashboard

### Overview

The Error Tracking Dashboard monitors failures, errors, and anomalies across the bots framework. This dashboard helps:

- **Identify Issues:** Detect errors before they impact users
- **Root Cause Analysis:** Understand error patterns
- **Monitor Reliability:** Track success rates
- **Alert on Anomalies:** Get notified of unusual error rates

**Key Metrics Tracked:**

- Error rates by provider and type
- Tool failure rates
- Success rates
- Error trends over time

### Dashboard Panels

#### 1. Error Rate (Errors per Second)

Shows overall error rate across all operations.

**PromQL Query:**

```promql
sum(rate(bot_errors_total[5m]))
```

**Alert Threshold:** > 0.1 errors/second
**Visualization:** Line graph with threshold line

#### 2. Error Rate by Provider

Compares error rates across providers.

**PromQL Query:**

```promql
sum(rate(bot_errors_total[5m])) by (provider)
```

**Use Cases:**

- Identify problematic providers
- Detect provider outages
- Compare provider reliability

#### 3. Error Rate by Type

Shows most common error types.

**PromQL Query:**

```promql
topk(10, sum(rate(bot_errors_total[5m])) by (error_type))
```

**Visualization:** Bar chart or table
**Sort:** Descending by rate

#### 4. Tool Failure Rate

Monitors tool execution failures.

**PromQL Query:**

```promql
sum(rate(bot_tool_failures_total[5m]))
```

**Alert Threshold:** > 0.05 failures/second

#### 5. Tool Failures by Tool Name

Identifies problematic tools.

**PromQL Query:**

```promql
topk(10, sum(rate(bot_tool_failures_total[5m])) by (tool_name))
```

**Use Cases:**

- Identify buggy tools
- Prioritize tool fixes
- Monitor tool reliability

#### 6. Success Rate (Percentage)

Shows percentage of successful operations.

**PromQL Query:**

```promql
(sum(rate(bot_api_calls_total{status="success"}[5m])) / sum(rate(bot_api_calls_total[5m]))) * 100
```

**Target:** > 99%
**Warning:** < 95%
**Critical:** < 90%

**Visualization:** Gauge or stat panel with thresholds

#### 7. Tool Success Rate

Shows percentage of successful tool executions.

**PromQL Query:**

```promql
(sum(rate(bot_tool_calls_total{success="true"}[5m])) / sum(rate(bot_tool_calls_total[5m]))) * 100
```

**Target:** > 95%

#### 8. Error Percentage (Errors vs Total Operations)

Shows error rate as percentage of all operations.

**PromQL Query:**

```promql
(sum(rate(bot_errors_total[5m])) / sum(rate(bot_api_calls_total[5m]))) * 100
```

**Target:** < 1%
**Warning:** > 5%
**Critical:** > 10%

#### 9. Errors Over Time

Time series showing error trends.

**PromQL Query:**

```promql
sum(rate(bot_errors_total[5m])) by (provider, error_type)
```

**Visualization:** Stacked area chart
**Use Cases:**

- Identify error spikes
- Correlate with deployments
- Track error patterns

#### 10. Total Errors (Last Hour)

Shows total error count in the last hour.

**PromQL Query:**

```promql
sum(increase(bot_errors_total[1h]))
```

**Visualization:** Single stat

#### 11. Error Heatmap

Visualizes error distribution over time.

**PromQL Query:**

```promql
sum(rate(bot_errors_total[5m])) by (error_type)
```

**Visualization:** Heatmap
**Use Cases:**

- Identify time-based patterns
- Detect recurring issues
- Visualize error intensity

#### 12. Recent Errors (Table)

Detailed table of recent error events.

**Columns:**

- Timestamp
- Provider
- Error Type
- Operation
- Rate (errors/sec)

**PromQL Queries:**

```promql
# Error rate by provider and type
sum(rate(bot_errors_total[5m])) by (provider, error_type, operation)
```

### Alert Rules

#### Critical: High Error Rate

```yaml
alert: HighErrorRate
expr: sum(rate(bot_errors_total[5m])) > 0.1
for: 5m
labels:
  severity: critical
annotations:
  summary: "High error rate detected"
  description: "Error rate is {{ $value }} errors/second (threshold: 0.1)"
```

#### Critical: Low Success Rate

```yaml
alert: LowSuccessRate
expr: (sum(rate(bot_api_calls_total{status="success"}[5m])) / sum(rate(bot_api_calls_total[5m]))) * 100 < 90
for: 10m
labels:
  severity: critical
annotations:
  summary: "Success rate below 90%"
  description: "Success rate is {{ $value }}% (threshold: 90%)"
```

#### Warning: High Tool Failure Rate

```yaml
alert: HighToolFailureRate
expr: (sum(rate(bot_tool_failures_total[5m])) / sum(rate(bot_tool_calls_total[5m]))) * 100 > 10
for: 10m
labels:
  severity: warning
annotations:
  summary: "Tool failure rate above 10%"
  description: "Tool failure rate is {{ $value }}% (threshold: 10%)"
```

#### Warning: Provider Errors

```yaml
alert: ProviderErrors
expr: sum(rate(bot_errors_total[5m])) by (provider) > 0.05
for: 5m
labels:
  severity: warning
annotations:
  summary: "High error rate for {{ $labels.provider }}"
  description: "Error rate is {{ $value }} errors/second for {{ $labels.provider }}"
```

### Dashboard Variables

**Provider Filter:**

```promql
label_values(bot_errors_total, provider)
```

**Error Type Filter:**

```promql
label_values(bot_errors_total, error_type)
```

**Tool Name Filter:**

```promql
label_values(bot_tool_failures_total, tool_name)
```

### Import Instructions

1. **Copy the dashboard JSON** (available in repository)
2. **Open Grafana** → Dashboards → Import
3. **Paste JSON** into the import dialog
4. **Select Prometheus datasource**
5. **Click Import**

---

## Best Practices

### Dashboard Organization

**1. Use Folders**
Organize dashboards into logical folders:

- `/Bots/Overview` - High-level metrics
- `/Bots/Cost` - Cost tracking
- `/Bots/Performance` - Performance monitoring
- `/Bots/Errors` - Error tracking
- `/Bots/Providers` - Provider-specific dashboards

**2. Create Dashboard Hierarchy**

- **Executive Dashboard:** High-level KPIs (cost, success rate, volume)
- **Operational Dashboard:** Detailed metrics for day-to-day monitoring
- **Debug Dashboard:** Deep-dive metrics for troubleshooting

**3. Use Consistent Naming**

- Prefix: `Bots Framework -`
- Examples:
  - `Bots Framework - Overview`
  - `Bots Framework - Cost Tracking`
  - `Bots Framework - Performance`

### Panel Design

**1. Choose Appropriate Visualizations**

- **Time Series:** Trends, rates, durations
- **Stat/Gauge:** Current values, percentages
- **Bar Chart:** Comparisons, top N
- **Pie Chart:** Distribution, percentages
- **Table:** Detailed breakdowns
- **Heatmap:** Time-based patterns

**2. Use Color Effectively**

- **Green:** Good/Normal (< threshold)
- **Yellow:** Warning (approaching threshold)
- **Red:** Critical (exceeding threshold)
- **Blue:** Informational

**3. Set Meaningful Thresholds**

- Based on SLAs and business requirements
- Adjust based on historical data
- Document threshold rationale

**4. Add Context**

- Panel descriptions explaining what to look for
- Links to runbooks or documentation
- Annotations for deployments and incidents

### Query Optimization

**1. Use Appropriate Time Ranges**

- Real-time monitoring: `[1m]` to `[5m]`
- Trend analysis: `[15m]` to `[1h]`
- Historical analysis: `[1h]` to `[24h]`

**2. Limit Cardinality**

- Use `topk()` for high-cardinality labels
- Aggregate where possible
- Filter unnecessary labels

**3. Use Recording Rules**
For frequently used queries, create Prometheus recording rules:

```yaml
groups:
  - name: bots_framework
    interval: 30s
    rules:
      - record: bots:cost_rate:5m
        expr: sum(rate(bot_cost_total_usd[5m]))

      - record: bots:error_rate:5m
        expr: sum(rate(bot_errors_total[5m]))

      - record: bots:success_rate:5m
        expr: sum(rate(bot_api_calls_total{status="success"}[5m])) / sum(rate(bot_api_calls_total[5m]))
```

### Alerting Best Practices

**1. Alert on Symptoms, Not Causes**

- ✅ Alert: "High response time"
- ❌ Alert: "High CPU usage"

**2. Use Appropriate Severity Levels**

- **Critical:** Immediate action required, user impact
- **Warning:** Investigate soon, potential impact
- **Info:** Awareness, no immediate action

**3. Avoid Alert Fatigue**

- Set realistic thresholds
- Use `for:` duration to avoid flapping
- Group related alerts
- Implement alert routing

**4. Include Actionable Information**

```yaml
annotations:
  summary: "High response time detected"
  description: "p99 response time is {{ $value }}s (threshold: 5s)"
  runbook_url: "https://wiki.example.com/runbooks/high-response-time"
  dashboard_url: "https://grafana.example.com/d/bots-performance"
```

### Metric Visualization Tips

**1. Response Time Metrics**

- Always show percentiles (p50, p95, p99)
- Use histogram_quantile() for accurate percentiles
- Show multiple percentiles on same graph for context

**2. Cost Metrics**

- Show both rate and cumulative
- Include projections (daily, monthly)
- Break down by provider and model
- Compare against budgets

**3. Error Metrics**

- Show both absolute rate and percentage
- Break down by type and provider
- Include success rate for context
- Use log scale for wide ranges

**4. Usage Metrics**

- Show rates (per second) not raw counts
- Include comparisons (hour-over-hour, day-over-day)
- Break down by dimensions (provider, model, tool)

### Dashboard Maintenance

**1. Regular Reviews**

- Monthly: Review dashboard relevance
- Quarterly: Update thresholds based on data
- After incidents: Add missing metrics

**2. Version Control**

- Export dashboards as JSON
- Store in Git repository
- Track changes and rationale

**3. Documentation**

- Document dashboard purpose
- Explain each panel
- Provide interpretation guidance
- Link to runbooks

**4. Performance Monitoring**

- Monitor dashboard load times
- Optimize slow queries
- Use recording rules for complex queries
- Limit time ranges for heavy queries

### Team Collaboration

**1. Share Dashboards**

- Create team-specific views
- Use dashboard playlists for rotation
- Share links with specific time ranges

**2. Dashboard Annotations**

- Mark deployments
- Note incidents
- Track configuration changes

**3. Create Runbooks**
Link dashboards to runbooks for common scenarios:

- High cost → Cost optimization runbook
- High errors → Error investigation runbook
- Slow performance → Performance tuning runbook

### Example Dashboard Layout

**Top Row (KPIs):**

- Total Cost (today)
- Success Rate
- Error Rate
- Avg Response Time

**Second Row (Trends):**

- Cost Over Time
- Response Time (p50, p95, p99)
- Error Rate Over Time

**Third Row (Breakdowns):**

- Cost by Provider
- Response Time by Model
- Errors by Type

**Bottom Row (Details):**

- Recent Errors (Table)
- Slow Operations (Table)
- Top Tools by Usage

---

## Conclusion

This dashboard guide provides everything you need to visualize and monitor the bots framework metrics. Key takeaways:

✅ **Setup:** Use Docker Compose for quick start
✅ **Queries:** 72+ ready-to-use PromQL queries
✅ **Dashboards:** 3 complete dashboards (Cost, Performance, Errors)
✅ **Alerts:** Production-ready alert rules
✅ **Best Practices:** Proven patterns for dashboard design

**Next Steps:**

1. Set up Grafana + Prometheus using Docker Compose
2. Import the provided dashboards
3. Customize thresholds for your use case
4. Set up alerts and notifications
5. Share dashboards with your team

**Additional Resources:**

- [SETUP.md](SETUP.md) - OpenTelemetry setup guide
- [COST_TRACKING.md](COST_TRACKING.md) - Cost tracking details
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)

---

**Last Updated:** October 2025
**Version:** 1.0
**Maintainer:** Bots Framework Team
