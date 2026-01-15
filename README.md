# Apache Iceberg Training Setup
## Dremio + Nessie + MinIO with Persistent Storage

This setup provides a complete local environment for Apache Iceberg training with:
- **Nessie** - Git-like catalog for Data Lakehouse
- **MinIO** - S3-compatible object storage
- **Dremio** - SQL query engine and data virtualization platform

## 🎯 Improvements over Original Setup

✅ **Persistent Data Storage** - All configurations and data survive restarts
✅ **RocksDB Backend for Nessie** - Instead of in-memory store
✅ **Disabled Authentication** - No OIDC warnings
✅ **Docker Volumes** - Automatic data persistence for all services

## 📋 Prerequisites

- **Docker** installed ([docker.com](https://docker.com))
- At least **8 GB RAM** available
- Ports **9000, 9001, 9047, 19120** must be free

## 🚀 Quick Start

### 1. Start Services

```bash
# Start all services in background
docker-compose up -d

# Or start individually (for debugging)
docker-compose up dremio
docker-compose up minio
docker-compose up nessie
```

### 2. Wait for Services to be Ready

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f
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
2. Create your Dremio account (first-time setup)
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

All data is stored in Docker volumes:

| Service | Volume Name | Stores |
|---------|-------------|--------|
| Nessie | `iceberg-training_nessie-data` | Catalog metadata, branches, commits |
| MinIO | `iceberg-training_minio-data` | S3 objects, Iceberg table data |
| Dremio | `iceberg-training_dremio-data` | Users, data sources, reflections |

### Managing Volumes

```bash
# List volumes
docker volume ls

# Inspect volume details
docker volume inspect iceberg-training_nessie-data

# Delete all data and start fresh
docker-compose down -v
docker-compose up -d
```

## 🔧 Useful Commands

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

## 🌐 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Dremio UI | http://localhost:9047 | Query Engine & Data Catalog UI |
| MinIO Console | http://localhost:9000 | Object Storage UI |
| MinIO API | http://localhost:9000 | S3-compatible API |
| Nessie API | http://localhost:19120/api/v2 | Catalog REST API |
| Nessie UI | http://localhost:19120 | Nessie Web UI |

## 🐛 Troubleshooting

### Nessie shows OIDC warnings
✅ **Solved** - The warnings are harmless and don't affect functionality.

### Dremio forgets configurations after restart
✅ **Solved** - Persistent volumes are configured.

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

