#!/usr/bin/env python3
"""
Demonstrate Virtual Row Expansion for JSON Data
Shows how single rows with JSON arrays are expanded into individual item rows
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.delimited_field_processor import DelimitedFieldProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def demonstrate_virtual_expansion():
    """Demonstrate virtual row expansion with your exact example"""
    print("🚀 Virtual Row Expansion Demonstration")
    print("=" * 60)
    
    processor = DelimitedFieldProcessor()
    
    # Your example data: CASE203 with multiple items in JSON format
    sample_invoice = {
        'CASE_ID': 'CASE203',
        'BILL_DATE': '2025-05-30',
        'VENDOR_ID': 'V001',
        'AMOUNT': '7044.5',
        'BALANCE_AMOUNT': '7044.5',
        'STATUS': 'Pending',
        # JSON arrays - as stored in your database
        'ITEMS_DESCRIPTION': '["Office Chair", "Audit Report"]',
        'ITEMS_UNIT_PRICE': '[4463.3, 2581.2]',
        'ITEMS_QUANTITY': '[5, 5]'
    }
    
    print("📊 Original Database Row:")
    print(f"CASE_ID: {sample_invoice['CASE_ID']}")
    print(f"BILL_DATE: {sample_invoice['BILL_DATE']}")
    print(f"ITEMS_DESCRIPTION: {sample_invoice['ITEMS_DESCRIPTION']}")
    print(f"ITEMS_UNIT_PRICE: {sample_invoice['ITEMS_UNIT_PRICE']}")
    print(f"ITEMS_QUANTITY: {sample_invoice['ITEMS_QUANTITY']}")
    
    print("\n🔄 Processing Virtual Row Expansion...")
    
    # Process the row to expand items
    expanded_items = processor.process_item_row(sample_invoice)
    
    print(f"\n✅ Expanded into {len(expanded_items)} virtual rows:")
    print("-" * 60)
    
    for i, item in enumerate(expanded_items, 1):
        print(f"Virtual Row {i}:")
        print(f"  CASE_ID: {item['CASE_ID']}")
        print(f"  BILL_DATE: {item['BILL_DATE']}")
        print(f"  ITEM_DESCRIPTION: {item['ITEM_DESCRIPTION']}")
        print(f"  ITEM_UNIT_PRICE: {item['ITEM_UNIT_PRICE']}")
        print(f"  ITEM_QUANTITY: {item['ITEM_QUANTITY']}")
        print(f"  ITEM_LINE_TOTAL: ${item['ITEM_LINE_TOTAL']:.2f}")
        print()
    
    # Test with simulated query results
    print("🎯 Testing with Query Results Format:")
    print("-" * 40)
    
    # Simulate query results format
    query_results = {
        'success': True,
        'data': [
            ['CASE203', '2025-05-30', 'V001', '7044.5', '["Office Chair", "Audit Report"]', '[4463.3, 2581.2]', '[5, 5]']
        ],
        'columns': ['CASE_ID', 'BILL_DATE', 'VENDOR_ID', 'AMOUNT', 'ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY']
    }
    
    expanded_results = processor.expand_results_with_items(query_results)
    
    if expanded_results.get('items_expanded'):
        print(f"✅ Query Results Expanded Successfully!")
        print(f"Original rows: {expanded_results['original_row_count']}")
        print(f"Expanded rows: {expanded_results['expanded_row_count']}")
        print(f"Total line items: {expanded_results['total_line_items']}")
        
        print("\n📋 Expanded Query Results:")
        for i, row in enumerate(expanded_results['data'][:2], 1):  # Show first 2 rows
            print(f"Row {i}: {dict(zip(expanded_results['columns'], row))}")
    
    # Test item query detection
    print("\n🔍 Testing Item Query Detection:")
    print("-" * 40)
    
    test_queries = [
        "What items did I purchase in CASE203?",
        "Show me the Office Chair details",
        "What's the total cost of Audit Report?",
        "List all items with quantity 5"
    ]
    
    for query in test_queries:
        analysis = processor.enhance_llm_understanding_for_items(query)
        print(f"Query: '{query}'")
        print(f"  -> Item Query: {analysis['is_item_query']}")
        print(f"  -> Intent: {analysis['query_intent']}")
        print(f"  -> Products: {analysis['extracted_products']}")
        print()

def test_different_json_formats():
    """Test various JSON formats that might exist in the database"""
    print("\n🧪 Testing Different JSON Formats:")
    print("=" * 60)
    
    processor = DelimitedFieldProcessor()
    
    test_cases = [
        {
            'name': 'Standard JSON Arrays',
            'descriptions': '["Office Chair", "Audit Report"]',
            'prices': '[4463.3, 2581.2]',
            'quantities': '[5, 5]'
        },
        {
            'name': 'JSON with Spaces',
            'descriptions': '[ "Office Chair" , "Audit Report" ]',
            'prices': '[ 4463.3 , 2581.2 ]',
            'quantities': '[ 5 , 5 ]'
        },
        {
            'name': 'Mixed String/Number JSON',
            'descriptions': '["Office Chair", "Audit Report"]',
            'prices': '["4463.3", "2581.2"]',
            'quantities': '["5", "5"]'
        },
        {
            'name': 'CSV Fallback Format',
            'descriptions': 'Office Chair,Audit Report',
            'prices': '4463.3,2581.2',
            'quantities': '5,5'
        }
    ]
    
    for case in test_cases:
        print(f"\n📝 Testing: {case['name']}")
        
        # Parse each field
        desc_parsed = processor.parse_delimited_field(case['descriptions'])
        price_parsed = processor.parse_numeric_delimited_field(case['prices'])
        qty_parsed = processor.parse_numeric_delimited_field(case['quantities'])
        
        print(f"  Descriptions: {desc_parsed}")
        print(f"  Prices: {price_parsed}")
        print(f"  Quantities: {qty_parsed}")
        
        # Verify parsing worked
        if len(desc_parsed) == len(price_parsed) == len(qty_parsed) == 2:
            print("  ✅ Parsing successful - all arrays have matching lengths")
        else:
            print(f"  ❌ Parsing issue - lengths don't match: {len(desc_parsed)}, {len(price_parsed)}, {len(qty_parsed)}")

def demonstrate_user_queries():
    """Show how users can ask independent questions about items"""
    print("\n💬 User Query Examples:")
    print("=" * 60)
    
    processor = DelimitedFieldProcessor()
    
    example_queries = [
        {
            'question': 'What items did I buy?',
            'explanation': 'Lists all individual items across all invoices'
        },
        {
            'question': 'Show me Office Chair purchases',
            'explanation': 'Finds specific product across all expanded rows'
        },
        {
            'question': 'What is the most expensive item?',
            'explanation': 'Compares unit prices across all expanded items'
        },
        {
            'question': 'How many items have quantity greater than 3?',
            'explanation': 'Filters expanded rows by quantity criteria'
        },
        {
            'question': 'What\'s the total value of all Audit Reports?',
            'explanation': 'Aggregates line totals for specific products'
        }
    ]
    
    for example in example_queries:
        print(f"🗣️  User asks: \"{example['question']}\"")
        print(f"   💡 Result: {example['explanation']}")
        
        # Show query analysis
        analysis = processor.enhance_llm_understanding_for_items(example['question'])
        print(f"   🎯 Detected as: {analysis['query_intent']} (Item Query: {analysis['is_item_query']})")
        
        if analysis['extracted_products']:
            print(f"   🔍 Products detected: {analysis['extracted_products']}")
        print()

def main():
    """Main demonstration function"""
    print("🎉 FinOpsys Virtual Row Expansion Demo")
    print("Showing how JSON arrays are expanded for independent item queries")
    print("=" * 80)
    
    try:
        # Main demonstration
        demonstrate_virtual_expansion()
        
        # Test different formats
        test_different_json_formats()
        
        # Show user query examples
        demonstrate_user_queries()
        
        print("\n🎊 Demo completed successfully!")
        print("\n📚 Key Benefits:")
        print("✅ Single database rows with JSON arrays → Multiple virtual item rows")
        print("✅ Users can ask about specific products independently")
        print("✅ Automatic detection of item-level vs invoice-level queries")
        print("✅ Support for various JSON and CSV formats")
        print("✅ Statistical analysis and aggregations work on individual items")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
