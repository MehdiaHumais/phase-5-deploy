# Monitoring and Observability for Todo Chatbot

This document provides comprehensive guidance on monitoring, logging, and observability for the Todo Chatbot application with Kafka and Dapr integration.

## Monitoring Philosophy

The Todo Chatbot follows the "Three Pillars of Observability":
1. **Logs**: Unstructured events and messages
2. **Metrics**: Quantitative measurements
3. **Traces**: Request flow across services

## Application Metrics

### Business Metrics
- **Task Creation Rate**: Number of tasks created per minute
- **Task Completion Rate**: Percentage of tasks completed
- **User Engagement**: Active users, session duration
- **Feature Adoption**: Usage of advanced features (reminders, recurring tasks)
- **Response Times**: API response times by endpoint

### System Metrics
- **CPU Usage**: Application and system CPU utilization
- **Memory Usage**: Memory consumption and garbage collection
- **Disk I/O**: Storage read/write operations
- **Network Traffic**: Inbound/outbound network traffic
- **Database Connections**: Active and idle database connections
- **Queue Lengths**: Kafka consumer lag, message queues

### Dapr-Specific Metrics
- **Dapr Sidecar Health**: Sidecar availability and performance
- **Service-to-Service Calls**: Call rates and latencies
- **State Operations**: State store read/write performance
- **Pub/Sub Throughput**: Message publishing/subscribing rates
- **Actor Activation**: Actor activation rates and duration

## Metric Collection and Storage

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerting_rules.yml"

