# Apache Iceberg Training Setup
## Dremio + Nessie + MinIO with Persistent Storage

This setup provides a complete local environment for Apache Iceberg training with:
- **Nessie** - Git-like catalog for Data Lakehouse
- **MinIO** - S3-compatible object storage
- **Dremio** - SQL query engine and data virtualization platform

## 🎯 Improvements over Original Setup

✅ **Persistent Data Storage** - All configurations and data survive restarts
✅ **RocksDB Backend for Nessie** - Instead of in-memory store
✅ **Proper File Permissions** - Fixed Nessie volume ownership (UID 185)
✅ **Disabled Authentication** - No OIDC warnings
✅ **Docker Volumes** - Automatic data persistence for all services
✅ **Tested Persistence** - Verified that tables and configurations survive container restarts

## 📋 Prerequisites

- **Docker** installed ([docker.com](https://docker.com))
- At least **8 GB RAM** available
- Ports **9000, 9001, 9047, 19120** must be free

## 🚀 Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# Start all services
make up

# Check health
make health

# View logs
make logs

# Stop services
make down

# See all available commands
make help
```

### Option 2: Using Docker Compose

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Verify Services are Ready

```bash
# Run automated health check
./health-check.sh

# Or check manually
curl http://localhost:19120/api/v2/config  # Nessie
curl http://localhost:9000/minio/health/live  # MinIO
curl http://localhost:9047  # Dremio
```

Services are ready when:
- **Dremio**: `http://localhost:9047` is accessible
- **MinIO**: `http://localhost:9000` is accessible
- **Nessie**: `http://localhost:19120/api/v2/config` responds

## ⚙️ Configuration

### MinIO Setup (Object Storage)

1. Open **http://localhost:9000** in your browser
2. Login with:
   - **Username**: `admin`
   - **Password**: `password`
3. Click on **"Buckets"** in the left menu
4. Create a new bucket named **`warehouse`**

### Dremio Setup (Query Engine)

1. Open **http://localhost:9047** in your browser
2. **Login with auto-created admin user:**
   - **Username**: `admin`
   - **Password**: `admin123` (or value from `DREMIO_ADMIN_PASSWORD` env var)
3. Click on **"Add Source"** → **"Nessie"**

#### Nessie Source Configuration:

**General Tab:**
- **Name**: `nessie`
- **Endpoint URL**: `http://nessie:19120/api/v2`
- **Authentication**: `none`

**Storage Tab:**
- **Access Key**: `admin`
- **Secret Key**: `password`
- **Root Path**: `/warehouse`
- **Connection Properties** (important!):
  ```
  fs.s3a.path.style.access = true
  fs.s3a.endpoint = minio:9000
  dremio.s3.compat = true
  ```
- ⚠️ **UNCHECK "Encrypt connection"**

4. Click **"Save"**

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Dremio (Port 9047)                   │
│              SQL Query Engine & UI                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├──────────────┐
                 │              │
        ┌────────▼─────┐  ┌────▼──────────┐
        │    Nessie    │  │     MinIO     │
        │ (Port 19120) │  │ (Port 9000)   │
        │              │  │               │
        │  Catalog &   │  │  S3-Storage   │
        │  Versioning  │  │  (Warehouse)  │
        └──────────────┘  └───────────────┘
             │                    │
        ┌────▼────┐          ┌────▼────┐
        │ RocksDB │          │  Data   │
        │ Volume  │          │ Volume  │
        └─────────┘          └─────────┘
```

## 💾 Persistent Data

All data is stored in Docker volumes and survives container restarts:

| Service | Volume Name | Stores | Owner |
|---------|-------------|--------|-------|
| Nessie | `iceberg-training_nessie-data` | Catalog metadata, branches, commits | UID 185 (default) |
| MinIO | `iceberg-training_minio-data` | S3 objects, Iceberg table data | UID 1000 (minio-user) |
| Dremio | `iceberg-training_dremio-data` | Users, data sources, reflections | UID 999 (dremio) |

### How Persistence Works

1. **Nessie**: Uses RocksDB to store catalog metadata in `/tmp/nessie-rocksdb-store/`
   - An init container creates the volume with correct permissions (UID 185)
   - All branches, commits, and table metadata are persisted

2. **MinIO**: Stores all S3 objects (Iceberg data files) in `/data`
   - Parquet files, metadata files, and manifest files are persisted

3. **Dremio**: Stores user accounts, data sources, and query history in `/opt/dremio/data`
   - Your Nessie source configuration is persisted
   - No need to reconfigure after restart

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect volume details
docker volume inspect iceberg-training_nessie-data

# Check Nessie data files
docker exec nessie ls -lah /tmp/nessie-rocksdb-store/

# Delete all data and start fresh
docker-compose down -v
docker-compose up -d
```

## 🔧 Useful Commands

### Using Makefile

```bash
# Start/Stop
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services

# Monitoring
make status          # Show service status
make logs            # Show all logs
make logs-nessie     # Show Nessie logs only
make logs-minio      # Show MinIO logs only
make logs-dremio     # Show Dremio logs only
make health          # Run health check

# Cleanup
make clean           # Stop and remove containers
make reset           # Complete reset (removes volumes!)

# Testing
make test            # Run full test suite

# Utilities
make urls            # Show all service URLs
make open-dremio     # Open Dremio UI in browser (macOS)
make open-minio      # Open MinIO UI in browser (macOS)
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f [service-name]

# Check status
docker-compose ps

# Access container shell
docker exec -it nessie /bin/bash
docker exec -it minio /bin/bash
docker exec -it dremio /bin/bash
```

### Environment Variables

You can customize ports and settings using environment variables:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# Then start services
docker-compose up -d
```

## 🌐 Service URLs & Credentials

| Service | URL | Username | Password | Description |
|---------|-----|----------|----------|-------------|
| Dremio UI | http://localhost:9047 | `admin` | `admin123` | Query Engine & Data Catalog UI |
| MinIO Console | http://localhost:9001 | `minioadmin` | `minioadmin` | Object Storage UI |
| MinIO API | http://localhost:9000 | `minioadmin` | `minioadmin` | S3-compatible API |
| Nessie API | http://localhost:19120/api/v2 | - | - | Catalog REST API |
| Nessie UI | http://localhost:19120 | - | - | Nessie Web UI |

> **Note**: Default credentials are automatically configured. Change them via environment variables in `.env` file for production use.

## 🐛 Troubleshooting

### Nessie shows OIDC warnings
✅ **Solved** - Authentication is disabled via `QUARKUS_OIDC_ENABLED=false`.

### Dremio forgets configurations after restart
✅ **Solved** - Persistent volumes are configured for all services.

### Nessie volume permission errors
✅ **Solved** - Init container creates proper user (UID 185) matching Nessie's default user.
The Nessie image uses user `default` (UID 185, GID 0) in versions < 0.96.0.

### Port already in use
```bash
# Check which process is using the port
lsof -i :9047  # Dremio
lsof -i :9000  # MinIO
lsof -i :19120 # Nessie

# Or change the ports in docker-compose.yml
```

### Services won't start
```bash
# Check logs
docker-compose logs [service-name]

# Recreate containers
docker-compose down
docker-compose up -d --force-recreate
```

## 📚 Additional Resources

- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [Project Nessie Documentation](https://projectnessie.org/)
- [Dremio Documentation](https://docs.dremio.com/)
- [MinIO Documentation](https://min.io/docs/)

## 🔄 Starting Fresh

If you want to completely reset:

```bash
# Delete all containers and volumes
docker-compose down -v

# Start all services again
docker-compose up -d

# Wait for everything to be ready
docker-compose logs -f
```

Then repeat the configuration steps (MinIO bucket + Dremio source).

## 📝 License

This setup is based on open-source components:
- Apache Iceberg (Apache License 2.0)
- Project Nessie (Apache License 2.0)
- Dremio OSS (Apache License 2.0)
- MinIO (GNU AGPL v3.0)

