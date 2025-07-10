#!/usr/bin/env python3
"""
Direct database test to see actual data
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    database=os.getenv('POSTGRES_DATABASE', 'finopsys_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD'),
    port=int(os.getenv('POSTGRES_PORT', '5432'))
)

cursor = conn.cursor()

# Check the actual data
print("Sample data from ai_invoice:")
print("=" * 60)
cursor.execute("""
    SELECT case_id, items_description, items_unit_price, items_quantity
    FROM ai_invoice 
    WHERE items_description IS NOT NULL 
    ORDER BY case_id DESC
    LIMIT 10
""")

rows = cursor.fetchall()
for row in rows:
    print(f"CASE_ID: {row[0]}")
    print(f"items_description: {row[1]}")
    print(f"items_unit_price: {row[2]}")
    print(f"items_quantity: {row[3]}")
    print("-" * 40)

# Check for data with multiple items (array length > 1)
print("\nChecking for multi-item data:")
print("=" * 60)
cursor.execute("""
    SELECT case_id, items_description, items_unit_price, items_quantity
    FROM ai_invoice 
    WHERE jsonb_array_length(items_description) > 1
    LIMIT 5
""")

multi_item_rows = cursor.fetchall()
if multi_item_rows:
    print(f"Found {len(multi_item_rows)} multi-item invoices:")
    for row in multi_item_rows:
        print(f"CASE_ID: {row[0]}")
        print(f"items_description: {row[1]}")
        print(f"items_unit_price: {row[2]}")
        print(f"items_quantity: {row[3]}")
        print("-" * 40)
else:
    print("No multi-item invoices found")

# Check for single item data
print("\nChecking for single-item data:")
print("=" * 60)
cursor.execute("""
    SELECT case_id, items_description, items_unit_price, items_quantity
    FROM ai_invoice 
    WHERE jsonb_array_length(items_description) = 1
    LIMIT 5
""")

json_rows = cursor.fetchall()
if json_rows:
    print(f"Found {len(json_rows)} single-item invoices:")
    for row in json_rows:
        print(f"CASE_ID: {row[0]}")
        print(f"items_description: {row[1]}")
        print(f"items_unit_price: {row[2]}")
        print(f"items_quantity: {row[3]}")
        print("-" * 40)
else:
    print("No single-item invoices found")

cursor.close()
conn.close()
