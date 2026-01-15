# A Complete Dremio + Nessie + Iceberg Environment — Ready in One Command

*A training and demo environment for the modern Data Lakehouse stack. Clone, start, query.*

---

When I run training sessions or demos for Dremio, Nessie, and Apache Iceberg, I want participants to focus on the technology — not on infrastructure setup. The individual Docker images for each project work great, but getting them to work *together* requires configuration: connecting Dremio to Nessie, setting up MinIO buckets, configuring S3 credentials, creating users.

That's not complicated, but it takes time. Time that's better spent actually exploring what these technologies can do.

So I built a Docker Compose setup that handles all of that automatically. One command, and you have a fully configured Data Lakehouse environment ready for training, demos, or local development.

---

## The Stack: Dremio, Nessie, and MinIO

Before diving in, let me explain what we're working with — and why these components form such a powerful combination.

### The Data Lakehouse: Best of Both Worlds

For years, organizations had to choose between two approaches: **Data Warehouses** offered fast SQL queries and strong governance, but were expensive and locked you into proprietary formats. **Data Lakes** gave you cheap, scalable storage for any data format, but lacked the reliability and performance needed for analytics.

The **Data Lakehouse** combines the strengths of both. You store data in open file formats on cheap object storage (like a data lake), but with a metadata layer that provides the reliability, performance, and SQL interface you'd expect from a warehouse. No vendor lock-in. No expensive proprietary storage. Full control over your data.

This training environment implements exactly that architecture.

### Apache Iceberg — The Table Format

Apache Iceberg is the foundation that makes the lakehouse work. It's an open table format that sits between your query engine and your raw data files (typically Parquet).

What does that mean in practice? Iceberg tracks which files belong to which table, manages schema information, and maintains a complete history of changes. This enables features that were previously only available in traditional databases:

- **ACID Transactions**: Multiple writers can safely update the same table without corrupting data
- **Time Travel**: Query your data as it existed at any point in the past
- **Schema Evolution**: Add, rename, or remove columns without rewriting your entire dataset
- **Partition Evolution**: Change how your data is partitioned without migrating existing data
- **Hidden Partitioning**: Users write simple queries; Iceberg handles partition pruning automatically

The key insight is that Iceberg stores all of this as metadata files alongside your data. Your actual data remains in standard Parquet files — readable by any tool that understands Parquet. There's no proprietary format, no lock-in.

### MinIO — The Object Storage Layer

Every lakehouse needs storage. In production, that's typically AWS S3, Azure Blob Storage, or Google Cloud Storage. For local development and training, we use **MinIO** — an S3-compatible object storage system that runs anywhere.

MinIO implements the S3 API, which means any code or configuration that works with S3 works with MinIO. When you're ready to move to production, you change a URL and credentials — everything else stays the same.

In this setup, MinIO stores:
- The actual Parquet data files that contain your table data
- Iceberg metadata files that track table structure and history
- The complete version history of all your tables

The MinIO console (`http://localhost:9000`) lets you explore this storage directly, which is helpful for understanding how Iceberg organizes data under the hood.

### Project Nessie — The Git-Inspired Catalog

When you create an Iceberg table, something needs to know that the table exists, where its files are stored, and what schema it has. That's the job of a **catalog**.

Project Nessie is a catalog with a unique capability: it treats your entire data catalog like a **Git repository**. Every change — creating a table, inserting data, modifying schema — becomes a commit. And just like Git, you can:

- **Create branches**: Work on changes in isolation without affecting production data
- **Merge branches**: Bring changes from a development branch into main when ready
- **Create tags**: Mark specific points in time as releases or snapshots
- **View history**: See exactly what changed, when, and roll back if needed

This is transformative for data engineering workflows. Imagine being able to:
- Test a complex ETL pipeline on a branch, verify the results, then merge to production
- Create a tag before a major data migration, knowing you can always query that exact state
- Let multiple teams work on the same tables without stepping on each other's changes

Nessie tracks all this metadata with full transactional guarantees. When you merge a branch, it's atomic — either all changes apply or none do.

### Dremio — The Query Engine and UI

Dremio brings everything together. It's a high-performance SQL query engine that connects to Nessie (for catalog metadata) and MinIO (for data storage), providing a unified interface to your lakehouse.

