#!/usr/bin/env python3
"""
Demo script for the Medium article: Dremio + Nessie + Iceberg Training Environment

This script executes all SQL commands from the article and validates the results
by checking MinIO (via S3 API) and Nessie (via REST API) status.

Requirements: pip install pyarrow boto3 requests
"""

import os
import sys
import time
import json
import pyarrow.flight as flight
import boto3
from botocore.client import Config
import requests

# Configuration
DREMIO_HOST = os.getenv("DREMIO_HOST", "localhost")
DREMIO_FLIGHT_PORT = int(os.getenv("DREMIO_FLIGHT_PORT", "32010"))
DREMIO_USERNAME = os.getenv("DREMIO_USERNAME", "admin")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "password1")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password1")
MINIO_BUCKET = "warehouse"

NESSIE_ENDPOINT = os.getenv("NESSIE_ENDPOINT", "http://localhost:19120")


class DremioClient:
    """Arrow Flight client for Dremio"""

    def __init__(self):
        self.client = None
        self.token = None

    def connect(self):
        print(f"🔗 Connecting to Dremio at {DREMIO_HOST}:{DREMIO_FLIGHT_PORT}...")
        location = flight.Location.for_grpc_tcp(DREMIO_HOST, DREMIO_FLIGHT_PORT)
        self.client = flight.FlightClient(location)
        self.token = self.client.authenticate_basic_token(DREMIO_USERNAME, DREMIO_PASSWORD)
        print("✅ Connected to Dremio\n")

    def execute(self, sql, description=None):
        if description:
            print(f"📝 {description}")
        print(f"   SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")

        flight_desc = flight.FlightDescriptor.for_command(sql)
        options = flight.FlightCallOptions(headers=[self.token])
        flight_info = self.client.get_flight_info(flight_desc, options=options)

        if not flight_info.endpoints:
            print("   ✅ Command executed\n")
            return None

        reader = self.client.do_get(flight_info.endpoints[0].ticket, options=options)
        table = reader.read_all()
        print(f"   ✅ Returned {table.num_rows} rows\n")
        return table

    def close(self):
        if self.client:
            self.client.close()


class MinIOClient:
    """S3 client for MinIO"""

    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )

    def list_tables(self, only_non_empty=False):
        """List all table folders in the warehouse bucket"""
        response = self.s3.list_objects_v2(Bucket=MINIO_BUCKET, Delimiter='/')
        folders = []
        for prefix in response.get('CommonPrefixes', []):
            folder = prefix['Prefix'].rstrip('/')
            if only_non_empty:
                # Check if folder has any files
                check = self.s3.list_objects_v2(
                    Bucket=MINIO_BUCKET, Prefix=folder + '/', MaxKeys=1
                )
                if check.get('KeyCount', 0) == 0:
                    continue
            folders.append(folder)
        return folders

    def list_table_contents(self, table_prefix):
        """List all files in a table folder"""
        response = self.s3.list_objects_v2(Bucket=MINIO_BUCKET, Prefix=table_prefix)
        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'modified': obj['LastModified'].isoformat()
            })
        return files

    def get_table_stats(self, table_prefix):
        """Get statistics for a table"""
        files = self.list_table_contents(table_prefix)
        parquet_files = [f for f in files if f['key'].endswith('.parquet')]
        metadata_files = [f for f in files if 'metadata' in f['key']]
        return {
            'total_files': len(files),
            'parquet_files': len(parquet_files),
            'metadata_files': len(metadata_files),
            'total_size_bytes': sum(f['size'] for f in files)
        }

    def delete_table_files(self, table_prefix):
        """Delete all files in a table folder (cleanup after DROP TABLE)"""
        files = self.list_table_contents(table_prefix)
        if not files:
            return 0

        # S3 delete_objects expects a list of {'Key': ...}
        objects_to_delete = [{'Key': f['key']} for f in files]

        # Delete in batches of 1000 (S3 limit)
        deleted_count = 0
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i+1000]
            self.s3.delete_objects(
                Bucket=MINIO_BUCKET,
                Delete={'Objects': batch}
            )
            deleted_count += len(batch)

        return deleted_count

    def delete_empty_prefixes(self, prefix_filter='sales_'):
        """Delete empty folder markers (MinIO creates these for 'folders')"""
        response = self.s3.list_objects_v2(Bucket=MINIO_BUCKET, Delimiter='/')
        deleted = 0
        for prefix in response.get('CommonPrefixes', []):
            folder = prefix['Prefix']
            if not folder.startswith(prefix_filter):
                continue
            # Check if folder is empty
            check = self.s3.list_objects_v2(
                Bucket=MINIO_BUCKET, Prefix=folder, MaxKeys=1
            )
            if check.get('KeyCount', 0) == 0:
                # Delete the folder marker object itself
                self.s3.delete_object(Bucket=MINIO_BUCKET, Key=folder)
                self.s3.delete_object(Bucket=MINIO_BUCKET, Key=folder.rstrip('/'))
                deleted += 1
        return deleted

    def cleanup_sales_tables(self):
        """Remove all sales_* folders from previous runs"""
        tables = self.list_tables()
        total_deleted = 0
        for table in tables:
            if table.startswith('sales_'):
                count = self.delete_table_files(table)
                if count > 0:
                    total_deleted += count
                    print(f"   Deleted {count} files from {table}")
        # Also remove empty folder markers
        self.delete_empty_prefixes('sales_')
        return total_deleted


