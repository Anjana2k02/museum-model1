# Docker Deployment Guide

Complete guide for building, testing, and deploying the HAR Realtime API using Docker.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose V2+ (included with Docker Desktop)
- Git (for version control)

## Quick Start (Local Testing)

### 1. Prepare Environment File

Copy the example environment file:

```bash
# Windows PowerShell
Copy-Item .env.example .env.local

# Linux/macOS
cp .env.example .env.local
```

The `.env.local` file contains default settings suitable for local development.

### 2. Build and Run with Docker Compose

```bash
# Build and start the container
docker compose up --build

# Or run in detached mode (background)
docker compose up -d

# View logs
docker compose logs -f

# Stop and remove container
docker compose down
```

### 3. Test the API

The API will be available at `http://localhost:8000`

```bash
# Health check
curl http://localhost:8000/health

# Or open in browser:
# http://localhost:8000/docs (Swagger UI)
```

## Production Deployment

### Build Production Image

```bash
# Build with tag
docker build -t har-api:1.0.0 .

# Or with latest tag
docker build -t har-api:latest .
```

### Run Production Container

```bash
# Create production environment file
cat > .env.prod << EOF
ENV=live
HOST=0.0.0.0
PORT=8000
HAR_MODEL_PATH=/app/har_position_model.joblib
HAR_WINDOW_SIZE=128
HAR_STEP_SIZE=10
EOF

# Run container with environment file
docker run -d \
  --name har-api \
  --env-file .env.prod \
  -p 8000:8000 \
  --restart unless-stopped \
  har-api:1.0.0
```

### Container Management

```bash
# View logs
docker logs har-api

# Follow logs
docker logs -f har-api

# Check container status
docker ps

# Stop container
docker stop har-api

# Remove container
docker rm har-api

# Restart container
docker restart har-api
```

## Docker Hub Deployment

### 1. Tag Image for Docker Hub

```bash
# Replace 'yourusername' with your Docker Hub username
docker tag har-api:1.0.0 yourusername/har-api:1.0.0
docker tag har-api:1.0.0 yourusername/har-api:latest
```

### 2. Login and Push

```bash
# Login to Docker Hub
docker login

# Push images
docker push yourusername/har-api:1.0.0
docker push yourusername/har-api:latest
```

### 3. Pull and Run on Server

```bash
# On production server
docker pull yourusername/har-api:latest

docker run -d \
  --name har-api \
  -e ENV=live \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -p 8000:8000 \
  --restart unless-stopped \
  yourusername/har-api:latest
```

## Cloud Platform Deployment

### AWS Elastic Container Service (ECS)

1. Push image to Amazon ECR:

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag har-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/har-api:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/har-api:latest
```

2. Create ECS task definition with environment variables
3. Create ECS service with load balancer

### Google Cloud Run

```bash
# Tag for Google Container Registry
docker tag har-api:latest gcr.io/PROJECT_ID/har-api:latest

# Push to GCR
docker push gcr.io/PROJECT_ID/har-api:latest

# Deploy to Cloud Run
gcloud run deploy har-api \
  --image gcr.io/PROJECT_ID/har-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars ENV=live,HOST=0.0.0.0
```

### Azure Container Instances

```bash
# Tag for Azure Container Registry
docker tag har-api:latest myregistry.azurecr.io/har-api:latest

# Login and push
az acr login --name myregistry
docker push myregistry.azurecr.io/har-api:latest

# Create container instance
az container create \
  --resource-group myResourceGroup \
  --name har-api \
  --image myregistry.azurecr.io/har-api:latest \
  --dns-name-label har-api-unique \
  --ports 8000 \
  --environment-variables ENV=live HOST=0.0.0.0
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `local` | Environment mode: `local` (dev) or `live` (production) |
| `HOST` | `127.0.0.1` | Server bind address. Use `0.0.0.0` for Docker |
| `PORT` | `8000` | Server port |
| `HAR_MODEL_PATH` | `har_position_model.joblib` | Path to trained model file |
| `HAR_WINDOW_SIZE` | `128` | Number of samples in prediction window |
| `HAR_STEP_SIZE` | `10` | Samples between predictions (streaming mode) |

## Troubleshooting

### Container fails to start

Check logs:
```bash
docker logs har-api
```

Common issues:
- Port 8000 already in use: Change host port `-p 8001:8000`
- Model file missing: Ensure `har_position_model.joblib` is in project root
- Environment variables: Verify `.env` file syntax

### Can't connect to API

1. Verify container is running:
   ```bash
   docker ps
   ```

2. Check port binding:
   ```bash
   docker port har-api
   ```

3. Test from inside container:
   ```bash
   docker exec har-api curl localhost:8000/health
   ```

4. Verify firewall rules allow port 8000

### Image too large

The image includes a 48MB .joblib model. This is expected.

To optimize:
- Model is already in a separate layer (cached separately)
- Use Docker layer caching in CI/CD
- Consider model versioning separately if size becomes critical

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main, master]
    tags: ['v*']

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            yourusername/har-api:latest
            yourusername/har-api:${{ github.sha }}
          cache-from: type=registry,ref=yourusername/har-api:latest
          cache-to: type=inline
```

## Security Best Practices

1. **Never commit `.env.local` or production secrets** — Use `.gitignore`
2. **Use secrets management** — AWS Secrets Manager, Azure Key Vault, etc.
3. **Run as non-root user** — Add to Dockerfile if deploying to production:
   ```dockerfile
   RUN useradd -m -u 1000 apiuser
   USER apiuser
   ```
4. **Scan images for vulnerabilities**:
   ```bash
   docker scan har-api:latest
   ```
5. **Use specific base image tags** — Avoid `latest` in production
6. **Keep dependencies updated** — Regularly update `requirements.txt`

## Performance Tuning

### Resource Limits

```bash
# Limit memory and CPU
docker run -d \
  --name har-api \
  --memory="512m" \
  --cpus="1.0" \
  -p 8000:8000 \
  har-api:latest
```

### Docker Compose with Resources

```yaml
services:
  har-api:
    image: har-api:latest
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Multi-stage Build (Optional)

For even smaller images, consider multi-stage builds to remove build dependencies:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

## Monitoring

### Health Checks

Docker Compose already includes health checks. For standalone:

```bash
docker run -d \
  --name har-api \
  --health-cmd "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)\"" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=20s \
  -p 8000:8000 \
  har-api:latest
```

### Logging

Configure JSON logging for production:

```bash
docker run -d \
  --name har-api \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -p 8000:8000 \
  har-api:latest
```

## Support

For issues or questions:
- Check container logs: `docker logs har-api`
- Review API documentation: http://localhost:8000/docs
- Verify environment variables are set correctly
- Ensure model file (`har_position_model.joblib`) is present in the build context
