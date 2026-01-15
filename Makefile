.PHONY: help up down restart logs status health clean reset test

# Default target
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Apache Iceberg Training - Available Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  🚀 Starting & Stopping:"
	@echo "    make up         - Start all services"
	@echo "    make down       - Stop all services"
	@echo "    make restart    - Restart all services"
	@echo ""
	@echo "  📊 Monitoring:"
	@echo "    make status     - Show service status"
	@echo "    make logs       - Show logs (all services)"
	@echo "    make health     - Run health check"
	@echo ""
	@echo "  🧹 Cleanup:"
	@echo "    make clean      - Stop services and remove containers"
	@echo "    make reset      - Complete reset (removes volumes!)"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    make test       - Run full test suite"
	@echo ""
	@echo "  📝 Individual Service Logs:"
	@echo "    make logs-nessie"
	@echo "    make logs-minio"
	@echo "    make logs-dremio"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start all services
up:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@make health

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ Services stopped!"

# Restart all services
restart:
	@echo "🔄 Restarting all services..."
	docker-compose restart
	@echo "✅ Services restarted!"

# Show service status
status:
	@echo "📊 Service Status:"
	@docker-compose ps

# Show logs for all services
logs:
	docker-compose logs -f

# Show logs for individual services
logs-nessie:
	docker-compose logs -f nessie

logs-minio:
	docker-compose logs -f minio

logs-dremio:
	docker-compose logs -f dremio

# Run health check
health:
	@./health-check.sh

# Clean up (stop and remove containers)
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down
	@echo "✅ Cleanup complete!"

# Complete reset (WARNING: removes all data!)
reset:
	@echo "⚠️  WARNING: This will delete ALL data!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	@echo "🗑️  Removing all containers and volumes..."
	docker-compose down -v
	@echo "✅ Complete reset done!"
	@echo "Run 'make up' to start fresh"

# Test suite
test:
	@echo "🧪 Running test suite..."
	@echo ""
	@echo "1️⃣  Testing clean start..."
	@make reset
	@sleep 2
	@make up
	@sleep 10
	@echo ""
	@echo "2️⃣  Running health checks..."
	@make health
	@echo ""
	@echo "3️⃣  Testing restart (persistence check)..."
	@make restart
	@sleep 10
	@make health
	@echo ""
	@echo "✅ All tests passed!"

# Open service UIs in browser (macOS)
open-dremio:
	@open http://localhost:9047

open-minio:
	@open http://localhost:9001

open-nessie:
	@open http://localhost:19120

# Show service URLs
urls:
	@echo "🌐 Service URLs:"
	@echo "  Dremio UI:      http://localhost:9047"
	@echo "  MinIO Console:  http://localhost:9001"
	@echo "  MinIO API:      http://localhost:9000"
	@echo "  Nessie API:     http://localhost:19120/api/v2"
	@echo "  Nessie UI:      http://localhost:19120"

