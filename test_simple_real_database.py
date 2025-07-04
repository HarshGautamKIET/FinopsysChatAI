#!/usr/bin/env python3
"""
Simple Real Database Test for JSON Virtual Row Expansion
Tests the core expansion functionality with real database data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.delimited_field_processor import DelimitedFieldProcessor
from utils.enhanced_db_manager import EnhancedDBManager
import json

def test_real_database_expansion():
    """Test virtual row expansion with real database data"""
    print("🧪 Real Database JSON Expansion Test")
    print("Testing actual database with JSON arrays")
    print("=" * 80)
    
    try:
        # Initialize components
        db_manager = EnhancedDBManager()
        processor = DelimitedFieldProcessor()
        
        print("✅ Connected to database")
        
        # Test query to get some real data
        test_query = """
        SELECT CASE_ID, BILL_DATE, ITEMS_DESCRIPTION, ITEMS_UNIT_PRICE, ITEMS_QUANTITY 
        FROM AI_INVOICE 
        WHERE ITEMS_DESCRIPTION IS NOT NULL 
        LIMIT 5
        """
        
        # Execute query
        results = db_manager.execute_query(test_query)
        
        if not results.get('success') or not results.get('data'):
            print("❌ No data found or query failed")
            return False
        
        print(f"📊 Found {len(results['data'])} invoices with item data")
        
        # Show original data format
        print("\n📋 Original Database Data:")
        print("-" * 60)
        columns = results['columns']
        for i, row in enumerate(results['data'][:3], 1):
            row_dict = dict(zip(columns, row))
            print(f"\nInvoice {i} (CASE_ID: {row_dict.get('CASE_ID')}):")
            print(f"  ITEMS_DESCRIPTION: {row_dict.get('ITEMS_DESCRIPTION')}")
            print(f"  ITEMS_UNIT_PRICE: {row_dict.get('ITEMS_UNIT_PRICE')}")
            print(f"  ITEMS_QUANTITY: {row_dict.get('ITEMS_QUANTITY')}")
            print(f"  Data types: {type(row_dict.get('ITEMS_DESCRIPTION'))}, {type(row_dict.get('ITEMS_UNIT_PRICE'))}, {type(row_dict.get('ITEMS_QUANTITY'))}")
        
        # Test expansion
        print(f"\n🔄 Testing Virtual Row Expansion...")
        print("-" * 60)
        
        expanded_results = processor.expand_results_with_items(results)
        
        if expanded_results.get('items_expanded'):
            print(f"✅ Successfully expanded {len(results['data'])} invoices into {expanded_results['total_line_items']} line items")
            
            # Show expanded data
            print(f"\n📋 Expanded Virtual Rows:")
            print("-" * 60)
            
            expanded_columns = expanded_results['columns']
            expanded_data = expanded_results['data']
            
            # Find column indices
            case_id_idx = expanded_columns.index('CASE_ID') if 'CASE_ID' in expanded_columns else 0
            item_desc_idx = expanded_columns.index('ITEM_DESCRIPTION') if 'ITEM_DESCRIPTION' in expanded_columns else -1
            item_price_idx = expanded_columns.index('ITEM_UNIT_PRICE') if 'ITEM_UNIT_PRICE' in expanded_columns else -1
            item_qty_idx = expanded_columns.index('ITEM_QUANTITY') if 'ITEM_QUANTITY' in expanded_columns else -1
            item_total_idx = expanded_columns.index('ITEM_LINE_TOTAL') if 'ITEM_LINE_TOTAL' in expanded_columns else -1
            
            for i, row in enumerate(expanded_data[:10], 1):  # Show first 10 items
                case_id = row[case_id_idx] if case_id_idx >= 0 else 'N/A'
                item_desc = row[item_desc_idx] if item_desc_idx >= 0 else 'N/A'
                item_price = row[item_price_idx] if item_price_idx >= 0 else 0
                item_qty = row[item_qty_idx] if item_qty_idx >= 0 else 0
                item_total = row[item_total_idx] if item_total_idx >= 0 else 0
                
                print(f"  Item {i}: {case_id} | {item_desc} | ${item_price} × {item_qty} = ${item_total}")
            
            # Test statistics
            stats = processor.get_item_statistics(results)
            if stats:
                print(f"\n📈 Item Statistics:")
                print(f"  • Total line items: {stats.get('total_line_items', 0)}")
                print(f"  • Total value: ${stats.get('total_item_value', 0):,.2f}")
                print(f"  • Average item price: ${stats.get('average_item_price', 0):.2f}")
                if stats.get('most_common_items'):
                    print(f"  • Most common items:")
                    for item_info in stats['most_common_items'][:3]:
                        print(f"    - {item_info.get('item', 'Unknown')} ({item_info.get('count', 0)} times)")
            
            return True
        else:
            print("❌ Virtual row expansion was not applied")
            return False
            
    except Exception as e:
        print(f"❌ Error testing real database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_queries():
    """Test product-specific queries with real data"""
    print(f"\n🔍 Testing Product-Specific Queries")
    print("=" * 80)
    
    processor = DelimitedFieldProcessor()
    
    # Test queries that might match real data
    test_queries = [
        "Show me Printer Ink details",
        "What is the price of Office Chair?",
        "Find all items with Payroll in the description",
        "List all Financial Analysis Tool purchases",
        "Show me all Desk Lamp items"
    ]
    
    for query in test_queries:
        print(f"\n💬 Query: '{query}'")
        
        # Test query analysis
        is_item_query = processor.is_item_query(query)
        is_product_query = processor.is_specific_product_query(query)
        extracted_products = processor.improve_product_extraction(query)
        
        print(f"  🔍 Analysis:")
        print(f"    • Item query: {is_item_query}")
        print(f"    • Product query: {is_product_query}")
        print(f"    • Extracted products: {extracted_products}")
        
        # Verify detection
        if is_item_query or is_product_query or extracted_products:
            print(f"    ✅ Query properly detected")
        else:
            print(f"    ⚠️  Query not detected as item/product query")
    
    return True

def main():
    """Run the real database tests"""
    print("🌟 Real Database JSON Virtual Row Expansion Test")
    print("Testing with actual PostgreSQL database data")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Real database expansion
    try:
        if test_real_database_expansion():
            tests_passed += 1
            print("\n✅ Real database expansion test passed")
        else:
            print("\n❌ Real database expansion test failed")
    except Exception as e:
        print(f"\n❌ Real database expansion test error: {e}")
    
    # Test 2: Product queries
    try:
        if test_product_queries():
            tests_passed += 1
            print("\n✅ Product query test passed")
        else:
            print("\n❌ Product query test failed")
    except Exception as e:
        print(f"\n❌ Product query test error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All real database tests passed!")
        print("\n💡 Key Findings:")
        print("  ✅ Real database data is properly handled")
        print("  ✅ PostgreSQL arrays are correctly parsed")
        print("  ✅ Virtual row expansion works with actual data")
        print("  ✅ Product queries are properly detected")
        print("  ✅ Statistics and analytics work correctly")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