class NessieClient:
    """REST API client for Nessie"""

    def __init__(self):
        self.base_url = f"{NESSIE_ENDPOINT}/api/v2"

    def get_branches(self):
        """Get all branches"""
        response = requests.get(f"{self.base_url}/trees")
        response.raise_for_status()
        refs = response.json().get('references', [])
        return [r for r in refs if r.get('type') == 'BRANCH']

    def get_tags(self):
        """Get all tags"""
        response = requests.get(f"{self.base_url}/trees")
        response.raise_for_status()
        refs = response.json().get('references', [])
        return [r for r in refs if r.get('type') == 'TAG']

    def get_tables(self, branch='main'):
        """Get all tables on a branch"""
        response = requests.get(f"{self.base_url}/trees/{branch}/entries")
        response.raise_for_status()
        return response.json().get('entries', [])

    def get_commit_log(self, branch='main', max_entries=5):
        """Get recent commits on a branch"""
        response = requests.get(f"{self.base_url}/trees/{branch}/history")
        response.raise_for_status()
        entries = response.json().get('logEntries', [])
        return entries[:max_entries]


def print_table(table, max_rows=10):
    """Pretty print an Arrow table"""
    if table is None or table.num_rows == 0:
        print("   (no rows)")
        return

    cols = table.column_names
    print("   " + " | ".join(f"{c:15}" for c in cols))
    print("   " + "-" * (17 * len(cols)))

    for i in range(min(table.num_rows, max_rows)):
        row = [str(table.column(j)[i].as_py())[:15] for j in range(table.num_columns)]
        print("   " + " | ".join(f"{v:15}" for v in row))

    if table.num_rows > max_rows:
        print(f"   ... and {table.num_rows - max_rows} more rows")
    print()


def check_minio_status(minio, description):
    """Check and print MinIO status"""
    print(f"\n📦 MinIO Status: {description}")
    tables = minio.list_tables(only_non_empty=True)
    if not tables:
        print("   No tables found in warehouse bucket")
        return

    found_any = False
    for table in tables:
        if 'sales' in table.lower():
            stats = minio.get_table_stats(table)
            # Only show folders that have files
            if stats['total_files'] > 0:
                found_any = True
                print(f"   Table folder: {table}")
                print(f"   - Parquet files: {stats['parquet_files']}")
                print(f"   - Metadata files: {stats['metadata_files']}")
                print(f"   - Total size: {stats['total_size_bytes']} bytes")

    if not found_any:
        print("   No sales tables found")


def check_nessie_status(nessie, description):
    """Check and print Nessie status"""
    print(f"\n🌿 Nessie Status: {description}")

    branches = nessie.get_branches()
    print(f"   Branches: {[b['name'] for b in branches]}")

    tags = nessie.get_tags()
    if tags:
        print(f"   Tags: {[t['name'] for t in tags]}")

    tables = nessie.get_tables('main')
    if tables:
        print(f"   Tables on main: {[e['name']['elements'][-1] for e in tables]}")


