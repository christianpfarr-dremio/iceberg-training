#!/usr/bin/env python3
"""
Integration tests for Dremio table operations with Nessie catalog.
Tests CREATE, INSERT, SELECT, UPDATE, DELETE operations using Arrow Flight.
"""

import os
import sys
import pyarrow.flight as flight

DREMIO_HOST = os.getenv("DREMIO_HOST", "localhost")
DREMIO_PORT = int(os.getenv("DREMIO_PORT", "32010"))
USERNAME = os.getenv("DREMIO_USERNAME", "admin")
PASSWORD = os.getenv("DREMIO_PASSWORD", "password1")

class DremioFlightClient:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.token = None

    def connect(self):
        """Connect to Dremio via Arrow Flight"""
        print(f"🔐 Connecting to Dremio Flight at {self.host}:{self.port}...")

        # Create Flight client
        location = flight.Location.for_grpc_tcp(self.host, self.port)
        self.client = flight.FlightClient(location)

        # Authenticate
        bearer_token = self.client.authenticate_basic_token(self.username, self.password)
        self.token = bearer_token

        print(f"✅ Connected successfully\n")

    def execute_sql(self, sql, description=""):
        """Execute SQL via Arrow Flight"""
        if description:
            print(f"=== {description} ===")

        print(f"SQL: {sql}\n")

        # Create Flight descriptor
        flight_desc = flight.FlightDescriptor.for_command(sql)

        # Create call options with bearer token
        options = flight.FlightCallOptions(headers=[self.token])

        # Execute query and get results
        flight_info = self.client.get_flight_info(flight_desc, options=options)

        # For DDL statements (CREATE, DROP, etc.), there might be no results
        if not flight_info.endpoints:
            print(f"✅ Command completed successfully!\n")
            return None

        # Read results for SELECT queries
        reader = self.client.do_get(flight_info.endpoints[0].ticket, options=options)

        # Convert to PyArrow Table
        table = reader.read_all()

        print(f"✅ Query completed successfully!\n")
        return table

    def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()

def print_results(table):
    """Pretty print Arrow Table results"""
    if table is None or table.num_rows == 0:
        print("Query returned 0 rows\n")
        return

    print("Results:")
    print("-" * 80)

    # Print header
    column_names = table.column_names
    print(" | ".join(f"{col:15}" for col in column_names))
    print("-" * 80)

    # Print rows
    for i in range(table.num_rows):
        row = [str(table.column(j)[i].as_py()) for j in range(table.num_columns)]
        print(" | ".join(f"{val:15}" for val in row))

    print("-" * 80)
    print(f"Total rows: {table.num_rows}\n")

    return table

def main():
    print("🧪 Starting Dremio Table Operations Tests (Arrow Flight)\n")

    client = None
    try:
        # Initialize client
        client = DremioFlightClient(DREMIO_HOST, DREMIO_PORT, USERNAME, PASSWORD)
        client.connect()
        
        # Test 1: Create table
        print("=" * 80)
        print("TEST 1: CREATE TABLE")
        print("=" * 80)
        client.execute_sql(
            """CREATE TABLE nessie.test_employees (
                id INT,
                name VARCHAR,
                department VARCHAR,
                salary DECIMAL(10,2)
            ) PARTITION BY (department)""",
            "Creating test table"
        )

        # Test 2: Insert data
        print("=" * 80)
        print("TEST 2: INSERT DATA")
        print("=" * 80)
        client.execute_sql(
            """INSERT INTO nessie.test_employees VALUES
                (1, 'Alice Johnson', 'Engineering', 95000.00),
                (2, 'Bob Smith', 'Sales', 75000.00),
                (3, 'Charlie Brown', 'Engineering', 88000.00),
                (4, 'Diana Prince', 'Marketing', 82000.00),
                (5, 'Eve Davis', 'Sales', 71000.00)""",
            "Inserting test data"
        )

        # Test 3: Select all data
        print("=" * 80)
        print("TEST 3: SELECT ALL DATA")
        print("=" * 80)
        results = client.execute_sql(
            "SELECT * FROM nessie.test_employees ORDER BY id",
            "Querying all employees"
        )
        print_results(results)

        # Verify row count
        if results.num_rows != 5:
            raise Exception(f"Expected 5 rows, got {results.num_rows}")

        # Test 4: Select with filter
        print("=" * 80)
        print("TEST 4: SELECT WITH FILTER")
        print("=" * 80)
        results = client.execute_sql(
            "SELECT * FROM nessie.test_employees WHERE department = 'Engineering' ORDER BY id",
            "Querying Engineering employees"
        )
        print_results(results)

        # Verify filtered results
        if results.num_rows != 2:
            raise Exception(f"Expected 2 Engineering employees, got {results.num_rows}")

        # Test 5: Aggregate query
        print("=" * 80)
        print("TEST 5: AGGREGATE QUERY")
        print("=" * 80)
        results = client.execute_sql(
            """SELECT department,
                      COUNT(*) as employee_count,
                      AVG(salary) as avg_salary,
                      MAX(salary) as max_salary
               FROM nessie.test_employees
               GROUP BY department
               ORDER BY department""",
            "Calculating department statistics"
        )
        print_results(results)

        # Test 6: Update data
        print("=" * 80)
        print("TEST 6: UPDATE DATA")
        print("=" * 80)
        client.execute_sql(
            "UPDATE nessie.test_employees SET salary = 100000.00 WHERE id = 1",
            "Updating Alice's salary"
        )

        # Verify update
        results = client.execute_sql(
            "SELECT * FROM nessie.test_employees WHERE id = 1",
            "Verifying update"
        )
        print_results(results)

        updated_salary = results.column("salary")[0].as_py()
        if float(updated_salary) != 100000.00:
            raise Exception(f"Expected salary 100000.00, got {updated_salary}")

        # Test 7: Delete data
        print("=" * 80)
        print("TEST 7: DELETE DATA")
        print("=" * 80)
        client.execute_sql(
            "DELETE FROM nessie.test_employees WHERE department = 'Sales'",
            "Deleting Sales employees"
        )

        # Verify deletion
        results = client.execute_sql(
            "SELECT * FROM nessie.test_employees ORDER BY id",
            "Verifying deletion"
        )
        print_results(results)

        if results.num_rows != 3:
            raise Exception(f"Expected 3 rows after deletion, got {results.num_rows}")

        # Test 8: Drop table
        print("=" * 80)
        print("TEST 8: DROP TABLE")
        print("=" * 80)
        client.execute_sql(
            "DROP TABLE nessie.test_employees",
            "Dropping test table"
        )

        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    sys.exit(main())

