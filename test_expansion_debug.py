#!/usr/bin/env python3
"""
Debug script to understand why invoice item expansion isn't working properly
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment
load_dotenv()

# Import our modules
from config import Config
from utils.delimited_field_processor import DelimitedFieldProcessor

# Add the streamlit src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'streamlit', 'src'))
from app import PostgreSQLManager

def test_expansion():
    """Test the expansion logic with actual database data"""
    print("🔍 Testing Invoice Item Expansion")
    print("=" * 50)
    
    # Initialize components
    db_config = Config()
    db_manager = PostgreSQLManager()
    db_manager.connect()
    processor = DelimitedFieldProcessor()
    
    # Test with a simple query that should have items
    test_query = "SELECT case_id, items_description, items_unit_price, items_quantity FROM ai_invoice LIMIT 3"
    
    print(f"Executing query: {test_query}")
    result = db_manager.execute_vendor_query(test_query)
    
    if not result.get('success'):
        print(f"❌ Query failed: {result.get('error')}")
        return
    
    print(f"✅ Query succeeded. Got {len(result['data'])} rows")
    print(f"Columns: {result['columns']}")
    
    # Print raw data to understand the format
    print("\n📊 Raw Data:")
    for i, row in enumerate(result['data']):
        print(f"Row {i+1}:")
        for j, col in enumerate(result['columns']):
            print(f"  {col}: {row[j]}")
        print()
    
    # Test expansion
    print("🔄 Testing Expansion...")
    expanded_result = processor.expand_results_with_items(result)
    
    print(f"Original rows: {len(result['data'])}")
    print(f"Expanded rows: {len(expanded_result['data'])}")
    print(f"Items expanded: {expanded_result.get('items_expanded', False)}")
    
    if expanded_result.get('items_expanded'):
        print(f"✅ Expansion successful!")
        print(f"New columns: {expanded_result['columns']}")
        
        # Show first few expanded rows
        print("\n📋 Sample Expanded Data:")
        for i, row in enumerate(expanded_result['data'][:5]):
            print(f"Expanded Row {i+1}:")
            for j, col in enumerate(expanded_result['columns']):
                print(f"  {col}: {row[j]}")
            print()
    else:
        print("❌ Expansion failed or not needed")
        
        # Debug why expansion failed
        has_item_columns = any(col in processor.item_columns for col in result['columns'])
        print(f"Has item columns: {has_item_columns}")
        print(f"Item columns: {processor.item_columns}")
        
        if has_item_columns:
            print("🔍 Debugging individual row processing...")
            df = pd.DataFrame(result['data'], columns=result['columns'])
            
            for idx, row in df.iterrows():
                print(f"\nProcessing row {idx+1}:")
                row_dict = row.to_dict()
                
                # Check each item column
                for col in processor.item_columns:
                    if col in row_dict:
                        value = row_dict[col]
                        print(f"  {col}: {value} (type: {type(value)})")
                        
                        if col == 'items_description':
                            parsed = processor.parse_delimited_field(value)
                            print(f"    Parsed: {parsed}")
                        elif col in ['items_unit_price', 'items_quantity']:
                            parsed = processor.parse_numeric_delimited_field(value)
                            print(f"    Parsed: {parsed}")
                
                # Process the row
                item_rows = processor.process_item_row(row_dict)
                print(f"  Generated {len(item_rows)} item rows")
                
                for item_idx, item_row in enumerate(item_rows):
                    print(f"    Item {item_idx + 1}: {item_row.get('ITEM_DESCRIPTION', '')}")

if __name__ == "__main__":
    test_expansion()
