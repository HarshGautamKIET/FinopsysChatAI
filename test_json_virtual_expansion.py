#!/usr/bin/env python3
"""
Test JSON Virtual Row Expansion for FinOpsys ChatAI
Tests the system's ability to expand JSON array data into virtual rows for item-level querying.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.delimited_field_processor import DelimitedFieldProcessor
import json

def test_json_array_parsing():
    """Test parsing of JSON arrays in the exact format from your example"""
    print("🧪 Testing JSON Array Parsing")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    # Test data in the exact format from your example
    test_descriptions = '["Office Chair", "Audit Report"]'
    test_prices = '["250.00", "1500.00"]'
    test_quantities = '["2", "1"]'
    
    print(f"Input ITEMS_DESCRIPTION: {test_descriptions}")
    print(f"Input ITEMS_UNIT_PRICE: {test_prices}")
    print(f"Input ITEMS_QUANTITY: {test_quantities}")
    print()
    
    # Parse each field
    descriptions = processor.parse_delimited_field(test_descriptions)
    prices = processor.parse_numeric_delimited_field(test_prices)
    quantities = processor.parse_numeric_delimited_field(test_quantities)
    
    print("Parsed Results:")
    print(f"  Descriptions: {descriptions}")
    print(f"  Prices: {prices}")
    print(f"  Quantities: {quantities}")
    print()
    
    # Verify parsing worked correctly
    assert descriptions == ["Office Chair", "Audit Report"], f"Expected ['Office Chair', 'Audit Report'], got {descriptions}"
    assert prices == [250.0, 1500.0], f"Expected [250.0, 1500.0], got {prices}"
    assert quantities == [2.0, 1.0], f"Expected [2.0, 1.0], got {quantities}"
    
    print("✅ JSON array parsing test passed!")
    return True

def test_virtual_row_expansion():
    """Test expansion of JSON array data into virtual rows"""
    print("\n🧪 Testing Virtual Row Expansion")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    # Mock database row with JSON arrays
    mock_row = {
        'CASE_ID': 'CASE203',
        'VENDOR_ID': 'V001',
        'BILL_DATE': '2023-12-15',
        'TOTAL_AMOUNT': 2000.00,
        'ITEMS_DESCRIPTION': '["Office Chair", "Audit Report"]',
        'ITEMS_UNIT_PRICE': '["250.00", "1500.00"]',
        'ITEMS_QUANTITY': '["2", "1"]'
    }
    
    print(f"Original row: {mock_row}")
    print()
    
    # Expand into virtual rows
    expanded_items = processor.process_item_row(mock_row)
    
    print(f"Expanded into {len(expanded_items)} virtual rows:")
    for i, item in enumerate(expanded_items, 1):
        print(f"\nVirtual Row {i}:")
        print(f"  CASE_ID: {item['CASE_ID']}")
        print(f"  ITEM_INDEX: {item['ITEM_INDEX']}")
        print(f"  ITEM_DESCRIPTION: {item['ITEM_DESCRIPTION']}")
        print(f"  ITEM_UNIT_PRICE: {item['ITEM_UNIT_PRICE']}")
        print(f"  ITEM_QUANTITY: {item['ITEM_QUANTITY']}")
        print(f"  ITEM_LINE_TOTAL: {item['ITEM_LINE_TOTAL']}")
    
    # Verify expansion
    assert len(expanded_items) == 2, f"Expected 2 items, got {len(expanded_items)}"
    
    # Check first item (Office Chair)
    item1 = expanded_items[0]
    assert item1['ITEM_DESCRIPTION'] == 'Office Chair'
    assert item1['ITEM_UNIT_PRICE'] == 250.0
    assert item1['ITEM_QUANTITY'] == 2.0
    assert item1['ITEM_LINE_TOTAL'] == 500.0  # 250 * 2
    
    # Check second item (Audit Report)
    item2 = expanded_items[1]
    assert item2['ITEM_DESCRIPTION'] == 'Audit Report'
    assert item2['ITEM_UNIT_PRICE'] == 1500.0
    assert item2['ITEM_QUANTITY'] == 1.0
    assert item2['ITEM_LINE_TOTAL'] == 1500.0  # 1500 * 1
    
    print("\n✅ Virtual row expansion test passed!")
    return True

def test_query_results_expansion():
    """Test expansion of full query results"""
    print("\n🧪 Testing Full Query Results Expansion")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    # Mock query results with multiple invoices
    mock_results = {
        'success': True,
        'data': [
            ['CASE203', 'V001', '2023-12-15', 2000.00, '["Office Chair", "Audit Report"]', '["250.00", "1500.00"]', '["2", "1"]'],
            ['CASE204', 'V002', '2023-12-16', 750.00, '["Laptop", "Software License"]', '["600.00", "150.00"]', '["1", "1"]']
        ],
        'columns': ['CASE_ID', 'VENDOR_ID', 'BILL_DATE', 'TOTAL_AMOUNT', 'ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY']
    }
    
    print(f"Original results: {len(mock_results['data'])} invoices")
    print("Data preview:")
    for row in mock_results['data']:
        print(f"  {row[0]}: {row[4]} = {row[5]} x {row[6]}")
    print()
    
    # Expand results
    expanded_results = processor.expand_results_with_items(mock_results)
    
    print(f"Expanded results: {len(expanded_results['data'])} line items")
    print(f"Total line items detected: {expanded_results.get('total_line_items', 0)}")
    print()
    
    print("Expanded data preview:")
    columns = expanded_results['columns']
    for i, row in enumerate(expanded_results['data']):
        row_dict = dict(zip(columns, row))
        print(f"  Row {i+1}: {row_dict.get('CASE_ID')} - {row_dict.get('ITEM_DESCRIPTION')} (${row_dict.get('ITEM_UNIT_PRICE')} x {row_dict.get('ITEM_QUANTITY')} = ${row_dict.get('ITEM_LINE_TOTAL')})")
    
    # Verify expansion
    assert expanded_results['success'] == True
    assert expanded_results['items_expanded'] == True
    assert len(expanded_results['data']) == 4  # 2 items from first invoice + 2 items from second invoice
    assert expanded_results['total_line_items'] == 4
    
    print("\n✅ Full query results expansion test passed!")
    return True

def test_product_specific_queries():
    """Test product-specific query detection and handling"""
    print("\n🧪 Testing Product-Specific Queries")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    test_queries = [
        "Show me Office Chair details",
        "What is the price of Audit Report?",
        "Find all items with quantity 2",
        "List all Office Chair purchases",
        "How much did we spend on Software License?",
        "Show me all invoices with Laptop"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Test query classification
        is_item_query = processor.is_item_query(query)
        is_product_query = processor.is_specific_product_query(query)
        extracted_products = processor.improve_product_extraction(query)
        
        print(f"  Is item query: {is_item_query}")
        print(f"  Is product query: {is_product_query}")
        print(f"  Extracted products: {extracted_products}")
        
        # Verify at least one detection method works
        assert is_item_query or is_product_query or extracted_products, f"Query '{query}' should be detected as item/product query"
    
    print("\n✅ Product-specific query detection test passed!")
    return True

def test_mixed_data_formats():
    """Test handling of mixed JSON and CSV data formats"""
    print("\n🧪 Testing Mixed Data Formats")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    # Test different data formats
    test_cases = [
        {
            'name': 'JSON Array Format',
            'data': '["Office Chair", "Audit Report"]'
        },
        {
            'name': 'CSV Format',
            'data': 'Office Chair, Audit Report'
        },
        {
            'name': 'Semicolon Delimited',
            'data': 'Office Chair; Audit Report'
        },
        {
            'name': 'PostgreSQL Array (Python List)',
            'data': ['Office Chair', 'Audit Report']  # This simulates PostgreSQL array type
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting {test_case['name']}: {test_case['data']}")
        
        parsed_items = processor.parse_delimited_field(test_case['data'])
        print(f"  Parsed: {parsed_items}")
        
        # All formats should produce the same result
        expected = ['Office Chair', 'Audit Report']
        assert parsed_items == expected, f"Expected {expected}, got {parsed_items} for {test_case['name']}"
    
    print("\n✅ Mixed data formats test passed!")
    return True

def run_all_tests():
    """Run all virtual row expansion tests"""
    print("🚀 Starting JSON Virtual Row Expansion Tests")
    print("=" * 60)
    
    tests = [
        test_json_array_parsing,
        test_virtual_row_expansion,
        test_query_results_expansion,
        test_product_specific_queries,
        test_mixed_data_formats
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! JSON virtual row expansion is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
