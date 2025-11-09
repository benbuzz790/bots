# OpenTelemetry Setup Guide

Complete guide for setting up OpenTelemetry observability in the bots framework.

## Table of Contents

- [Quick Start](#quick-start)
- [Console Exporter (Development)](#console-exporter-development)
- [OTLP Exporter (Production)](#otlp-exporter-production)
- [Jaeger Setup](#jaeger-setup)
- [Grafana + Prometheus Setup](#grafana--prometheus-setup)
- [Cloud Provider Integration](#cloud-provider-integration)
- [Environment Variables Reference](#environment-variables-reference)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

The bots framework includes built-in OpenTelemetry support for tracing, logging, and metrics.

**Enable observability with default settings:**

```python
from bots import AnthropicBot

# Tracing and metrics enabled by default
bot = AnthropicBot()
response = bot.respond("Hello!")
```

**Disable observability:**

```bash
export BOTS_OTEL_TRACING_ENABLED=false
```

---

## Console Exporter (Development)

The console exporter prints traces and metrics to stdout - perfect for development and debugging.

### Setup

**1. Install dependencies:**

```bash
pip install opentelemetry-api opentelemetry-sdk
```

**2. Configure environment:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=console
export BOTS_OTEL_METRICS_ENABLED=true
export BOTS_OTEL_METRICS_EXPORTER=console
```

**3. Run your bot:**

```python
from bots import AnthropicBot

bot = AnthropicBot()
response = bot.respond("What is 2+2?")
```

**Expected output:**

```json
{
    "name": "bot.respond",
    "context": {
        "trace_id": "0x1234...",
        "span_id": "0x5678..."
    },
    "attributes": {
        "bot.model": "claude-3-5-sonnet-latest",
        "bot.provider": "anthropic"
    }
}
```

### Advantages

- ✅ Zero infrastructure required
- ✅ Immediate feedback
- ✅ Easy debugging
- ✅ No network dependencies

### Disadvantages

- ❌ No persistence
- ❌ No visualization
- ❌ Clutters logs in production

---

## OTLP Exporter (Production)

The OpenTelemetry Protocol (OTLP) exporter is the production-standard way to send telemetry data.

### Setup

**1. Install dependencies:**

```bash
pip install opentelemetry-exporter-otlp-proto-grpc
```

**2. Configure environment:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=otlp
export BOTS_OTEL_ENDPOINT=http://localhost:4317
export BOTS_OTEL_METRICS_ENABLED=true
export BOTS_OTEL_METRICS_EXPORTER=otlp
```

**3. Run an OTLP collector:**

Use the OpenTelemetry Collector as a central aggregation point:

```yaml
# otel-collector-config.yaml
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

exporters:
  logging:
    loglevel: debug
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging, otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
```

**4. Start the collector:**

```bash
docker run -p 4317:4317 -p 4318:4318 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

### Advantages

- ✅ Industry standard protocol
- ✅ Vendor-neutral
- ✅ Supports all telemetry types
- ✅ Flexible routing and processing

---

## Jaeger Setup

Jaeger provides distributed tracing visualization with a powerful UI.

### Docker Compose Setup

**1. Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

**2. Start Jaeger:**

```bash
docker-compose up -d
```

**3. Configure your bot:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=otlp
export BOTS_OTEL_ENDPOINT=http://localhost:4317
```

**4. Run your bot and view traces:**

Open <http://localhost:16686> in your browser.

### Using Jaeger Exporter Directly

Alternatively, use the Jaeger exporter without OTLP:

```bash
pip install opentelemetry-exporter-jaeger
```

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=jaeger
export BOTS_OTEL_JAEGER_ENDPOINT=http://localhost:14250
```

### Jaeger UI Features

- **Trace Search**: Find traces by service, operation, tags
- **Trace Timeline**: Visualize span relationships and durations
- **Service Dependencies**: See how services interact
- **Performance Analysis**: Identify bottlenecks

---

## Grafana + Prometheus Setup

Combine Grafana and Prometheus for powerful metrics visualization and alerting.

### Docker Compose Setup

**1. Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports:
      - "4317:4317"
      - "4318:4318"
      - "8889:8889"  # Prometheus metrics
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    command: ["--config=/etc/otel-collector-config.yaml"]

volumes:
  prometheus-data:
  grafana-data:
```

**2. Create `prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

**3. Create `otel-collector-config.yaml`:**

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  logging:
    loglevel: info

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

**5. Configure your bot:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_METRICS_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=otlp
export BOTS_OTEL_ENDPOINT=http://localhost:4317
```

**6. Access dashboards:**

- Grafana: <http://localhost:3000> (admin/admin)
- Prometheus: <http://localhost:9090>

### Grafana Dashboard Setup

**1. Add Prometheus data source:**

- Go to Configuration → Data Sources
- Add Prometheus
- URL: `http://prometheus:9090`
- Save & Test

**2. Import dashboard:**

Create a new dashboard with these panels:

**API Call Duration:**

```promql
histogram_quantile(0.95, 
  rate(bot_api_call_duration_bucket[5m])
)
```

**Total Cost:**

```promql
sum(rate(bot_cost_total_usd[5m])) * 60
```

**Error Rate:**

```promql
rate(bot_errors_total[5m])
```

**Token Usage:**

```promql
rate(bot_tokens_used[5m])
```

### Alerting Rules

Prometheus alerting rules help you proactively monitor bot operations and catch issues before they impact users.

#### Setting Up Alerting

**1. Create `prometheus-alerts.yml`:**

```yaml
groups:
  - name: bot_cost_alerts
    interval: 30s
    rules:
      - alert: HighCostRate
        expr: rate(bot_cost_total_usd[5m]) > 0.10
        for: 5m
        labels:
          severity: warning
          category: cost
        annotations:
          summary: "Bot API costs are high"
          description: "Cost rate is ${{ $value | humanize }}/min (threshold: $0.10/min)"

      - alert: CriticalCostRate
        expr: rate(bot_cost_total_usd[5m]) > 0.50
        for: 2m
        labels:
          severity: critical
          category: cost
        annotations:
          summary: "Bot API costs are critically high"
          description: "Cost rate is ${{ $value | humanize }}/min (threshold: $0.50/min)"

      - alert: DailyCostBudgetExceeded
        expr: increase(bot_cost_total_usd[24h]) > 50.0
        labels:
          severity: warning
          category: cost
        annotations:
          summary: "Daily cost budget exceeded"
          description: "Total cost in last 24h: ${{ $value | humanize }} (budget: $50)"

      - alert: UnexpectedCostSpike
        expr: |
          rate(bot_cost_total_usd[5m]) > 
          (avg_over_time(rate(bot_cost_total_usd[5m])[1h:5m]) * 3)
        for: 5m
        labels:
          severity: warning
          category: cost
        annotations:
          summary: "Unexpected cost spike detected"
          description: "Current cost rate is 3x the hourly average"

  - name: bot_error_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(bot_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          category: errors
        annotations:
          summary: "Bot error rate is high"
          description: "Error rate: {{ $value | humanize }} errors/sec"

      - alert: CriticalErrorRate
        expr: rate(bot_errors_total[5m]) > 1.0
        for: 2m
        labels:
          severity: critical
          category: errors
        annotations:
          summary: "Bot error rate is critical"
          description: "Error rate: {{ $value | humanize }} errors/sec"

      - alert: ToolFailureSpike
        expr: rate(bot_tool_failures_total[5m]) > 0.5
        for: 5m
        labels:
          severity: warning
          category: errors
        annotations:
          summary: "Tool failures are elevated"
          description: "Tool failure rate: {{ $value | humanize }} failures/sec"

      - alert: APIErrorsByProvider
        expr: |
          sum by (provider) (rate(bot_errors_total{error_type="api_error"}[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
          category: errors
        annotations:
          summary: "High API error rate for {{ $labels.provider }}"
          description: "{{ $labels.provider }} API errors: {{ $value | humanize }}/sec"

  - name: bot_performance_alerts
    interval: 30s
    rules:
      - alert: SlowAPIResponses
        expr: |
          histogram_quantile(0.95, 
            rate(bot_api_call_duration_bucket[5m])
          ) > 30
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "API response times are slow"
          description: "P95 latency: {{ $value | humanize }}s (threshold: 30s)"

      - alert: VerySlowAPIResponses
        expr: |
          histogram_quantile(0.95, 
            rate(bot_api_call_duration_bucket[5m])
          ) > 60
        for: 2m
        labels:
          severity: critical
          category: performance
        annotations:
          summary: "API response times are critically slow"
          description: "P95 latency: {{ $value | humanize }}s (threshold: 60s)"

      - alert: ToolExecutionSlow
        expr: |
          histogram_quantile(0.95,
            rate(bot_tool_execution_duration_bucket[5m])
          ) > 10
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "Tool execution is slow"
          description: "P95 tool execution time: {{ $value | humanize }}s"

      - alert: HighTokenUsage
        expr: rate(bot_tokens_used[5m]) > 100000
        for: 5m
        labels:
          severity: warning
          category: performance
        annotations:
          summary: "Token usage is very high"
          description: "Token rate: {{ $value | humanize }} tokens/sec"

  - name: bot_availability_alerts
    interval: 30s
    rules:
      - alert: NoAPICallsRecent
        expr: rate(bot_api_calls_total[10m]) == 0
        for: 10m
        labels:
          severity: info
          category: availability
        annotations:
          summary: "No bot API calls in last 10 minutes"
          description: "Bot may be idle or experiencing issues"

      - alert: LowSuccessRate
        expr: |
          (
            rate(bot_api_calls_total[5m]) - 
            rate(bot_errors_total[5m])
          ) / rate(bot_api_calls_total[5m]) < 0.95
        for: 5m
        labels:
          severity: warning
          category: availability
        annotations:
          summary: "Bot success rate is low"
          description: "Success rate: {{ $value | humanizePercentage }}"
```

**2. Update `prometheus.yml` to load alerts:**

```yaml
global:
  scrape_interval: 15s

rule_files:
  - 'prometheus-alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

**3. Set up Alertmanager (optional but recommended):**

Add to your `docker-compose.yml`:

```yaml
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
```

**4. Create `alertmanager.yml`:**

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'category']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        category: cost
      receiver: 'cost-alerts'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://your-webhook-endpoint'

  - name: 'critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
    email_configs:
      - to: 'oncall@example.com'

  - name: 'cost-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#bot-costs'
        title: 'Bot Cost Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### Alert Severity Levels

**Critical** (Immediate action required):

- Cost rate > $0.50/min
- Error rate > 1.0/sec
- P95 latency > 60s
- Success rate < 90%

**Warning** (Investigation needed):

- Cost rate > $0.10/min
- Daily budget exceeded
- Error rate > 0.1/sec
- P95 latency > 30s
- Success rate < 95%

**Info** (Awareness only):

- No recent API calls
- Unusual patterns detected

#### Grafana Alerting

Grafana also supports alerting directly from dashboards:

**1. Create alert in Grafana panel:**

- Edit a panel (e.g., "API Call Duration")
- Go to Alert tab
- Click "Create Alert"
- Set conditions:

  ```
  WHEN avg() OF query(A, 5m, now) IS ABOVE 30
  ```

- Configure notifications

**2. Set up notification channels:**

- Go to Alerting → Notification channels
- Add channels: Email, Slack, PagerDuty, etc.
- Test notifications

**3. Example Grafana alert for cost:**

```json
{
  "alert": {
    "name": "High Bot Costs",
    "conditions": [
      {
        "evaluator": {
          "params": [0.10],
          "type": "gt"
        },
        "operator": {
          "type": "and"
        },
        "query": {
          "params": ["A", "5m", "now"]
        },
        "reducer": {
          "params": [],
          "type": "avg"
        },
        "type": "query"
      }
    ],
    "executionErrorState": "alerting",
    "frequency": "1m",
    "handler": 1,
    "message": "Bot API costs are exceeding $0.10/min",
    "name": "High Bot Costs",
    "noDataState": "no_data",
    "notifications": [
      {"uid": "slack-channel"}
    ]
  }
}
```

#### Alert Best Practices

**1. Tune thresholds based on your usage:**

- Start with conservative thresholds
- Monitor false positive rate
- Adjust based on actual patterns
- Document threshold rationale

**2. Use appropriate time windows:**

- Short windows (2-5m) for critical alerts
- Longer windows (5-15m) for warnings
- Consider business hours vs. off-hours

**3. Implement alert fatigue prevention:**

- Group related alerts
- Use appropriate repeat intervals
- Implement alert dependencies
- Auto-resolve when conditions clear

**4. Test your alerts:**

```bash
# Simulate high cost rate
for i in {1..100}; do
  python -c "from bots import AnthropicBot; bot = AnthropicBot(); bot.respond('test')"
done

# Check if alert fires
curl http://localhost:9090/api/v1/alerts
```

**5. Document alert response procedures:**

- What does each alert mean?
- Who should respond?
- What are the troubleshooting steps?
- When to escalate?

#### Cost Alert Examples

**Alert on specific model costs:**

```yaml
- alert: ExpensiveModelOveruse
  expr: |
    sum by (model) (rate(bot_cost_usd{model=~".*opus.*|.*gpt-4.*"}[5m])) > 0.05
  for: 5m
  annotations:
    summary: "Expensive model {{ $labels.model }} is being overused"
    description: "Cost rate: ${{ $value | humanize }}/min"
```

**Alert on cost per conversation:**

```yaml
- alert: HighCostPerConversation
  expr: |
    rate(bot_cost_total_usd[5m]) / rate(bot_conversations_total[5m]) > 0.50
  for: 5m
  annotations:
    summary: "Cost per conversation is high"
    description: "Average cost: ${{ $value | humanize }} per conversation"
```

**Alert on unexpected provider costs:**

```yaml
- alert: UnexpectedProviderCosts
  expr: |
    sum by (provider) (rate(bot_cost_usd[5m])) > 
    (avg_over_time(sum by (provider) (rate(bot_cost_usd[5m]))[1h:5m]) * 2)
  for: 5m
  annotations:
    summary: "{{ $labels.provider }} costs are 2x normal"
    description: "Investigate usage patterns for {{ $labels.provider }}"
```

#### Integration with Incident Management

**PagerDuty Integration:**

```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_SERVICE_KEY'
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
```

**Slack Integration:**

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_WEBHOOK_URL'
        channel: '#bot-alerts'
        title: '{{ .CommonAnnotations.summary }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Labels.alertname }}
          *Severity:* {{ .Labels.severity }}
          *Description:* {{ .Annotations.description }}
          {{ end }}
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
```

**Email Integration:**

```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'team@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'YOUR_APP_PASSWORD'
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .CommonAnnotations.summary }}'
```

---

## Cloud Provider Integration

### Datadog

**1. Install Datadog exporter:**

```bash
pip install opentelemetry-exporter-datadog
```

**2. Configure environment:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export DD_API_KEY=your_api_key
export DD_SITE=datadoghq.com
```

**3. Custom setup (if needed):**

```python
from opentelemetry.exporter.datadog import DatadogExporter
from bots.observability.tracing import setup_tracing

exporter = DatadogExporter(
    agent_url="http://localhost:8126",
    service="bots-framework"
)
setup_tracing(exporter=exporter)
```

**4. View in Datadog:**

- APM → Traces
- Metrics → Explorer
- Dashboards → Create custom dashboard

### New Relic

**1. Install New Relic exporter:**

```bash
pip install opentelemetry-exporter-otlp
```

**2. Configure environment:**

```bash
export BOTS_OTEL_TRACING_ENABLED=true
export BOTS_OTEL_EXPORTER_TYPE=otlp
export BOTS_OTEL_ENDPOINT=https://otlp.nr-data.net:4317
export OTEL_EXPORTER_OTLP_HEADERS="api-key=YOUR_LICENSE_KEY"
```

**3. View in New Relic:**

- Distributed Tracing
- Metrics Explorer
- Custom Dashboards

### AWS X-Ray

**1. Install AWS X-Ray exporter:**

```bash
pip install opentelemetry-sdk-extension-aws
pip install opentelemetry-propagator-aws-xray
```

**2. Configure:**

```python
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdGenerator
from bots.observability.tracing import setup_tracing

setup_tracing(id_generator=AwsXRayIdGenerator())
```

**3. Set environment:**

```bash
export AWS_REGION=us-east-1
export BOTS_OTEL_TRACING_ENABLED=true
```

### Google Cloud Trace

**1. Install Google Cloud exporter:**

```bash
pip install opentelemetry-exporter-gcp-trace
```

**2. Configure:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
export BOTS_OTEL_TRACING_ENABLED=true
```

---

## Environment Variables Reference

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `BOTS_OTEL_TRACING_ENABLED` | `true` | Enable/disable tracing |
| `BOTS_OTEL_METRICS_ENABLED` | follows tracing | Enable/disable metrics |
| `BOTS_OTEL_SERVICE_NAME` | `bots-framework` | Service name in traces |

### Exporter Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BOTS_OTEL_EXPORTER_TYPE` | `console` | Exporter type: console, otlp, jaeger |
| `BOTS_OTEL_ENDPOINT` | `http://localhost:4317` | OTLP endpoint |
| `BOTS_OTEL_JAEGER_ENDPOINT` | `http://localhost:14250` | Jaeger endpoint |
| `BOTS_OTEL_METRICS_EXPORTER` | follows tracing | Metrics exporter type |

### Advanced Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_HEADERS` | - | Custom headers for OTLP |
| `OTEL_EXPORTER_OTLP_TIMEOUT` | `10` | Timeout in seconds |
| `OTEL_TRACES_SAMPLER` | `always_on` | Sampling strategy |

---

## Troubleshooting

### No traces appearing

**Check if tracing is enabled:**

```python
from bots.observability.tracing import is_tracing_enabled
print(f"Tracing enabled: {is_tracing_enabled()}")
```

**Verify environment variables:**

```bash
env | grep BOTS_OTEL
```

**Check exporter connectivity:**

```bash
# Test OTLP endpoint
curl -v http://localhost:4317
```

### Metrics not recording

**Verify metrics are enabled:**

```python
from bots.observability.metrics import is_metrics_enabled
print(f"Metrics enabled: {is_metrics_enabled()}")
```

**Check if OpenTelemetry is installed:**

```bash
pip list | grep opentelemetry
```

**Expected packages:**

- opentelemetry-api
- opentelemetry-sdk
- opentelemetry-exporter-otlp-proto-grpc (for OTLP)

### High overhead

**Reduce sampling rate:**

```bash
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1  # Sample 10%
```

**Use batch processing:**

```bash
export OTEL_BSP_MAX_QUEUE_SIZE=2048
export OTEL_BSP_SCHEDULE_DELAY=5000
```

### Connection refused errors

**Check if collector is running:**

```bash
docker ps | grep otel
```

**Verify endpoint configuration:**

```bash
echo $BOTS_OTEL_ENDPOINT
```

**Test with console exporter:**

```bash
export BOTS_OTEL_EXPORTER_TYPE=console
```

### Missing dependencies

**Install all observability dependencies:**

```bash
pip install opentelemetry-api \
            opentelemetry-sdk \
            opentelemetry-exporter-otlp-proto-grpc \
            opentelemetry-exporter-jaeger
```

### Performance issues

**Disable observability temporarily:**

```bash
export BOTS_OTEL_TRACING_ENABLED=false
```

**Profile overhead:**

```python
import time
from bots import AnthropicBot

# Without observability
start = time.time()
bot = AnthropicBot(enable_tracing=False)
response = bot.respond("test")
no_otel_time = time.time() - start

# With observability
start = time.time()
bot = AnthropicBot(enable_tracing=True)
response = bot.respond("test")
with_otel_time = time.time() - start

print(f"Overhead: {(with_otel_time - no_otel_time) * 1000:.2f}ms")
```

---

## Best Practices

### Development

- ✅ Use console exporter for quick debugging
- ✅ Enable verbose logging
- ✅ Test with small workloads first

### Staging

- ✅ Use OTLP with local collector
- ✅ Set up Jaeger for trace visualization
- ✅ Configure sampling (50-100%)

### Production

- ✅ Use OTLP with managed collector
- ✅ Send to cloud provider (Datadog, New Relic, etc.)
- ✅ Configure appropriate sampling (1-10%)
- ✅ Set up alerting on key metrics
- ✅ Monitor costs with dashboards

---

## Next Steps

- [Cost Tracking Guide](COST_TRACKING.md) - Learn how to track and optimize costs
- [Callbacks Guide](CALLBACKS.md) - Implement custom progress indicators
- [Metrics Reference](METRICS.md) - Complete metrics documentation

---

**Last Updated**: October 2025
