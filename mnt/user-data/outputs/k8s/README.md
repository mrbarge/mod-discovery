# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying ModPlayer in a Kubernetes cluster.

## Architecture

The deployment consists of:
- **PostgreSQL StatefulSet**: Database with persistent storage
- **ModPlayer Deployment**: Application with 2 replicas for high availability
- **Services**: Internal communication between components
- **Ingress** (optional): External access to the application
- **ConfigMap**: Non-sensitive configuration
- **Secret**: Sensitive credentials (database passwords, secret keys)
- **PVCs**: Persistent storage for database and module cache

## Prerequisites

- Kubernetes cluster (1.21+)
- `kubectl` configured to access your cluster
- Sufficient cluster resources (at least 2 CPU cores, 2GB RAM)
- Storage provisioner for PersistentVolumes
- (Optional) Ingress controller for external access

## Quick Start

### 1. Build and Push Docker Image

First, build the Docker image and push it to your registry:

```bash
# Build the image
docker build -t your-registry/modplayer:latest .

# Push to registry
docker push your-registry/modplayer:latest
```

Or if using Podman:

```bash
podman build -t your-registry/modplayer:latest .
podman push your-registry/modplayer:latest
```

Update the image reference in `05-app.yaml` if using a custom registry.

### 2. Configure Secrets

**IMPORTANT**: Edit `02-secret.yaml` and change the default passwords and secret key:

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Edit the secret file
vi k8s/02-secret.yaml
```

### 3. Deploy to Kubernetes

Deploy all components:

```bash
# Apply all manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get all -n modplayer

# Check pod status
kubectl get pods -n modplayer -w
```

### 4. Access the Application

**Option A: Port Forward (for testing)**

```bash
kubectl port-forward -n modplayer service/modplayer 5000:5000
# Access at http://localhost:5000
```

**Option B: Ingress (for production)**

1. Ensure you have an Ingress controller installed
2. Edit `06-ingress.yaml` with your domain
3. Apply the ingress:
   ```bash
   kubectl apply -f k8s/06-ingress.yaml
   ```
4. Access at your configured domain

**Option C: NodePort**

```bash
# Uncomment the NodePort service in 06-ingress.yaml and apply
kubectl apply -f k8s/06-ingress.yaml
# Access at http://<node-ip>:30500
```

## Managing the Deployment

### View Logs

```bash
# Application logs
kubectl logs -n modplayer -l component=app -f

# Database logs
kubectl logs -n modplayer -l component=database -f
```

### Scale the Application

```bash
# Scale to 3 replicas
kubectl scale deployment/modplayer -n modplayer --replicas=3

# Verify
kubectl get pods -n modplayer
```

### Update the Application

```bash
# Build new image with tag
docker build -t your-registry/modplayer:v1.1.0 .
docker push your-registry/modplayer:v1.1.0

# Update deployment
kubectl set image deployment/modplayer modplayer=your-registry/modplayer:v1.1.0 -n modplayer

# Watch rollout
kubectl rollout status deployment/modplayer -n modplayer
```

### Backup Database

```bash
# Create a job to backup PostgreSQL
kubectl exec -n modplayer postgres-0 -- pg_dump -U modplayer modplayer > backup.sql

# Or use a CronJob for automated backups (create separate manifest)
```

### Restore Database

```bash
# Copy backup to pod
kubectl cp backup.sql modplayer/postgres-0:/tmp/backup.sql

# Restore
kubectl exec -n modplayer postgres-0 -- psql -U modplayer modplayer < /tmp/backup.sql
```

## Configuration

### Update ConfigMap

```bash
# Edit configmap
kubectl edit configmap modplayer-config -n modplayer

# Restart pods to pick up changes
kubectl rollout restart deployment/modplayer -n modplayer
```

### Update Secrets

```bash
# Edit secret
kubectl edit secret modplayer-secret -n modplayer

# Restart pods
kubectl rollout restart deployment/modplayer -n modplayer
kubectl rollout restart statefulset/postgres -n modplayer
```

## Storage

### Storage Classes

If your cluster has multiple storage classes, specify the desired class in PVC manifests:

```yaml
spec:
  storageClassName: fast-ssd  # or whatever your storage class is named
```

View available storage classes:

```bash
kubectl get storageclass
```

### Resize Volumes

To increase volume size:

```bash
# Edit PVC
kubectl edit pvc postgres-pvc -n modplayer
# Increase storage size in spec.resources.requests.storage

# Restart pod to resize filesystem
kubectl delete pod postgres-0 -n modplayer
```

## Monitoring

### Health Checks

Check application health:

```bash
# Port forward and check health endpoint
kubectl port-forward -n modplayer service/modplayer 5000:5000
curl http://localhost:5000/health
```

### Resource Usage

```bash
# View resource usage
kubectl top pods -n modplayer
kubectl top nodes
```

### Events

```bash
# View recent events
kubectl get events -n modplayer --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n modplayer

# Check logs
kubectl logs <pod-name> -n modplayer

# Check previous container logs (if pod restarted)
kubectl logs <pod-name> -n modplayer --previous
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
kubectl get pods -n modplayer -l component=database

# Test database connection from app pod
kubectl exec -n modplayer <app-pod-name> -- psql $DATABASE_URL -c "SELECT 1"
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n modplayer

# Check PV status
kubectl get pv

# Describe PVC for events
kubectl describe pvc postgres-pvc -n modplayer
```

## Cleanup

To remove the entire deployment:

```bash
# Delete all resources
kubectl delete namespace modplayer

# Or delete individual resources
kubectl delete -f k8s/
```

**Warning**: This will delete all data including the database. Make sure to backup first!

## Production Considerations

### Security

1. **Secrets Management**:
   - Use external secret management (e.g., HashiCorp Vault, AWS Secrets Manager)
   - Consider using Sealed Secrets or SOPS for encrypted secrets in Git

2. **Network Policies**:
   - Implement NetworkPolicies to restrict pod-to-pod communication
   - Only allow app pods to connect to database

3. **RBAC**:
   - Create service accounts with minimal required permissions
   - Avoid using default service account

### High Availability

1. **Database**:
   - Consider PostgreSQL replication for HA
   - Use managed database service (e.g., RDS, Cloud SQL)

2. **Application**:
   - Run multiple replicas (already configured with 2)
   - Use Pod Disruption Budgets
   - Deploy across multiple availability zones

### Monitoring & Observability

1. **Metrics**:
   - Install Prometheus for metrics collection
   - Configure Grafana dashboards

2. **Logging**:
   - Set up centralized logging (ELK, Loki, etc.)
   - Configure log rotation

3. **Tracing**:
   - Implement distributed tracing if needed

### Backups

1. **Database**:
   - Schedule regular backups using CronJob
   - Store backups in object storage (S3, GCS)
   - Test restore procedures regularly

2. **Application Data**:
   - Backup module cache PVC if needed
   - Document recovery procedures

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [PostgreSQL on Kubernetes](https://www.postgresql.org/docs/current/app-postgres.html)
- [Flask Production Deployment](https://flask.palletsprojects.com/en/latest/deploying/)