scrape_configs:
  - job_name: 'todo-chatbot'
    static_configs:
      - targets: ['todo-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'dapr-sidecar'
    static_configs:
      - targets: ['todo-api:3501']  # Dapr metrics endpoint
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9404']  # JMX Exporter for Kafka
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres:9187']  # Postgres Exporter
    scrape_interval: 30s
```

### Application Metrics Implementation
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from functools import wraps
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'active_users',
    'Number of active users'
)

TASK_OPERATIONS = Counter(
    'task_operations_total',
    'Total task operations',
    ['operation']  # create, update, delete, complete
)

def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics."""
    start_time = time.time()

    response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)

    return response

# Decorator for business metrics
def track_task_operation(operation: str):
    """Decorator to track task operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            TASK_OPERATIONS.labels(operation=operation).inc()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage
@track_task_operation("create")
async def create_task(title: str, description: str):
    # Task creation logic
    pass
```

## Logging Strategy

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Unexpected but handled events
- **ERROR**: Runtime errors that don't prevent operation
- **CRITICAL**: Errors that prevent normal operation

### Structured Logging
```python
import structlog
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Example log entry
async def create_task(task_data: dict):
    logger.info(
        "task_creation_started",
        user_id=task_data.get("user_id"),
        task_title=task_data.get("title"),
        timestamp=datetime.utcnow().isoformat()
    )

    try:
        # Task creation logic
        task = await task_service.create_task(task_data)

        logger.info(
            "task_creation_successful",
            task_id=task.id,
            user_id=task.user_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return task
    except Exception as e:
        logger.error(
            "task_creation_failed",
            user_id=task_data.get("user_id"),
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )
        raise
```

### Log Fields Standardization
```json
{
  "timestamp": "2025-12-20T10:00:00Z",
  "level": "INFO",
  "logger": "todo_chatbot.api.tasks",
  "message": "task_created",
  "fields": {
    "user_id": "user-123",
    "task_id": "task-456",
    "request_id": "req-789",
    "duration_ms": 123,
    "correlation_id": "corr-abc"
  }
}
```

## Distributed Tracing

### OpenTelemetry Integration
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.aiopg import AioPGInstrumentor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export spans to Jaeger/Zipkin
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://jaeger:4317")
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument frameworks
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
AioPGInstrumentor().instrument()
```

### Trace Context Propagation
```python
from opentelemetry import trace
from opentelemetry.propagate import extract
import httpx

async def call_external_service(url: str, headers: dict = None):
    """Call external service with trace context propagation."""
    current_span = trace.get_current_span()

    # Extract trace context from incoming request
    ctx = extract(headers or {})

    with trace.use_span(trace.INVALID_SPAN if ctx is None else trace.NonRecordingSpan(ctx)):
        with tracer.start_as_current_span("external_api_call") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("http.url", url)

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                span.set_attribute("http.status_code", response.status_code)
                return response
```

## Dapr Observability

### Dapr Telemetry Configuration
```yaml
# components/telemetry.yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: appconfig
spec:
  tracing:
    samplingRate: "1"
    zipkin:
      endpointAddress: "http://zipkin.default.svc.cluster.local:9411/api/v2/spans"
  metric:
    enabled: true
  mtls:
    enabled: true
    workloadCertTTL: "24h"
    allowedClockSkew: "15m"
```

### Dapr Component Monitoring
- **Sidecar Health**: Monitor Dapr sidecar status
- **Component Status**: Track component initialization
- **Traffic Metrics**: Monitor service invocation metrics
- **Resource Usage**: Track Dapr sidecar resource consumption

## Kafka Monitoring

### Kafka Metrics
- **Consumer Lag**: Monitor message processing delays
- **Throughput**: Messages produced/consumed per second
- **Partitions**: Partition distribution and balance
- **Replication**: Replica synchronization status

### Kafka Consumer Metrics
```python
from aiokafka import AIOKafkaConsumer
import asyncio

async def monitor_consumer_health(consumer: AIOKafkaConsumer):
    """Monitor Kafka consumer health and metrics."""
    while True:
        try:
            # Get consumer metrics
            assignment = consumer.assignment()
            positions = await consumer.position(assignment)

            for tp in assignment:
                committed = consumer.committed(tp)
                position = positions[tp]

                # Calculate lag
                lag = position - committed if committed is not None else 0

                # Log metrics
                logger.info(
                    "kafka_consumer_metrics",
                    topic=tp.topic,
                    partition=tp.partition,
                    committed_offset=committed,
                    current_position=position,
                    lag=lag
                )

                # Alert if lag is too high
                if lag > 1000:  # Threshold
                    logger.warning(
                        "high_consumer_lag",
                        topic=tp.topic,
                        partition=tp.partition,
                        lag=lag
                    )

        except Exception as e:
            logger.error("consumer_monitoring_error", error=str(e))

        await asyncio.sleep(30)  # Check every 30 seconds
```

## Alerting and Notifications

### Alerting Rules
```yaml
# alerting_rules.yml
groups:
  - name: todo-chatbot.rules
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} over 5 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }} seconds"

      - alert: HighKafkaLag
        expr: kafka_consumer_lag > 1000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High Kafka consumer lag"
          description: "Consumer lag is {{ $value }} messages"

      - alert: DaprSidecarDown
        expr: up{job="dapr-sidecar"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Dapr sidecar is down"
          description: "Dapr sidecar for {{ $labels.instance }} is not responding"
```

### Notification Channels
- **Slack**: For critical alerts
- **Email**: For non-critical alerts
- **PagerDuty**: For production incidents
- **SMS**: For critical outages

## Monitoring Stack

### ELK Stack Configuration
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "id": null,
    "title": "Todo Chatbot Dashboard",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[1m])",
            "legendFormat": "Errors"
          }
        ]
      }
    ]
  }
}
```

## Health Checks

### Liveness and Readiness Probes
```python
from fastapi import FastAPI, HTTPException
import httpx
import asyncio

app = FastAPI()

@app.get("/health/liveness")
async def liveness_check():
    """Liveness probe - indicates if the application should be restarted."""
    # Check if the application is alive (basic functionality)
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/readiness")
async def readiness_check():
    """Readiness probe - indicates if the application can serve traffic."""
    checks = {
        "database": False,
        "kafka": False,
        "dapr": False
    }

    # Check database connectivity
    try:
        # Test database connection
        await db.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Check Kafka connectivity
    try:
        # Test Kafka connection
        async with httpx.AsyncClient() as client:
            response = await client.get("http://kafka:9092")
            checks["kafka"] = response.status_code == 200
    except Exception:
        checks["kafka"] = False

    # Check Dapr sidecar
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3500/v1.0/healthz")
            checks["dapr"] = response.status_code == 200
    except Exception:
        checks["dapr"] = False

    # Return overall status
    overall_status = all(checks.values())

    return {
        "status": "ready" if overall_status else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Performance Monitoring

### Profiling Tools
- **Py-Spy**: Low-overhead Python profiler
- **Scalene**: CPU, memory, and GPU profiler
- **Memory Profiler**: Memory usage analysis
- **Line Profiler**: Line-by-line performance analysis

### Performance Indicators
- **Response Time**: 95th percentile under 500ms
- **Throughput**: Target requests per second
- **Error Rate**: Less than 1% errors
- **Resource Utilization**: CPU/Memory under 80%

## Monitoring Best Practices

### 1. Set Appropriate Thresholds
- Base thresholds on historical data
- Account for traffic patterns
- Set both warning and critical thresholds
- Regularly review and adjust thresholds

### 2. Use Meaningful Alerts
- Avoid alert fatigue with intelligent grouping
- Include actionable information in alerts
- Set appropriate firing durations
- Use escalation policies

### 3. Monitor Business Metrics
- Track user engagement metrics
- Monitor feature adoption
- Measure conversion rates
- Watch revenue-related metrics

### 4. Implement Synthetic Monitoring
- Simulate user workflows
- Test critical paths regularly
- Monitor from different locations
- Track external service dependencies

## Troubleshooting

### Common Issues
1. **High Latency**: Check database queries, external services, and resource usage
2. **High Error Rates**: Review application logs, error patterns, and dependencies
3. **Kafka Lag**: Investigate consumer performance and partition distribution
4. **Dapr Issues**: Check sidecar logs, component configurations, and connectivity

### Diagnostic Commands
```bash
# Check application logs
kubectl logs deployment/todo-chatbot-api --tail=100

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check Dapr sidecar
dapr status -k

# Check Kafka consumer lag
kafka-run-class kafka.tools.ConsumerOffsetChecker --zkconnect localhost:2181 --group mygroup
```

## Monitoring Checklist

### Pre-Production
- [ ] Metrics collection is implemented
- [ ] Logging is configured with structured format
- [ ] Distributed tracing is enabled
- [ ] Health checks are implemented
- [ ] Alerting rules are defined
- [ ] Dashboard templates are created
- [ ] Notification channels are configured
- [ ] Performance baselines are established

### Production Monitoring
- [ ] Monitor system metrics continuously
- [ ] Track business metrics daily
- [ ] Review alert effectiveness weekly
- [ ] Update dashboards monthly
- [ ] Conduct monitoring reviews quarterly
- [ ] Optimize alert noise annually

This monitoring and observability guide ensures that the Todo Chatbot system remains healthy, performant, and reliable in production environments.