# Land Analysis MSA Docker Setup

This directory contains Docker configuration for the Land Analysis MSA (Microservice Architecture) application.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available for the container

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Navigate to docker directory
cd docker

# Build and start the service
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### Option 2: Using Docker directly

```bash
# Navigate to docker directory
cd docker

# Build the image
docker build -t land-analysis-msa .

# Run the container
docker run -d \
  --name land-analysis-msa \
  -p 8000:8000 \
  -e KNOWLEDGE_BASE_ID=1QN1H9SBJM \
  -e AWS_REGION=ap-northeast-2 \
  -e MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0 \
  -e BIZINFO_API_KEY=VtdTy4 \
  -v $(pwd)/reports:/app/reports \
  land-analysis-msa
```

## API Endpoints

Once the container is running, the following endpoints will be available:

- **API Documentation**: http://localhost:8000/docs
- **API Info**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **Browser Test**: http://localhost:8000/browser_test.html
- **Demo Analysis**: http://localhost:8000/demo/start

### Main API Endpoints:

- `POST /api/analyze` - Start land analysis
- `GET /api/status/{task_id}` - Check analysis status
- `GET /api/result/{task_id}` - Get analysis result (JSON)
- `GET /result/{task_id}` - Get analysis result (HTML)
- `GET /loading/{task_id}` - Loading page
- `GET /api/tasks` - List active tasks

## Sample API Request

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "land_data": {
      "주소": "대구광역시 중구 동인동1가 2-1",
      "지목": "대",
      "용도지역": "중심상업지역",
      "용도지구": "지정되지않음",
      "토지이용상황": "업무용",
      "지형고저": "평지",
      "형상": "세로장방",
      "도로접면": "광대소각",
      "공시지가": 3735000
    }
  }'
```

## Environment Variables

The following environment variables are configured:

- `KNOWLEDGE_BASE_ID`: AWS Knowledge Base ID
- `AWS_REGION`: AWS region (ap-northeast-2)
- `MODEL_ID`: Bedrock model ID
- `BIZINFO_API_KEY`: Business info API key

## Container Management

### View logs
```bash
docker-compose logs -f land-analysis-api
```

### Stop the service
```bash
docker-compose down
```

### Restart the service
```bash
docker-compose restart
```

### Update and rebuild
```bash
docker-compose down
docker-compose up --build
```

## Health Check

The container includes a health check that monitors the `/health` endpoint every 30 seconds.

Check container health:
```bash
docker ps
# Look for "healthy" status in the STATUS column
```

## Volumes

- `./reports:/app/reports` - Analysis reports are stored in the local `reports` directory

## Troubleshooting

### Container won't start
1. Check if port 8000 is already in use: `lsof -i :8000`
2. Check Docker logs: `docker-compose logs land-analysis-api`
3. Verify all required files are present in the `../final/` directory

### API returns errors
1. Check if AWS credentials are properly configured
2. Verify environment variables are set correctly
3. Check application logs for detailed error messages

### Performance issues
1. Ensure at least 2GB RAM is available
2. Monitor container resource usage: `docker stats`
3. Check if the knowledge base and model endpoints are accessible

## Production Considerations

For production deployment, consider:

1. **Security**: Use secrets management for API keys
2. **Scaling**: Use container orchestration (Kubernetes, Docker Swarm)
3. **Monitoring**: Add application monitoring and logging
4. **Persistence**: Use external database for task storage
5. **Load Balancing**: Add reverse proxy (nginx, traefik)
6. **SSL/TLS**: Configure HTTPS termination