But Dremio is more than just a query engine. It exposes all of Nessie's Git-like capabilities directly in its SQL interface:

```sql
-- Create a branch
CREATE BRANCH dev IN nessie;

-- Switch branches
USE BRANCH dev IN nessie;

-- Query a specific tag
SELECT * FROM nessie.sales AT TAG v1_release;

-- Merge branches
MERGE BRANCH dev INTO main IN nessie;
```

You don't need to learn a separate tool or API — branching, tagging, and time travel are all available through familiar SQL commands.

Dremio also provides:
- A web-based SQL editor with syntax highlighting and auto-completion
- Visual exploration of your catalog, tables, and branches
- Query history and performance insights
- Role-based access control for multi-user environments

### How They Fit Together

```
┌─────────────────────────────────────────────────────────────┐
│                         Dremio                              │
│                                                             │
│  • SQL Query Engine       • Branch/Tag Management           │
│  • Web UI                 • Access Control                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │     Nessie      │             │     MinIO       │
    │   (Catalog)     │             │  (Object Store) │
    │                 │             │                 │
    │ • Table schemas │             │ • Parquet files │
    │ • Branch/Tag    │             │ • Iceberg       │
    │   history       │             │   metadata      │
    │ • Commit log    │             │ • Version       │
    │                 │             │   history       │
    └─────────────────┘             └─────────────────┘
```

When you run a query in Dremio:
1. Dremio asks Nessie: "What files make up this table on this branch?"
2. Nessie returns the metadata — file locations, schema, partition info
3. Dremio reads the actual Parquet files from MinIO
4. Results come back to you

When you write data:
1. Dremio writes new Parquet files to MinIO
2. Dremio tells Nessie: "Here's the new state of this table"
3. Nessie creates a new commit with the updated metadata

The beauty is that each component is **independent and replaceable**:
- Swap MinIO for S3, and your data works the same way
- Use a different query engine that supports Nessie, and it sees the same tables
- Your Parquet files are standard files — export them, analyze them with Spark, do whatever you need

This is the promise of the open lakehouse: your data is yours, stored in open formats, accessible by any compatible tool.

---

## Why a Pre-Configured Setup?

Each component in this stack — Dremio, Nessie, MinIO — has excellent official Docker images. They're well-documented and production-ready. But when you want to use them *together* for training or demos, there's integration work to do:

- **Nessie** needs persistent storage configured (the default is in-memory)
- **MinIO** needs a bucket created with the right permissions
- **Dremio** needs a user account, and a Nessie source configured with S3 credentials

None of this is difficult. But when you're running a workshop with 20 participants, or giving a 30-minute demo, you don't want to spend the first 15 minutes on setup. You want to jump straight into `CREATE TABLE` and show what Iceberg can do.

That's what this repository provides: all the integration done upfront, so you can focus on the actual content.

---

## Getting Started

Clone the repository and start the environment:

```bash
git clone https://github.com/christianpfarr-dremio/iceberg-training.git
cd iceberg-training
docker-compose up -d
```

After 30 seconds, open `http://localhost:9047`, log in with `admin` / `password1` — and you're ready to go:

```sql
CREATE TABLE nessie.sales (
    order_id INT,
    customer VARCHAR,
    amount DECIMAL(10,2)
);

INSERT INTO nessie.sales VALUES (1, 'Acme Corp', 1500.00);

SELECT * FROM nessie.sales;
```

No manual setup. No "first you need to configure X". It just works.

![Dremio SQL Editor](images/dremio-ui-screenshot.png)
*The Dremio SQL editor with the Nessie catalog ready to use — no configuration needed*

---

## What Happens Under the Hood

The setup consists of three main components plus three init containers:

```
+-------------------------------------------------------------+
|                    Dremio (Port 9047)                       |
|              SQL Query Engine and UI                        |
+------------------------+------------------------------------+
                         |
            +------------+------------+
            |                         |
      +-----v------+           +------v---------+
      |   Nessie   |           |     MinIO      |
      |  (19120)   |           |    (9000)      |
      +-----+------+           +-------+--------+
            |                          |
      +-----v------+           +-------v--------+
      |  RocksDB   |           |     Data       |
      |   Volume   |           |    Volume      |
      +------------+           +----------------+
```

