# Node-LLM System Infrastructure

This directory contains all the infrastructure-as-code configurations for deploying the Node-LLM System in production environments.

## Directory Structure

```
infra/
├── helm/                 # Helm charts for Kubernetes deployment
│   ├── Chart.yaml        # Helm chart metadata
│   ├── values.yaml       # Default configuration values
│   └── templates/        # Kubernetes manifest templates
├── monitoring/           # Observability stack configurations
│   ├── prometheus/       # Prometheus configuration
│   ├── grafana/          # Grafana dashboards
│   ├── fluentd/          # Fluentd configuration
│   └── k8s/              # Kubernetes manifests for monitoring stack
├── security/             # Security configurations
│   └── network-policies.yaml  # Kubernetes network policies
└── README.md            # This file
```

## Deployment Architecture

The Node-LLM System is designed to be deployed on Kubernetes with the following components:

1. **Frontend Service** - React application serving the UI
2. **Backend Service** - FastAPI application with REST API
3. **Worker Service** - Distributed agents for pipeline execution
4. **Redis** - In-memory data store for task queues
5. **PostgreSQL** - Relational database for persistent storage
6. **Ingress Controller** - External access to services

## Prerequisites

- Kubernetes cluster (v1.20 or higher)
- kubectl CLI configured
- Helm v3 installed
- Docker images pushed to a container registry

## Deployment

### Using Helm (Recommended)

```bash
# Create namespace
kubectl create namespace node-llm-system

# Deploy using Helm
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set image.repository=your-registry/node-llm-system \
  --set image.tag=latest
```

### Customizing Deployment

Update `values.yaml` or provide custom values during deployment:

```bash
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set replicaCount.backend=5 \
  --set backend.autoscaling.enabled=true \
  --set backend.autoscaling.maxReplicas=20
```

## Monitoring

Deploy the monitoring stack:

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy monitoring components
kubectl apply -f infra/monitoring/k8s/
```

## Security

Apply network policies:

```bash
kubectl apply -f infra/security/network-policies.yaml
```

## Scaling

The Helm chart includes Horizontal Pod Autoscaler configurations for backend and worker services. Ensure metrics-server is installed:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## Cloud Deployment

See [CLOUD_DEPLOYMENT.md](../docs/CLOUD_DEPLOYMENT.md) for detailed instructions on deploying to GKE, EKS, and AKS.

## Security Best Practices

See [SECURITY.md](../docs/SECURITY.md) for security recommendations and implementations.

## CI/CD Pipeline

The CI/CD pipeline is implemented using GitHub Actions. See [.github/workflows/ci-cd.yaml](../.github/workflows/ci-cd.yaml) for details.
