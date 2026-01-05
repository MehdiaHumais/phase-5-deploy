# Cloud Deployment Guide for Todo Chatbot

This document provides comprehensive instructions for deploying the Todo Chatbot application with Kafka and Dapr to DigitalOcean Kubernetes (DOKS).

## Prerequisites

### Required Tools
- **DigitalOcean Account**: With billing information configured
- **doctl**: DigitalOcean command-line tool
- **kubectl**: Kubernetes command-line tool
- **Helm**: Kubernetes package manager
- **Dapr CLI**: Dapr command-line interface
- **Docker**: For building container images
- **Git**: For version control

### DigitalOcean Setup
1. Sign up at [digitalocean.com](https://digitalocean.com)
2. Create a Kubernetes cluster (DOKS)
3. Configure kubectl to connect to DOKS
4. Set up billing information (new accounts get $200 credit for 60 days)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean Kubernetes (DOKS)               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Todo API      │  │  Notification │  │  Recurring Task │  │
│  │   Service       │  │   Service     │  │   Service       │  │
│  │  + Dapr Sidecar │  │ + Dapr Sidecar│  │ + Dapr Sidecar  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│              │                    │                    │        │
│              ▼                    ▼                    ▼        │
│  ┌─────────────────────────────────────────────────────────────┤
│  │              Dapr Building Blocks                           │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  │ pubsub.kafka│ │state.postgres│ │secretstores │           │
│  │  │             │ │             │ │ .kubernetes │           │
│  │  └─────────────┘ └─────────────┘ └─────────────┘           │
│  └─────────────────────────────────────────────────────────────┤
│              │                    │                    │        │
│              ▼                    ▼                    ▼        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Kafka Cluster   │  │ PostgreSQL DB   │  │ Kubernetes      │  │
│  │ (Redpanda)      │  │ (DO Managed)    │  │ Secrets         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Prepare Your Local Environment

### Install Required Tools
```bash
# Install doctl
curl -fsSL https://repos.insights.digitalocean.com/install.sh | sudo sh

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Dapr CLI
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
```

### Configure DigitalOcean
```bash
# Authenticate with DigitalOcean
doctl auth init

# Get your DOKS cluster credentials
doctl kubernetes cluster kubeconfig save <your-cluster-name>

# Verify connection
kubectl cluster-info
```

## Step 2: Set Up Kafka on Redpanda Cloud

### Create Redpanda Cloud Account
1. Sign up at [redpanda.com/cloud](https://redpanda.com/cloud)
2. Create a Serverless cluster (free tier available)
3. Create topics: `task-events`, `reminders`, `task-updates`
4. Copy the bootstrap server URL and credentials

### Configure Kafka Connection
Create a Kubernetes secret for Kafka credentials:
```bash
kubectl create secret generic kafka-credentials \
  --from-literal=bootstrap-servers="<your-redpanda-bootstrap-server>" \
  --from-literal=username="<your-username>" \
  --from-literal=password="<your-password>"
```

## Step 3: Deploy Dapr to DOKS

### Install Dapr on Kubernetes
```bash
# Install Dapr
dapr init -k

# Verify installation
dapr status -k
kubectl get pods -n dapr-system
```

### Configure Dapr Components
Create Dapr component configurations:

**Kafka Pub/Sub Component** (`dapr-kafka-pubsub.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
  namespace: default
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "<your-redpanda-bootstrap-server>:9092"
  - name: authRequired
    value: "true"
  - name: saslUsername
    secretKeyRef:
      name: kafka-credentials
      key: username
  - name: saslPassword
    secretKeyRef:
      name: kafka-credentials
      key: password
  - name: saslMechanism
    value: "SCRAM-SHA-256"
  - name: consumerGroup
    value: "todo-service"
  - name: publishTimeout
    value: "30s"
  - name: dialTimeout
    value: "30s"
  - name: readTimeout
    value: "30s"
  - name: writeTimeout
    value: "30s"
```

**PostgreSQL State Store Component** (`dapr-statestore.yaml`):
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: default
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    secretKeyRef:
      name: postgres-credentials
      key: connection-string
  - name: actorStateStore
    value: "true"
  - name: concurrency
    value: "first-write"
```

Apply the configurations:
```bash
kubectl apply -f dapr-kafka-pubsub.yaml
kubectl apply -f dapr-statestore.yaml
```

## Step 4: Set Up PostgreSQL Database

### Create Managed Database
```bash
# Create PostgreSQL database on DigitalOcean
doctl databases create todo-chatbot-db \
  --engine pg \
  --num-nodes 1 \
  --region nyc1 \
  --size db-s-1vcpu-1gb

# Get connection information
doctl databases connection-string todo-chatbot-db
```

### Create Database Credentials
```bash
kubectl create secret generic postgres-credentials \
  --from-literal=connection-string="postgresql://doadmin:<password>@<host>:25060/todo_chatbot_db?sslmode=require"
```

## Step 5: Build and Push Container Images

### Build Docker Images
```bash
# Build the main API image
docker build -t digitalocean/todo-chatbot-api:latest .

# Tag for DigitalOcean Container Registry (optional)
docker tag digitalocean/todo-chatbot-api:latest registry.digitalocean.com/todo-chatbot/todo-chatbot-api:latest
```

### Push to Registry (if using DOCR)
```bash
# Create container registry
doctl registry create todo-chatbot-registry --region nyc1

# Log in to registry
doctl registry login

# Push images
docker push registry.digitalocean.com/todo-chatbot/todo-chatbot-api:latest
```

## Step 6: Create Kubernetes Deployment Manifests

### Main API Deployment (`api-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-api
  labels:
    app: todo-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: todo-api
  template:
    metadata:
      labels:
        app: todo-api
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "todo-api"
        dapr.io/app-port: "8000"
        dapr.io/app-protocol: "http"
        dapr.io/app-health-check-path: "/health"
        dapr.io/config: "appconfig"
    spec:
      containers:
      - name: todo-api
        image: digitalocean/todo-chatbot-api:latest  # Use registry image if applicable
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: connection-string
        - name: KAFKA_BROKERS
          valueFrom:
            secretKeyRef:
              name: kafka-credentials
              key: bootstrap-servers
        - name: TODO_CHATBOT_ENV
          value: "production"
        - name: TODO_CHATBOT_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: todo-api-service
spec:
  selector:
    app: todo-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### Notification Service Deployment (`notification-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
  labels:
    app: notification-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: notification-service
  template:
    metadata:
      labels:
        app: notification-service
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "notification-service"
        dapr.io/app-port: "8001"
    spec:
      containers:
      - name: notification-service
        image: digitalocean/todo-chatbot-notification:latest  # Build and push this image
        ports:
        - containerPort: 8001
        env:
        - name: KAFKA_BROKERS
          valueFrom:
            secretKeyRef:
              name: kafka-credentials
              key: bootstrap-servers
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: notification-service
spec:
  selector:
    app: notification-service
  ports:
    - protocol: TCP
      port: 8001
      targetPort: 8001
  type: ClusterIP
```

## Step 7: Deploy Applications to DOKS

### Apply Kubernetes Manifests
```bash
# Apply Dapr configurations first
kubectl apply -f dapr-kafka-pubsub.yaml
kubectl apply -f dapr-statestore.yaml

# Apply service deployments
kubectl apply -f notification-deployment.yaml
kubectl apply -f api-deployment.yaml

# Verify deployments
kubectl get pods
kubectl get services
kubectl get deployments
```

### Configure Ingress (Optional)
```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/do/deploy.yaml

# Create ingress resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-chatbot-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: todo.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: todo-api-service
            port:
              number: 80
EOF
```

## Step 8: Set Up CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/deploy.yml`):
```yaml
name: Deploy to DOKS

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python -m pytest

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to DigitalOcean Container Registry
      uses: docker/login-action@v2
      with:
        registry: registry.digitalocean.com
        username: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
        password: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

    - name: Build and push Docker images
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: registry.digitalocean.com/todo-chatbot/todo-chatbot-api:${{ github.sha }}

    - name: Install doctl
      uses: digitalocean/action-doctl@v2
      with:
        token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

    - name: Configure kubectl
      run: doctl kubernetes cluster kubeconfig save ${{ secrets.DOKS_CLUSTER_NAME }}

    - name: Deploy to DOKS
      run: |
        # Update deployment with new image
        kubectl set image deployment/todo-api todo-api=registry.digitalocean.com/todo-chatbot/todo-chatbot-api:${{ github.sha }}

        # Wait for rollout to complete
        kubectl rollout status deployment/todo-api

    - name: Run post-deployment tests
      run: |
        # Add health check or integration tests
        echo "Running post-deployment tests..."
```

## Step 9: Configure Monitoring and Logging

### Set up DigitalOcean Monitoring
```bash
# Install DO agent for monitoring (if needed)
kubectl apply -f https://do-agent-instructions
```

### Configure Application Logging
```bash
# Create ConfigMap for logging configuration
kubectl create configmap logging-config \
  --from-literal=log-level=info \
  --from-literal=structured-logs=true
```

## Step 10: Security Configuration

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: todo-chatbot-network-policy
spec:
  podSelector:
    matchLabels:
      app: todo-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []  # Allow all egress initially, then restrict as needed
```

### RBAC Configuration
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: todo-chatbot-service-account
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: todo-chatbot-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: todo-chatbot-rolebinding
subjects:
- kind: ServiceAccount
  name: todo-chatbot-service-account
roleRef:
  kind: Role
  name: todo-chatbot-role
  apiGroup: rbac.authorization.k8s.io
```

## Step 11: Scale and Optimize

### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: todo-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: todo-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Apply HPA
```bash
kubectl apply -f hpa.yaml
```

## Step 12: Verify and Monitor Deployment

### Check Deployment Status
```bash
# Verify all pods are running
kubectl get pods

# Check services
kubectl get services

# Check deployments
kubectl get deployments

# Check Dapr status
dapr status -k

# Check logs
kubectl logs deployment/todo-api
```

### Test Application
```bash
# Get external IP
kubectl get service todo-api-service

# Test API endpoint
curl http://<EXTERNAL-IP>/health
```

## Troubleshooting

### Common Issues

1. **Pods Stuck in Pending State**
   ```bash
   # Check events
   kubectl describe pods

   # Check resource quotas
   kubectl describe quota
   ```

2. **Dapr Sidecar Issues**
   ```bash
   # Check Dapr logs
   kubectl logs -n dapr-system

   # Check component status
   kubectl get components.dapr.io
   ```

3. **Database Connection Issues**
   ```bash
   # Check secret
   kubectl describe secret postgres-credentials

   # Test connection from inside pod
   kubectl exec -it <pod-name> -- psql <connection-string>
   ```

4. **Kafka Connection Issues**
   ```bash
   # Check Kafka credentials
   kubectl describe secret kafka-credentials

   # Verify Redpanda cluster accessibility
   ```

### Useful Commands
```bash
# Check cluster status
kubectl get nodes
kubectl top nodes
kubectl top pods

# Check Dapr sidecars
kubectl get pods -l app=todo-api -o yaml | grep dapr

# Port forward for local testing
kubectl port-forward svc/todo-api-service 8080:80

# Check ingress (if configured)
kubectl get ingress
kubectl describe ingress todo-chatbot-ingress
```

## Rollback Procedure

If you need to rollback to a previous version:
```bash
# Check rollout history
kubectl rollout history deployment/todo-api

# Undo to previous version
kubectl rollout undo deployment/todo-api

# Or rollback to specific revision
kubectl rollout undo deployment/todo-api --to-revision=2
```

## Maintenance

### Regular Maintenance Tasks
- Monitor resource usage and scale as needed
- Update dependencies regularly
- Rotate secrets and certificates
- Backup databases regularly
- Update Dapr runtime periodically
- Monitor security advisories

### Backup Strategy
- Database backups: Use DigitalOcean's automated backups
- Configuration backups: Store in version control
- Secrets backup: Use Dapr secret store backups

This deployment guide provides a comprehensive approach to deploying the Todo Chatbot application to DigitalOcean Kubernetes with full Dapr integration, Kafka messaging, and proper security and monitoring configurations.