**The init containers are the trick:**

1. **nessie-init**: Creates a user with UID 185 and sets correct permissions on the volume.

2. **minio-init**: Automatically creates the `warehouse` bucket (versioning disabled — Iceberg handles its own versioning via metadata).

3. **dremio-init**: The most interesting piece. This container waits until all services are healthy, creates the admin user via REST API, logs in, and configures the Nessie source.

Everything automatic, everything idempotent.

---

## Why RocksDB Instead of In-Memory?

Many tutorials use Nessie with its default backend — which is in-memory. After `docker-compose down`, all branches, commits, and table metadata are gone.

This setup uses RocksDB:

```yaml
environment:
  - NESSIE_VERSION_STORE_TYPE=ROCKSDB
volumes:
  - nessie-data:/tmp/nessie-rocksdb-store
```

Your tables, branches, and the complete history survive restarts.

---

## The Permission Trap

Nessie runs as user `default` with UID 185. Docker volumes are created as root by default. Result: `Permission denied`.

The solution is an init container that runs *before* Nessie:

```yaml
nessie-init:
  image: alpine:latest
  command: sh -c "adduser -D -u 185 default && chown -R default:root /data"
  volumes:
    - nessie-data:/data
```

With `depends_on` and `condition: service_completed_successfully`, Nessie only starts after the permissions are fixed.

---

## Who Is This For?

The repository is called `iceberg-training` for a reason. This is a **training environment**, purpose-built to help developers and customers get started with Dremio, Nessie, and Apache Iceberg as quickly as possible.

**Typical use cases:**

- **Customer demos**: Jump straight into showing capabilities instead of configuring infrastructure
- **Developer onboarding**: New team members can experiment with a lakehouse architecture on day one
- **Workshops and training sessions**: Everyone in the room gets the same working environment
- **Proof of concepts**: Quickly validate whether this stack fits your use case
- **Learning**: Understand how Dremio, Nessie, and MinIO work together by actually using them

This is a **training setup**, not a production template. The default credentials are simple (`admin` / `password1`), there's no TLS, and no high availability. For production deployments, refer to the official documentation for each project.


---

## Hands-On: Exploring the Stack

Once the environment is running, you can explore all the key features directly from Dremio's SQL editor. Here are some examples to get you started.

### Create Some Test Data

```sql
-- Create a table on the main branch
CREATE TABLE nessie.sales (
    order_id INT,
    customer VARCHAR,
    amount DECIMAL(10,2),
    order_date DATE
);

INSERT INTO nessie.sales VALUES
    (1, 'Acme Corp', 1500.00, DATE '2024-01-10'),
    (2, 'Globex Inc', 2300.00, DATE '2024-01-11'),
    (3, 'Initech', 890.00, DATE '2024-01-12');

SELECT * FROM nessie.sales ORDER BY order_id;
```

Result:
```
order_id | customer   | amount  | order_date
---------|------------|---------|------------
1        | Acme Corp  | 1500.00 | 2024-01-10
2        | Globex Inc | 2300.00 | 2024-01-11
3        | Initech    | 890.00  | 2024-01-12
```

### Time Travel with Snapshots

Every change to an Iceberg table creates a new snapshot. You can query the history to see all snapshots:

```sql
SELECT * FROM TABLE(table_history('nessie.sales')) ORDER BY made_current_at DESC;
```

Result:
```
made_current_at     | snapshot_id         | parent_id           | is_current_ancestor
--------------------|---------------------|---------------------|--------------------
2024-01-15 17:30:02 | 4465122803571422774 | 3697355837526781938 | true
2024-01-15 17:30:01 | 3697355837526781938 | 1063678714522285507 | true
2024-01-15 17:30:00 | 1063678714522285507 | 1602227990585108066 | true
2024-01-15 17:29:59 | 1602227990585108066 | NULL                | true
```

Now you can use any snapshot ID to travel back in time:

```sql
-- First, get the current snapshot ID
-- (the first row from table_history is the current state)

-- Make a change
DELETE FROM nessie.sales WHERE amount < 1000;

-- Query the data BEFORE the delete using the snapshot ID you captured
SELECT * FROM nessie.sales AT SNAPSHOT '4465122803571422774' ORDER BY order_id;
```

