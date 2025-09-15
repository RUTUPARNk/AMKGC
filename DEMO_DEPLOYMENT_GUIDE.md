# Node-LLM System Demo Deployment Guide

This guide provides step-by-step instructions for deploying the Node-LLM System for demonstration purposes on a managed Kubernetes cluster.

## Prerequisites

1. A managed Kubernetes cluster (GKE, EKS, or AKS)
2. `kubectl` CLI configured to access your cluster
3. `helm` CLI installed
4. `docker` CLI installed
5. A container registry (GitHub Container Registry is used in this guide)

## 1. Provision Cluster

Choose one of the following managed cluster options:

### GKE
```bash
gcloud container clusters create node-llm-demo --num-nodes=2 --machine-type=e2-medium
```

### EKS
```bash
eksctl create cluster --name node-llm-demo --nodes=2 --node-type=t3.medium
```

### AKS
```bash
az aks create --resource-group demo-rg --name node-llm-demo --node-count 2 --node-vm-size Standard_B2s
```

## 2. Set Up Ingress + SSL

### Install Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx ingress-nginx/ingress-nginx
```

### Install cert-manager for SSL
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

## 3. Configure Secrets

Create Kubernetes secrets for database credentials and API keys:

```bash
kubectl create secret generic node-llm-secrets \
  --from-literal=DB_URL=postgresql://user:password@postgres:5432/node_llm_system \
  --from-literal=OPENAI_KEY=your-openai-api-key-here
```

These secrets will be automatically mounted into pods via `envFrom.secretRef` in the Helm chart.

## 4. Set Up Monitoring

Install Prometheus and Grafana using kube-prometheus-stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack
```

After installation, import these two dashboards:
1. Kubernetes / Compute Resources
2. HTTP Request Rate + Error Rate

## 5. Deploy Application

Deploy the Node-LLM System using Helm:

```bash
helm upgrade --install node-llm ./infra/helm \
  --namespace demo \
  --create-namespace
```

## 6. Configure DNS (Optional)

For external access, configure DNS to point to the ingress controller's external IP:

```bash
kubectl get svc nginx-ingress-nginx-controller
```

## 7. Verify Deployment

Check that all pods are running:

```bash
kubectl get pods -n demo
```

## 8. Run Load Test

Install k6:
```bash
brew install k6
```

Run the load test:
```bash
k6 run --vus 100 --duration 30s load-test.js
```

## 9. Access Services

### Frontend
Access the frontend at the root path of your domain.

### Backend API
Access the backend API at `/api` path of your domain.

### Monitoring
Access Grafana for monitoring:
```bash
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```

Access Prometheus:
```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
```

## Resource Configuration

The demo deployment uses minimal resources as configured in `infra/helm/values.yaml`:

- CPU requests: 200m
- Memory requests: 256Mi
- CPU limits: 500m
- Memory limits: 512Mi
- Single replica for each service
- Autoscaling enabled with max 3 replicas

## Cleanup

To remove the deployment:

```bash
helm uninstall node-llm -n demo
helm uninstall monitoring -n monitoring
helm uninstall cert-manager -n cert-manager
helm uninstall nginx
```

To delete the cluster:

### GKE
```bash
gcloud container clusters delete node-llm-demo
```

### EKS
```bash
eksctl delete cluster --name node-llm-demo
```

### AKS
```bash
az aks delete --resource-group demo-rg --name node-llm-demo
```