def main():
    print("=" * 70)
    print("🚀 Dremio + Nessie + Iceberg Demo Script")
    print("   This script demonstrates all features from the Medium article")
    print("=" * 70)
    print()

    dremio = DremioClient()
    minio = MinIOClient()
    nessie = NessieClient()

    try:
        dremio.connect()

        # Cleanup from previous runs
        print("🧹 Cleanup: Removing any existing test data...")
        try:
            dremio.execute("DROP TABLE IF EXISTS nessie.sales")
        except:
            pass
        try:
            dremio.execute("DROP BRANCH IF EXISTS dev IN nessie")
        except:
            pass
        try:
            dremio.execute("DROP TAG IF EXISTS v1_0_release IN nessie")
        except:
            pass

        # Clean up MinIO files from previous runs
        print("🧹 Cleaning up MinIO files from previous runs...")
        deleted = minio.cleanup_sales_tables()
        if deleted > 0:
            print(f"   ✅ Removed {deleted} orphaned files\n")
        else:
            print("   ✅ No orphaned files found\n")

        # ============================================================
        # STEP 1: Create table and insert data
        # ============================================================
        print("=" * 70)
        print("STEP 1: Create Table and Insert Data")
        print("=" * 70)

        dremio.execute("""
            CREATE TABLE nessie.sales (
                order_id INT,
                customer VARCHAR,
                amount DECIMAL(10,2),
                order_date DATE
            )
        """, "Creating sales table")

        dremio.execute("""
            INSERT INTO nessie.sales VALUES
                (1, 'Acme Corp', 1500.00, DATE '2024-01-10'),
                (2, 'Globex Inc', 2300.00, DATE '2024-01-11'),
                (3, 'Initech', 890.00, DATE '2024-01-12')
        """, "Inserting initial data")

        result = dremio.execute("SELECT * FROM nessie.sales ORDER BY order_id", "Querying data")
        print_table(result)

        check_minio_status(minio, "After CREATE and INSERT")
        check_nessie_status(nessie, "After CREATE and INSERT")

        # ============================================================
        # STEP 2: Schema Evolution
        # ============================================================
        print("\n" + "=" * 70)
        print("STEP 2: Schema Evolution - Add Column")
        print("=" * 70)

        dremio.execute("ALTER TABLE nessie.sales ADD COLUMNS (region VARCHAR)", "Adding region column")

        dremio.execute("""
            INSERT INTO nessie.sales VALUES
                (4, 'Wayne Enterprises', 5000.00, DATE '2024-01-15', 'Northeast')
        """, "Inserting row with new column")

        result = dremio.execute("SELECT * FROM nessie.sales ORDER BY order_id", "Querying with new schema")
        print_table(result)

        check_minio_status(minio, "After Schema Evolution")

        # ============================================================
        # STEP 3: Branching
        # ============================================================
        print("\n" + "=" * 70)
        print("STEP 3: Branching - Git for Your Data")
        print("=" * 70)

        dremio.execute("CREATE BRANCH dev IN nessie", "Creating dev branch")
        check_nessie_status(nessie, "After CREATE BRANCH")

        # Note: USE BRANCH changes the session context for subsequent queries
        # We use AT BRANCH for explicit reads to ensure correct data
        dremio.execute("USE BRANCH dev IN nessie", "Switching to dev branch")

        dremio.execute("""
            INSERT INTO nessie.sales AT BRANCH dev VALUES
                (5, 'Stark Industries', 12000.00, DATE '2024-01-15', 'West')
        """, "Inserting on dev branch")

        dremio.execute(
            "UPDATE nessie.sales AT BRANCH dev SET amount = 1600.00 WHERE order_id = 1",
            "Updating on dev branch"
        )

        print("\n📊 Data on DEV branch:")
        result = dremio.execute("SELECT * FROM nessie.sales AT BRANCH dev ORDER BY order_id")
        print_table(result)

        print("📊 Data on MAIN branch (unchanged):")
        result = dremio.execute("SELECT * FROM nessie.sales AT BRANCH main ORDER BY order_id")
        print_table(result)

        dremio.execute("MERGE BRANCH dev INTO main IN nessie", "Merging dev into main")

        print("📊 Data on MAIN after merge:")
        result = dremio.execute("SELECT * FROM nessie.sales AT BRANCH main ORDER BY order_id")
        print_table(result)

        check_minio_status(minio, "After Branching and Merge")
        check_nessie_status(nessie, "After Branching and Merge")

        # ============================================================
        # STEP 4: Time Travel with Snapshots
        # ============================================================
        print("\n" + "=" * 70)
        print("STEP 4: Time Travel with Snapshots")
        print("=" * 70)

        # Query the table history to get snapshot IDs
        print("📸 Querying table history to find snapshots...")
        result = dremio.execute(
            "SELECT * FROM TABLE(table_history('nessie.sales')) ORDER BY made_current_at DESC",
            "Getting table history"
        )
        print_table(result)

        # Get the current snapshot ID (latest)
        current_snapshot_id = result.column('snapshot_id')[0].as_py()
        print(f"   ➡️  Current snapshot ID: {current_snapshot_id}\n")

        # Make a change
        dremio.execute(
            "DELETE FROM nessie.sales WHERE amount < 1000",
            "Deleting low-value orders (Initech)"
        )

        print("📊 Data on MAIN after DELETE:")
        result = dremio.execute("SELECT * FROM nessie.sales ORDER BY order_id")
        print_table(result)

        # Query the history again to show the new snapshot
        print("📸 Table history after DELETE:")
        result = dremio.execute(
            "SELECT * FROM TABLE(table_history('nessie.sales')) ORDER BY made_current_at DESC",
            "Getting updated table history"
        )
        print_table(result)

        new_snapshot_id = result.column('snapshot_id')[0].as_py()
        print(f"   ➡️  New snapshot ID: {new_snapshot_id}")
        print(f"   ➡️  Previous snapshot ID: {current_snapshot_id}\n")

        # Time travel using the snapshot ID we captured earlier
        print(f"📊 Time travel: Data AT SNAPSHOT '{current_snapshot_id}' (before DELETE):")
        result = dremio.execute(
            f"SELECT * FROM nessie.sales AT SNAPSHOT '{current_snapshot_id}' ORDER BY order_id"
        )
        print_table(result)

        # ============================================================
        # STEP 5: Tagging a Snapshot
        # ============================================================
        print("\n" + "=" * 70)
        print("STEP 5: Tagging - Named Snapshots for Easy Reference")
        print("=" * 70)

        # Create a tag at the current state
        dremio.execute(
            "CREATE TAG v1_0_release AT BRANCH main IN nessie",
            "Creating tag at current state"
        )
        check_nessie_status(nessie, "After CREATE TAG")

        # Insert new data after the tag
        dremio.execute("""
            INSERT INTO nessie.sales VALUES
                (6, 'LexCorp', 8500.00, DATE '2024-01-20', 'South')
        """, "Inserting new row after tag")

        print("📊 Current data (includes new row):")
        result = dremio.execute("SELECT * FROM nessie.sales ORDER BY order_id")
        print_table(result)

        print("📊 Data AT TAG v1_0_release (before INSERT):")
        result = dremio.execute(
            "SELECT * FROM nessie.sales AT TAG v1_0_release ORDER BY order_id"
        )
        print_table(result)

        check_minio_status(minio, "After Time Travel and Tagging")

        # ============================================================
        # FINAL STATUS
        # ============================================================
        print("\n" + "=" * 70)
        print("FINAL: Complete System Status")
        print("=" * 70)

        print("\n📦 MinIO - All files in warehouse bucket:")
        tables = minio.list_tables(only_non_empty=True)
        for table in tables:
            if 'sales' in table.lower():
                files = minio.list_table_contents(table)
                print(f"\n   {table}/")
                for f in files:
                    key = f['key'].replace(table + '/', '  ')
                    print(f"      {key} ({f['size']} bytes)")

        print("\n🌿 Nessie - Complete status:")
        branches = nessie.get_branches()
        for b in branches:
            print(f"   Branch: {b['name']} (hash: {b['hash'][:8]}...)")

        tags = nessie.get_tags()
        for t in tags:
            print(f"   Tag: {t['name']} (hash: {t['hash'][:8]}...)")

        print("\n   Recent commits on main:")
        commits = nessie.get_commit_log('main', 5)
        for c in commits:
            msg = c.get('commitMeta', {}).get('message', 'No message')[:50]
            print(f"      - {msg}")

        # ============================================================
        # CLEANUP
        # ============================================================
        print("\n" + "=" * 70)
        print("CLEANUP: Removing test data")
        print("=" * 70)

        dremio.execute("DROP TAG v1_0_release IN nessie", "Dropping tag")
        dremio.execute("DROP BRANCH dev IN nessie", "Dropping dev branch")
        dremio.execute("DROP TABLE nessie.sales", "Dropping sales table")

        # Important: DROP TABLE only removes the Nessie reference.
        # The actual files in MinIO remain until explicitly deleted.
        print("\n📦 Cleaning up MinIO files...")
        deleted = minio.cleanup_sales_tables()
        print(f"   ✅ Removed {deleted} files from MinIO")

        print("\n" + "=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        dremio.close()


if __name__ == "__main__":
    sys.exit(main())
