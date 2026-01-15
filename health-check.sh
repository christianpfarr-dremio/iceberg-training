#!/bin/bash

###########################################
# Health Check Script for Iceberg Training
# Checks if all services are running and healthy
###########################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Checking Iceberg Training Services..."
echo ""

# Function to check if a service is running
check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✓${NC} ${service_name} container is running"
        return 0
    else
        echo -e "${RED}✗${NC} ${service_name} container is NOT running"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local service_name=$1
    local url=$2
    local max_retries=${3:-3}
    
    for i in $(seq 1 $max_retries); do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} ${service_name} is healthy (${url})"
            return 0
        fi
        if [ $i -lt $max_retries ]; then
            sleep 2
        fi
    done
    
    echo -e "${RED}✗${NC} ${service_name} is NOT responding (${url})"
    return 1
}

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running!"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Check containers
echo "📦 Checking Containers..."
check_service "Nessie" "nessie"
check_service "MinIO" "minio"
check_service "Dremio" "dremio"
echo ""

# Check endpoints
echo "🌐 Checking Service Endpoints..."
check_endpoint "Nessie API" "http://localhost:19120/api/v2/config"
check_endpoint "MinIO Health" "http://localhost:9000/minio/health/live"
check_endpoint "MinIO Console" "http://localhost:9001"
check_endpoint "Dremio UI" "http://localhost:9047" 5
echo ""

# Check volumes
echo "💾 Checking Volumes..."
for volume in nessie-data minio-data dremio-data; do
    if docker volume ls --format '{{.Name}}' | grep -q "${volume}"; then
        echo -e "${GREEN}✓${NC} Volume ${volume} exists"
    else
        echo -e "${YELLOW}⚠${NC} Volume ${volume} does not exist"
    fi
done
echo ""

# Check networks
echo "🔌 Checking Networks..."
if docker network ls --format '{{.Name}}' | grep -q "iceberg"; then
    echo -e "${GREEN}✓${NC} Network iceberg exists"
else
    echo -e "${YELLOW}⚠${NC} Network iceberg does not exist"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Service URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dremio UI:      http://localhost:9047"
echo "  MinIO Console:  http://localhost:9001"
echo "  MinIO API:      http://localhost:9000"
echo "  Nessie API:     http://localhost:19120/api/v2"
echo "  Nessie UI:      http://localhost:19120"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Health check complete!${NC}"

