#!/usr/bin/env python3
"""
Test expansion with real database data to confirm it's working
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from utils.delimited_field_processor import DelimitedFieldProcessor

load_dotenv()

def test_with_real_data():
    """Test expansion with real database data"""
    print("🔍 Testing Expansion with Real Database Data")
    print("=" * 60)
    
    # Connect to database
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        database=os.getenv('POSTGRES_DATABASE', 'finopsys_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD'),
        port=int(os.getenv('POSTGRES_PORT', '5432'))
    )
    
    cursor = conn.cursor()
    
    # Get some real multi-item data
    cursor.execute("""
        SELECT case_id, items_description, items_unit_price, items_quantity
        FROM ai_invoice 
        WHERE jsonb_array_length(items_description) > 1
        LIMIT 2
    """)
    
    rows = cursor.fetchall()
    columns = ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    
    # Convert to the format expected by the processor
    real_data = {
        'success': True,
        'data': rows,
        'columns': columns
    }
    
    print(f"📊 Original data from database:")
    for i, row in enumerate(rows):
        print(f"Row {i+1}:")
        print(f"  CASE_ID: {row[0]}")
        print(f"  items_description: {row[1]}")
        print(f"  items_unit_price: {row[2]}")
        print(f"  items_quantity: {row[3]}")
        
        # Calculate expected expansion
        desc_len = len(row[1]) if row[1] else 0
        price_len = len(row[2]) if row[2] else 0
        qty_len = len(row[3]) if row[3] else 0
        max_items = max(desc_len, price_len, qty_len)
        print(f"  Expected expansion: {max_items} items")
        print()
    
    # Test expansion
    processor = DelimitedFieldProcessor()
    expanded_result = processor.expand_results_with_items(real_data)
    
    print(f"🔄 Expansion Results:")
    print(f"Original rows: {len(real_data['data'])}")
    print(f"Expanded rows: {len(expanded_result['data'])}")
    print(f"Items expanded: {expanded_result.get('items_expanded', False)}")
    
    if expanded_result.get('items_expanded'):
        print(f"✅ Expansion successful!")
        print(f"Columns: {expanded_result['columns']}")
        
        print(f"\n📋 Expanded data (first 10 rows):")
        for i, row in enumerate(expanded_result['data'][:10]):
            row_dict = dict(zip(expanded_result['columns'], row))
            print(f"Row {i+1}:")
            print(f"  CASE_ID: {row_dict.get('case_id', '')}")
            print(f"  ITEM_INDEX: {row_dict.get('ITEM_INDEX', '')}")
            print(f"  ITEM_DESCRIPTION: {row_dict.get('ITEM_DESCRIPTION', '')}")
            print(f"  ITEM_UNIT_PRICE: {row_dict.get('ITEM_UNIT_PRICE', '')}")
            print(f"  ITEM_QUANTITY: {row_dict.get('ITEM_QUANTITY', '')}")
            print(f"  ITEM_LINE_TOTAL: {row_dict.get('ITEM_LINE_TOTAL', '')}")
            print()
    else:
        print("❌ Expansion failed")
    
    # Show the message that would be displayed to users
    original_count = len(real_data['data'])
    expanded_count = len(expanded_result['data'])
    
    print(f"📝 User Message:")
    print(f"✅ Expanded from {original_count} invoices to {expanded_count} individual line items")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_with_real_data()
