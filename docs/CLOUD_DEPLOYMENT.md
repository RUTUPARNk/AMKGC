# Cloud Deployment Guidelines

This document provides guidelines for deploying the Node-LLM System to various cloud providers.

## Prerequisites

1. Kubernetes cluster (v1.20 or higher)
2. kubectl CLI configured
3. Helm v3 installed
4. Docker images pushed to a container registry
5. Domain name (optional, for ingress)

## Deployment Options

### 1. Google Cloud Platform (GKE)

#### Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create node-llm-system \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10

# Get credentials
gcloud container clusters get-credentials node-llm-system --zone=us-central1-a
```

#### Deploy Application

```bash
# Create namespace
kubectl create namespace node-llm-system

# Deploy using Helm
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set image.repository=gcr.io/your-project/node-llm-system \
  --set image.tag=latest
```

### 2. Amazon Web Services (EKS)

#### Create EKS Cluster

```bash
# Create cluster using eksctl
eksctl create cluster \
  --name node-llm-system \
  --version 1.21 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed
```

#### Deploy Application

```bash
# Create namespace
kubectl create namespace node-llm-system

# Deploy using Helm
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set image.repository=your-aws-account.dkr.ecr.us-west-2.amazonaws.com/node-llm-system \
  --set image.tag=latest
```

### 3. Microsoft Azure (AKS)

#### Create AKS Cluster

```bash
# Create resource group
az group create --name node-llm-system-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group node-llm-system-rg \
  --name node-llm-system-cluster \
  --node-count 3 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group node-llm-system-rg --name node-llm-system-cluster
```

#### Deploy Application

```bash
# Create namespace
kubectl create namespace node-llm-system

# Deploy using Helm
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set image.repository=your-acr.azurecr.io/node-llm-system \
  --set image.tag=latest
```

## Managed Services

For production deployments, consider using managed services for stateful components:

### PostgreSQL
- Google Cloud SQL
- Amazon RDS
- Azure Database for PostgreSQL

### Redis
- Google Cloud Memorystore
- Amazon ElastiCache
- Azure Cache for Redis

### Example with Google Cloud SQL

```bash
# Update Helm deployment to use external PostgreSQL
helm upgrade --install node-llm-system ./infra/helm \
  --namespace node-llm-system \
  --set postgres.enabled=false \
  --set externalDatabase.host=your-cloud-sql-instance.connection-string \
  --set externalDatabase.user=your-db-user \
  --set externalDatabase.password=your-db-password
```

## Ingress and TLS

### Install NGINX Ingress Controller

```bash
# Add ingress-nginx repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install ingress controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Configure TLS with Let's Encrypt

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Update Helm Values for TLS

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: your-domain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: node-llm-system-tls
      hosts:
        - your-domain.com
```

## Monitoring and Observability

Deploy the monitoring stack to the monitoring namespace:

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f infra/monitoring/k8s/prometheus.yaml

# Deploy Grafana
kubectl apply -f infra/monitoring/k8s/grafana.yaml

# Deploy EFK stack
kubectl apply -f infra/monitoring/k8s/efk.yaml
```

## Scaling and Performance

### Horizontal Pod Autoscaler

The Helm chart includes HPA configurations for backend and worker services. Ensure metrics-server is installed:

```bash
# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Resource Requests and Limits

Update the Helm values.yaml with appropriate resource requests and limits:

```yaml
backend:
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

worker:
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "250m"
```

## Backup and Disaster Recovery

1. Regularly backup PostgreSQL database
2. Backup Redis data if persistence is enabled
3. Store Docker images in multiple regions
4. Use multi-zone Kubernetes clusters for high availability

## Cost Optimization

1. Use spot instances for worker nodes
2. Implement proper resource requests/limits
3. Use autoscaling to adjust capacity based on demand
4. Monitor resource usage and adjust accordingly
