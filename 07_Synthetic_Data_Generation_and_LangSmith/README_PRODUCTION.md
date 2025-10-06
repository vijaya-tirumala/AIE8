# 🚀 Production Deployment Guide: RAGAS LangGraph SDG Optimized

## Overview

This guide provides comprehensive instructions for deploying the RAGAS LangGraph SDG Optimized system to production with enterprise-grade features including monitoring, logging, scalability, and security.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │────│   SDG API       │────│     Redis       │
│  (Load Balancer)│    │  (FastAPI)      │    │   (Caching)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Grafana      │────│   Prometheus    │    │   File Storage  │
│ (Monitoring UI) │    │   (Metrics)     │    │   (Exports)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- LangChain API Key (optional)
- 4GB+ RAM available
- 10GB+ disk space

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repository>
cd 07_Synthetic_Data_Generation_and_LangSmith
```

### 2. Configure Environment

```bash
# Copy environment template
cp production.env.example production.env

# Edit with your API keys
nano production.env
```

Required environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here  # Optional
```

### 3. Deploy

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f sdg-api
```

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| SDG API | http://localhost:8000 | Main API endpoint |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Grafana | http://localhost:3000 | Monitoring dashboard (admin/admin) |
| Prometheus | http://localhost:9090 | Metrics collection |

## 📊 API Usage

### Generate Synthetic Data

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "content": "Your document content here...",
        "metadata": {"source": "example.pdf"},
        "source": "example.pdf"
      }
    ],
    "async_processing": false
  }'
```

### Check Task Status

```bash
curl "http://localhost:8000/tasks/{task_id}"
```

### Download Results

```bash
# JSON format
curl "http://localhost:8000/tasks/{task_id}/download?format=json"

# CSV format
curl "http://localhost:8000/tasks/{task_id}/download?format=csv"
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | API host address |
| `PORT` | 8000 | API port |
| `WORKERS` | 4 | Number of worker processes |
| `MAX_DOCUMENTS` | 10 | Maximum documents per request |
| `QUESTIONS_PER_DOCUMENT` | 3 | Questions generated per document |
| `TIMEOUT_SECONDS` | 300 | Request timeout |
| `EXPORT_DIR` | /app/data/exports | Export directory |

### Scaling Configuration

```bash
# Increase workers for higher throughput
export WORKERS=8

# Increase document limits
export MAX_DOCUMENTS=20

# Restart service
docker-compose restart sdg-api
```

## 📈 Monitoring

### Grafana Dashboards

1. **API Performance Dashboard**
   - Request rates
   - Response times
   - Error rates
   - Success rates

2. **SDG Processing Dashboard**
   - Task completion rates
   - Processing times
   - Document throughput
   - Evolution type distribution

3. **System Resources Dashboard**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

### Prometheus Metrics

Key metrics available:
- `sdg_tasks_total` - Total tasks processed
- `sdg_tasks_completed` - Completed tasks
- `sdg_tasks_failed` - Failed tasks
- `sdg_processing_duration_seconds` - Processing time
- `sdg_documents_processed_total` - Documents processed

## 🔒 Security

### Authentication (Optional)

To enable authentication, add to `production.env`:

```bash
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Rate Limiting

Configured in nginx.conf:
- 10 requests per second per IP
- Burst of 20 requests
- Applied to all endpoints

### CORS Configuration

```bash
CORS_ORIGINS=["https://yourdomain.com"]
CORS_CREDENTIALS=true
```

## 🛠️ Management Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart API
docker-compose restart sdg-api

# View logs
docker-compose logs -f sdg-api

# Scale API
docker-compose up -d --scale sdg-api=3
```

### Data Management

```bash
# Backup exports
tar -czf exports_backup.tar.gz data/exports/

# Clean old exports
find data/exports -name "*.json" -mtime +30 -delete

# View disk usage
docker system df
```

### Monitoring Commands

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check API health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
```

## 🚨 Troubleshooting

### Common Issues

1. **API Not Starting**
   ```bash
   # Check logs
   docker-compose logs sdg-api
   
   # Verify environment variables
   docker-compose config
   ```

2. **Out of Memory**
   ```bash
   # Reduce workers
   export WORKERS=2
   docker-compose restart sdg-api
   ```

3. **Slow Processing**
   ```bash
   # Increase timeout
   export TIMEOUT_SECONDS=600
   docker-compose restart sdg-api
   ```

4. **Export Failures**
   ```bash
   # Check disk space
   df -h
   
   # Check permissions
   ls -la data/exports/
   ```

### Performance Optimization

1. **Database Connection Pooling**
   - Configure Redis for session storage
   - Use connection pooling for external databases

2. **Caching Strategy**
   - Cache processed documents
   - Cache embedding vectors
   - Use Redis for session storage

3. **Load Balancing**
   - Deploy multiple API instances
   - Use nginx for load balancing
   - Configure health checks

## 📊 Production Metrics

### Expected Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Requests/sec | 10-50 | Depends on document size |
| Response Time | <30s | For typical documents |
| Uptime | >99.9% | With proper monitoring |
| Memory Usage | <2GB | Per worker process |
| CPU Usage | <80% | Under normal load |

### SLA Targets

- **Availability**: 99.9% uptime
- **Response Time**: <30 seconds for 95% of requests
- **Error Rate**: <1% of requests
- **Throughput**: 100+ documents/hour

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Build new image
docker build -t ragas-sdg-optimized:latest .

# Update services
docker-compose up -d --no-deps sdg-api
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf "backup_${DATE}.tar.gz" data/ logs/
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/docker-containers
```

## 📞 Support

For production issues:
1. Check logs: `docker-compose logs -f sdg-api`
2. Monitor metrics: http://localhost:3000
3. Verify health: `curl http://localhost:8000/health`
4. Review configuration: `docker-compose config`

## 🎯 Best Practices

1. **Resource Monitoring**: Set up alerts for CPU, memory, and disk usage
2. **Log Management**: Implement log rotation and centralized logging
3. **Backup Strategy**: Regular backups of configuration and data
4. **Security Updates**: Keep Docker images and dependencies updated
5. **Performance Testing**: Regular load testing and optimization
6. **Documentation**: Keep deployment and operational documentation current

This production deployment provides enterprise-grade reliability, monitoring, and scalability for your RAGAS LangGraph SDG system! 🚀