The deleted row (Initech) is still accessible through the old snapshot — nothing is ever truly deleted until you explicitly expire snapshots.

### Schema Evolution

Add columns without rewriting existing data:

```sql
ALTER TABLE nessie.sales ADD COLUMNS (region VARCHAR);

-- Old rows get NULL, new rows get the value
INSERT INTO nessie.sales VALUES (4, 'Wayne Enterprises', 5000.00, DATE '2024-01-15', 'Northeast');

SELECT * FROM nessie.sales ORDER BY order_id;
```

Result:
```
order_id | customer          | amount   | order_date | region
---------|-------------------|----------|------------|----------
1        | Acme Corp         | 1500.00  | 2024-01-10 | NULL
2        | Globex Inc        | 2300.00  | 2024-01-11 | NULL
3        | Initech           | 890.00   | 2024-01-12 | NULL
4        | Wayne Enterprises | 5000.00  | 2024-01-15 | Northeast
```

### Branching — Git for Your Data

This is where Nessie shines. Create a branch, make changes in isolation, then merge back — just like Git, but for tables.

```sql
-- Create a development branch
CREATE BRANCH dev IN nessie;

-- Switch to the dev branch and make changes
USE BRANCH dev IN nessie;

INSERT INTO nessie.sales VALUES (5, 'Stark Industries', 12000.00, DATE '2024-01-15', 'West');
UPDATE nessie.sales SET amount = 1600.00 WHERE order_id = 1;

-- Check the dev branch — you'll see your changes
SELECT * FROM nessie.sales ORDER BY order_id;
```

On the dev branch, you now have 5 rows with the updated amount for order 1:

```
order_id | customer          | amount   | order_date | region
---------|-------------------|----------|------------|----------
1        | Acme Corp         | 1600.00  | 2024-01-10 | NULL
2        | Globex Inc        | 2300.00  | 2024-01-11 | NULL
3        | Initech           | 890.00   | 2024-01-12 | NULL
4        | Wayne Enterprises | 5000.00  | 2024-01-15 | Northeast
5        | Stark Industries  | 12000.00 | 2024-01-15 | West
```

```sql
-- When you're ready, merge dev into main
USE BRANCH main IN nessie;
MERGE BRANCH dev INTO main IN nessie;
```

### Time Travel — Query the Past

First, let's delete some data and then show how we can query previous states:

```sql
-- Delete low-value orders
DELETE FROM nessie.sales WHERE amount < 1000;

-- Current state shows only 4 rows (Initech is gone)
SELECT * FROM nessie.sales ORDER BY order_id;
```

```
order_id | customer          | amount   | order_date | region
---------|-------------------|----------|------------|----------
1        | Acme Corp         | 1600.00  | 2024-01-10 | NULL
2        | Globex Inc        | 2300.00  | 2024-01-11 | NULL
4        | Wayne Enterprises | 5000.00  | 2024-01-15 | Northeast
5        | Stark Industries  | 12000.00 | 2024-01-15 | West
```

```sql
-- Query table history to find snapshot IDs
SELECT * FROM TABLE(table_history('nessie.sales')) ORDER BY made_current_at DESC;

-- Time travel to see data before the DELETE (using the previous snapshot ID)
SELECT * FROM nessie.sales AT SNAPSHOT '1288762194691800129' ORDER BY order_id;
```

### Tagging — Named Snapshots for Easy Reference

Create immutable snapshots of your data at important points:

```sql
-- Tag the current state
CREATE TAG v1_0_release AT BRANCH main IN nessie;

-- Add more data after the tag
INSERT INTO nessie.sales VALUES (6, 'LexCorp', 8500.00, DATE '2024-01-20', 'South');

-- Current main shows 5 rows (includes LexCorp)
SELECT * FROM nessie.sales ORDER BY order_id;
```

```
order_id | customer          | amount   | order_date | region
---------|-------------------|----------|------------|----------
1        | Acme Corp         | 1600.00  | 2024-01-10 | NULL
2        | Globex Inc        | 2300.00  | 2024-01-11 | NULL
4        | Wayne Enterprises | 5000.00  | 2024-01-15 | Northeast
5        | Stark Industries  | 12000.00 | 2024-01-15 | West
6        | LexCorp           | 8500.00  | 2024-01-20 | South
```

