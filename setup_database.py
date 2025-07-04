#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for FinOpsysAI
Creates the database and ai_invoice table with the specified schema
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Harsh@123')
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'finopsys_db')
POSTGRES_SCHEMA = os.getenv('POSTGRES_SCHEMA', 'public')

def create_database():
    """Create the FinOpsys database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (POSTGRES_DATABASE,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"🔨 Creating database '{POSTGRES_DATABASE}'...")
            cursor.execute(f'CREATE DATABASE "{POSTGRES_DATABASE}"')
            print(f"✅ Database '{POSTGRES_DATABASE}' created successfully")
        else:
            print(f"✅ Database '{POSTGRES_DATABASE}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        return False

def create_ai_invoice_table():
    """Create the ai_invoice table with the specified schema"""
    try:
        # Connect to the FinOpsys database
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Create the ai_invoice table
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {POSTGRES_SCHEMA}.ai_invoice (
            case_id TEXT PRIMARY KEY,
            bill_id TEXT,
            customer_id TEXT,
            vendor_id TEXT,
            due_date DATE,
            bill_date DATE,
            decline_date DATE,
            receiving_date DATE,
            approveddate1 DATE,
            approveddate2 DATE,
            amount NUMERIC(18,2),
            balance_amount NUMERIC(18,2),
            paid NUMERIC(18,2),
            total_tax NUMERIC(18,2),
            subtotal NUMERIC(18,2),
            items_description JSONB,
            items_unit_price JSONB,
            items_quantity JSONB,
            status TEXT,
            decline_reason TEXT,
            department TEXT
        );
        """
        
        print(f"🔨 Creating ai_invoice table in schema '{POSTGRES_SCHEMA}'...")
        cursor.execute(create_table_sql)
        
        # Create indexes for better performance
        indexes_sql = [
            f"CREATE INDEX IF NOT EXISTS idx_ai_invoice_vendor_id ON {POSTGRES_SCHEMA}.ai_invoice(vendor_id);",
            f"CREATE INDEX IF NOT EXISTS idx_ai_invoice_case_id ON {POSTGRES_SCHEMA}.ai_invoice(case_id);",
            f"CREATE INDEX IF NOT EXISTS idx_ai_invoice_status ON {POSTGRES_SCHEMA}.ai_invoice(status);",
            f"CREATE INDEX IF NOT EXISTS idx_ai_invoice_bill_date ON {POSTGRES_SCHEMA}.ai_invoice(bill_date);",
            f"CREATE INDEX IF NOT EXISTS idx_ai_invoice_due_date ON {POSTGRES_SCHEMA}.ai_invoice(due_date);"
        ]
        
        print("🔨 Creating performance indexes...")
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ ai_invoice table and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False

def insert_sample_data():
    """Insert sample data for testing"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Insert sample data
        sample_data_sql = f"""
        INSERT INTO {POSTGRES_SCHEMA}.ai_invoice (
            case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
            amount, balance_amount, paid, total_tax, subtotal,
            items_description, items_unit_price, items_quantity,
            status, department
        ) VALUES
        ('CASE001', 'BILL001', 'CUST001', 'VENDOR001', '2024-08-15', '2024-07-15',
         1500.00, 0.00, 1500.00, 150.00, 1350.00,
         '["Cloud Storage Service", "Technical Support"]'::jsonb,
         '[99.99, 199.99]'::jsonb,
         '[10, 5]'::jsonb,
         'Paid', 'IT'),
        ('CASE002', 'BILL002', 'CUST002', 'VENDOR001', '2024-08-20', '2024-07-20',
         2500.00, 500.00, 2000.00, 250.00, 2250.00,
         '["Software License", "Maintenance"]'::jsonb,
         '[1999.99, 500.00]'::jsonb,
         '[1, 12]'::jsonb,
         'Partial', 'IT'),
        ('CASE003', 'BILL003', 'CUST003', 'VENDOR002', '2024-08-25', '2024-07-25',
         750.00, 750.00, 0.00, 75.00, 675.00,
         '["Office Supplies"]'::jsonb,
         '[25.00]'::jsonb,
         '[30]'::jsonb,
         'Pending', 'Admin')
        ON CONFLICT (case_id) DO NOTHING;
        """
        
        print("🔨 Inserting sample data...")
        cursor.execute(sample_data_sql)
        
        # Check how many rows were inserted
        cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_SCHEMA}.ai_invoice")
        count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Sample data inserted. Total rows in table: {count}")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {str(e)}")
        return False

def test_connection():
    """Test database connection and table access"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_SCHEMA}.ai_invoice")
        count = cursor.fetchone()[0]
        
        # Test vendor-specific query
        cursor.execute(f"SELECT DISTINCT vendor_id FROM {POSTGRES_SCHEMA}.ai_invoice")
        vendors = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Connection test successful!")
        print(f"   Total records: {count}")
        print(f"   Available vendors: {[v[0] for v in vendors]}")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🚀 Starting PostgreSQL Database Setup for FinOpsysAI")
    print("=" * 50)
    
    print(f"📋 Configuration:")
    print(f"   Host: {POSTGRES_HOST}")
    print(f"   Port: {POSTGRES_PORT}")
    print(f"   User: {POSTGRES_USER}")
    print(f"   Database: {POSTGRES_DATABASE}")
    print(f"   Schema: {POSTGRES_SCHEMA}")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Create table
    if not create_ai_invoice_table():
        print("❌ Failed to create table. Exiting.")
        sys.exit(1)
    
    # Step 3: Insert sample data
    if not insert_sample_data():
        print("⚠️ Failed to insert sample data, but continuing...")
    
    # Step 4: Test connection
    if not test_connection():
        print("❌ Failed connection test. Check your configuration.")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("✅ You can now run the FinOpsysAI application")
    print("=" * 50)

if __name__ == "__main__":
    main()
