#!/usr/bin/env python3
"""
CSV Data Import Script for FinOpsysAI PostgreSQL Database
Imports data from ai_invoice.csv into the PostgreSQL ai_invoice table
"""

import os
import sys
import psycopg2
import csv
import json
from datetime import datetime
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

def parse_date(date_str):
    """Parse date string in DD-MM-YYYY format or return None if empty"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d-%m-%Y').date()
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}', setting to None")
        return None

def parse_decimal(value_str):
    """Parse decimal value or return None if empty"""
    if not value_str or value_str.strip() == '':
        return None
    try:
        return float(value_str.strip())
    except ValueError:
        print(f"Warning: Could not parse decimal '{value_str}', setting to None")
        return None

def parse_json_array(json_str):
    """Parse JSON array string or return None if empty"""
    if not json_str or json_str.strip() == '':
        return None
    try:
        # Replace double quotes with proper JSON format
        cleaned_str = json_str.strip()
        if cleaned_str.startswith('"') and cleaned_str.endswith('"'):
            cleaned_str = cleaned_str[1:-1]  # Remove outer quotes
        
        # Parse as JSON
        parsed = json.loads(cleaned_str)
        return json.dumps(parsed)  # Return as JSON string for PostgreSQL JSONB
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Could not parse JSON '{json_str}': {e}, setting to None")
        return None

def clear_existing_data():
    """Clear existing data from ai_invoice table"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute(f"DELETE FROM {POSTGRES_SCHEMA}.ai_invoice")
        conn.commit()
        
        # Reset sequence if exists
        cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_SCHEMA}.ai_invoice")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Cleared existing data from ai_invoice table")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing existing data: {str(e)}")
        return False

def import_csv_data(csv_file_path):
    """Import data from CSV file into PostgreSQL"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Prepare insert statement
        insert_sql = f"""
        INSERT INTO {POSTGRES_SCHEMA}.ai_invoice (
            case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
            decline_date, receiving_date, approveddate1, approveddate2,
            amount, balance_amount, paid, total_tax, subtotal,
            items_description, items_unit_price, items_quantity,
            status, decline_reason, department
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Read and process CSV file
        imported_count = 0
        error_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 since row 1 is header
                try:
                    # Parse and prepare data
                    data = [
                        row['case_id'].strip() if row['case_id'] else None,
                        row['bill_id'].strip() if row['bill_id'] else None,
                        row['customer_id'].strip() if row['customer_id'] else None,
                        row['vendor_id'].strip() if row['vendor_id'] else None,
                        parse_date(row['due_date']),
                        parse_date(row['bill_date']),
                        parse_date(row['decline_date']),
                        parse_date(row['receiving_date']),
                        parse_date(row['approveddate1']),
                        parse_date(row['approveddate2']),
                        parse_decimal(row['amount']),
                        parse_decimal(row['balance_amount']),
                        parse_decimal(row['paid']),
                        parse_decimal(row['total_tax']),
                        parse_decimal(row['subtotal']),
                        parse_json_array(row['items_description']),
                        parse_json_array(row['items_unit_price']),
                        parse_json_array(row['items_quantity']),
                        row['status'].strip() if row['status'] else None,
                        row['decline_reason'].strip() if row['decline_reason'] else None,
                        row['department'].strip() if row['department'] else None
                    ]
                    
                    # Insert data
                    cursor.execute(insert_sql, data)
                    imported_count += 1
                    
                    if imported_count % 50 == 0:
                        print(f"📊 Imported {imported_count} records...")
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error importing row {row_num}: {str(e)}")
                    print(f"   Row data: {row}")
                    continue
        
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Import completed!")
        print(f"   📊 Successfully imported: {imported_count} records")
        print(f"   ❌ Errors: {error_count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        return False

def verify_import():
    """Verify the imported data"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DATABASE
        )
        cursor = conn.cursor()
        
        # Check total count
        cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_SCHEMA}.ai_invoice")
        total_count = cursor.fetchone()[0]
        
        # Check distinct vendors
        cursor.execute(f"SELECT DISTINCT vendor_id FROM {POSTGRES_SCHEMA}.ai_invoice ORDER BY vendor_id")
        vendors = [row[0] for row in cursor.fetchall()]
        
        # Check distinct statuses
        cursor.execute(f"SELECT status, COUNT(*) FROM {POSTGRES_SCHEMA}.ai_invoice GROUP BY status ORDER BY status")
        statuses = cursor.fetchall()
        
        # Check sample records
        cursor.execute(f"SELECT case_id, vendor_id, amount, status FROM {POSTGRES_SCHEMA}.ai_invoice LIMIT 5")
        sample_records = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 Import Verification:")
        print(f"   Total records: {total_count}")
        print(f"   Unique vendors: {vendors}")
        print(f"   Status distribution:")
        for status, count in statuses:
            print(f"     - {status}: {count}")
        
        print(f"\n📋 Sample records:")
        for record in sample_records:
            print(f"     {record[0]} | {record[1]} | ${record[2]} | {record[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

def main():
    """Main import function"""
    csv_file_path = r"c:\Users\pixot\OneDrive\Desktop\ai_invoice.csv"
    
    print("🚀 Starting CSV Import for FinOpsysAI PostgreSQL Database")
    print("=" * 60)
    
    print(f"📋 Configuration:")
    print(f"   Host: {POSTGRES_HOST}")
    print(f"   Port: {POSTGRES_PORT}")
    print(f"   User: {POSTGRES_USER}")
    print(f"   Database: {POSTGRES_DATABASE}")
    print(f"   Schema: {POSTGRES_SCHEMA}")
    print(f"   CSV File: {csv_file_path}")
    print("=" * 60)
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    # Step 1: Clear existing data
    print("\n🧹 Step 1: Clearing existing data...")
    if not clear_existing_data():
        print("❌ Failed to clear existing data. Exiting.")
        sys.exit(1)
    
    # Step 2: Import CSV data
    print("\n📥 Step 2: Importing CSV data...")
    if not import_csv_data(csv_file_path):
        print("❌ Failed to import CSV data. Exiting.")
        sys.exit(1)
    
    # Step 3: Verify import
    print("\n🔍 Step 3: Verifying import...")
    if not verify_import():
        print("❌ Failed to verify import. Check your data.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 CSV Import completed successfully!")
    print("✅ Your data is now available in the PostgreSQL database")
    print("=" * 60)

if __name__ == "__main__":
    main()