```sql
-- Query the tagged version — 4 rows, no LexCorp
SELECT * FROM nessie.sales AT TAG v1_0_release ORDER BY order_id;
```

```
order_id | customer          | amount   | order_date | region
---------|-------------------|----------|------------|----------
1        | Acme Corp         | 1600.00  | 2024-01-10 | NULL
2        | Globex Inc        | 2300.00  | 2024-01-11 | NULL
4        | Wayne Enterprises | 5000.00  | 2024-01-15 | Northeast
5        | Stark Industries  | 12000.00 | 2024-01-15 | West
```

The tag preserves the exact state of your data at the moment it was created — regardless of what happens afterward. This is incredibly useful for auditing, compliance, or simply having a "known good" state to reference.

### See Your Changes in MinIO

Every SQL command you run in Dremio creates real files in MinIO. Open the MinIO console at `http://localhost:9001` (login: `admin` / `password1`) to see what's happening under the hood.

Navigate to **Buckets → warehouse** and you'll see your tables as folders. Each table gets a unique identifier appended to its name:

```
warehouse/
└── sales_db1f6567-a3f2-432e-8e2f-6e52f65007aa/
    ├── 1696df84-c52d-5780-.../0_0_0.parquet      # Initial INSERT
    ├── 1696df88-a5ff-aa9b-.../0_0_0.parquet      # After ADD COLUMNS + INSERT
    ├── 1696df89-777d-b4a2-.../0_0_0.parquet      # INSERT on dev branch
    ├── 1696df8a-4883-eb3a-.../0_0_0.parquet      # UPDATE on dev branch
    ├── 1696df8c-0749-0292-.../0_0_0.parquet      # DELETE result
    └── metadata/
        ├── 00000-...-metadata.json               # CREATE TABLE
        ├── 00001-...-metadata.json               # After INSERT
        ├── 00002-...-metadata.json               # After ADD COLUMNS
        ├── 00003-...-metadata.json               # After INSERT with region
        ├── ...
        ├── 00006-...-metadata.json               # Current state
        └── snap-...-avro                         # Snapshot manifests
```

**What you'll observe:**

- **After CREATE TABLE + INSERT**: 1 Parquet file, 5 metadata files (~22 KB total)
- **After ADD COLUMNS + INSERT**: 2 Parquet files, 9 metadata files (~45 KB total)
- **After branching, UPDATE, MERGE**: 4 Parquet files, 16 metadata files (~91 KB total)
- **After Time Travel + Tagging**: 6 Parquet files, 23 metadata files (~142 KB total)

Each operation adds files — nothing is modified in place. This immutability is what enables time travel and branching.

### See Your Tables and Branches in Nessie

Open the Nessie UI at `http://localhost:19120` to see the catalog side of things.

Click on **Tables** to see all registered Iceberg tables. Select `nessie / sales` to see:

- **Type**: ICEBERG_TABLE
- **Metadata Location**: Points to the current metadata file in MinIO, e.g., `s3://warehouse/sales_.../metadata/00006-...-metadata.json`

Use the branch dropdown to switch views. After the demo, you'll see:

- **Branches**: `main`, `dev`
- **Tags**: `v1_0_release`

The commit history shows each operation:
```
- DELETE on TABLE sales
- UPDATE on TABLE sales
- INSERT on TABLE sales
- INSERT on TABLE sales
- ALTER on TABLE sales
- INSERT on TABLE sales
- CREATE on TABLE sales
```

This is where you can see the connection: Nessie tracks which metadata file is current for each branch, and that metadata file (in MinIO) describes which Parquet files contain the data.

---

## Bonus: The Demo Script

All examples in this article are based on a fully automated Python script that you can run yourself. It executes every SQL command, validates the results, and shows you what's happening in MinIO and Nessie after each step.

Find it at `publications/article_demo.py` in the repository.

### What the Script Does

The script connects to all three systems and walks through the complete workflow:

```python
# Connect to Dremio via Arrow Flight
dremio = DremioClient()
dremio.connect()

# Check MinIO via S3 API
minio = MinIOClient()
tables = minio.list_tables()

# Query Nessie via REST API
nessie = NessieClient()
branches = nessie.get_branches()
```

After each SQL operation, it reports the state of all systems — so you can see exactly how many Parquet files were created, which metadata files exist, and what Nessie's commit log looks like.

### The Arrow Flight Connection

Dremio exposes an Arrow Flight endpoint for high-performance queries. Here's the core of how we connect and execute SQL:

```python
class DremioClient:
    def connect(self):
        location = flight.Location.for_grpc_tcp(DREMIO_HOST, DREMIO_FLIGHT_PORT)
        self.client = flight.FlightClient(location)
        self.token = self.client.authenticate_basic_token(
            DREMIO_USERNAME, DREMIO_PASSWORD
        )

    def execute(self, sql, description=None):
        flight_desc = flight.FlightDescriptor.for_command(sql)
        options = flight.FlightCallOptions(headers=[self.token])
        flight_info = self.client.get_flight_info(flight_desc, options=options)

        reader = self.client.do_get(
            flight_info.endpoints[0].ticket, options=options
        )
        return reader.read_all()  # Returns a PyArrow Table
```

This is the same interface you'd use in production code to query Dremio programmatically.

### Dynamic Snapshot Discovery

The script doesn't use hardcoded snapshot IDs. Instead, it queries the table history dynamically:

```python
# Query the table history to get snapshot IDs
result = dremio.execute(
    "SELECT * FROM TABLE(table_history('nessie.sales')) ORDER BY made_current_at DESC"
)

# Get the current snapshot ID (first row = latest)
current_snapshot_id = result.column('snapshot_id')[0].as_py()
print(f"Current snapshot ID: {current_snapshot_id}")

# Make a change
dremio.execute("DELETE FROM nessie.sales WHERE amount < 1000")

# Time travel to the snapshot we captured
result = dremio.execute(
    f"SELECT * FROM nessie.sales AT SNAPSHOT '{current_snapshot_id}' ORDER BY order_id"
)
```

This pattern — capture snapshot ID, make changes, query old snapshot — is how you'd implement audit trails or undo functionality in production.

### Observing File Growth in MinIO

One of the most instructive parts is watching how Iceberg's immutable design manifests as file growth:

```python
def get_table_stats(self, table_prefix):
    files = self.list_table_contents(table_prefix)
    parquet_files = [f for f in files if f['key'].endswith('.parquet')]
    metadata_files = [f for f in files if 'metadata' in f['key']]
    return {
        'parquet_files': len(parquet_files),
        'metadata_files': len(metadata_files),
        'total_size_bytes': sum(f['size'] for f in files)
    }
```

The script prints these stats after each operation, so you can see:
- **After CREATE + INSERT**: 1 Parquet, 5 metadata files (~22 KB)
- **After ADD COLUMNS + INSERT**: 2 Parquet, 9 metadata files (~45 KB)
- **After BRANCH + UPDATE + MERGE**: 4 Parquet, 16 metadata files (~91 KB)
- **After Time Travel + Tagging**: 6 Parquet, 23 metadata files (~142 KB)

### Running the Demo

Make sure the environment is running, then:

```bash
# Install dependencies
pip install pyarrow boto3 requests

# Run the full demo
python publications/article_demo.py
```

The script cleans up after itself, but you can comment out the cleanup section at the end if you want to explore the data in the UIs afterward.

---

## Links

- **Repository:** [github.com/christianpfarr-dremio/iceberg-training](https://github.com/christianpfarr-dremio/iceberg-training)
- **Apache Iceberg:** [iceberg.apache.org](https://iceberg.apache.org)
- **Project Nessie:** [projectnessie.org](https://projectnessie.org)
- **Dremio:** [docs.dremio.com](https://docs.dremio.com)

---

If this setup saved you time, leave a star on GitHub. And if you run into problems — issues are welcome.

---

## Medium Publication Info

**Recommended Tags:**
- `data-engineering`
- `apache-iceberg`
- `docker`
- `dremio`
- `data-lakehouse`

**Recommended Publications:**
- Towards Data Science
- Data Engineering with Dremio
- Better Programming

**Estimated Reading Time:** ~25 minutes

---

**Image to include:** Save the Dremio UI screenshot and insert it after the first SQL code block. Upload directly when publishing to Medium.