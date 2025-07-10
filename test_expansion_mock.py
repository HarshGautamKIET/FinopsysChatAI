#!/usr/bin/env python3
"""
Simple test to understand the expansion logic with mock data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.delimited_field_processor import DelimitedFieldProcessor

def test_expansion_with_mock_data():
    """Test expansion with mock data to understand the logic"""
    print("🔍 Testing Invoice Item Expansion with Mock Data")
    print("=" * 50)
    
    processor = DelimitedFieldProcessor()
    
    # Test case 1: Single item invoice
    print("\n📋 Test Case 1: Single Item Invoice")
    single_item_result = {
        'success': True,
        'data': [
            ['INV001', 'Office Supplies', '25.50', '2']
        ],
        'columns': ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    }
    
    expanded_single = processor.expand_results_with_items(single_item_result)
    print(f"Original rows: {len(single_item_result['data'])}")
    print(f"Expanded rows: {len(expanded_single['data'])}")
    print(f"Items expanded: {expanded_single.get('items_expanded', False)}")
    
    if expanded_single.get('items_expanded'):
        print("✅ Single item expansion working!")
        print(f"Expanded data: {expanded_single['data']}")
    else:
        print("❌ Single item expansion failed")
    
    # Test case 2: Multiple items in one invoice
    print("\n📋 Test Case 2: Multiple Items in One Invoice")
    multi_item_result = {
        'success': True,
        'data': [
            ['INV002', 'Office Supplies, Printer Paper, Pens', '25.50, 15.00, 8.99', '2, 5, 10']
        ],
        'columns': ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    }
    
    expanded_multi = processor.expand_results_with_items(multi_item_result)
    print(f"Original rows: {len(multi_item_result['data'])}")
    print(f"Expanded rows: {len(expanded_multi['data'])}")
    print(f"Items expanded: {expanded_multi.get('items_expanded', False)}")
    
    if expanded_multi.get('items_expanded'):
        print("✅ Multi-item expansion working!")
        print("Expanded data:")
        for i, row in enumerate(expanded_multi['data']):
            print(f"  Row {i+1}: {dict(zip(expanded_multi['columns'], row))}")
    else:
        print("❌ Multi-item expansion failed")
    
    # Test case 3: JSON array format
    print("\n📋 Test Case 3: JSON Array Format")
    json_result = {
        'success': True,
        'data': [
            ['INV003', '["Cloud Storage", "Email Service", "Security License"]', '[29.99, 15.00, 45.00]', '[1, 3, 2]']
        ],
        'columns': ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    }
    
    expanded_json = processor.expand_results_with_items(json_result)
    print(f"Original rows: {len(json_result['data'])}")
    print(f"Expanded rows: {len(expanded_json['data'])}")
    print(f"Items expanded: {expanded_json.get('items_expanded', False)}")
    
    if expanded_json.get('items_expanded'):
        print("✅ JSON array expansion working!")
        print("Expanded data:")
        for i, row in enumerate(expanded_json['data']):
            print(f"  Row {i+1}: {dict(zip(expanded_json['columns'], row))}")
    else:
        print("❌ JSON array expansion failed")
    
    # Test case 4: Empty/null items
    print("\n📋 Test Case 4: Empty/Null Items")
    empty_result = {
        'success': True,
        'data': [
            ['INV004', '', '', ''],
            ['INV005', None, None, None]
        ],
        'columns': ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    }
    
    expanded_empty = processor.expand_results_with_items(empty_result)
    print(f"Original rows: {len(empty_result['data'])}")
    print(f"Expanded rows: {len(expanded_empty['data'])}")
    print(f"Items expanded: {expanded_empty.get('items_expanded', False)}")
    
    if expanded_empty.get('items_expanded'):
        print("✅ Empty items handling working!")
        print("Expanded data:")
        for i, row in enumerate(expanded_empty['data']):
            print(f"  Row {i+1}: {dict(zip(expanded_empty['columns'], row))}")
    else:
        print("❌ Empty items handling failed")
    
    # Test case 5: Mixed data
    print("\n📋 Test Case 5: Mixed Data (Some with items, some without)")
    mixed_result = {
        'success': True,
        'data': [
            ['INV006', 'Office Supplies, Printer Paper', '25.50, 15.00', '2, 5'],
            ['INV007', '', '', ''],
            ['INV008', 'Single Item', '100.00', '1']
        ],
        'columns': ['case_id', 'items_description', 'items_unit_price', 'items_quantity']
    }
    
    expanded_mixed = processor.expand_results_with_items(mixed_result)
    print(f"Original rows: {len(mixed_result['data'])}")
    print(f"Expanded rows: {len(expanded_mixed['data'])}")
    print(f"Items expanded: {expanded_mixed.get('items_expanded', False)}")
    
    if expanded_mixed.get('items_expanded'):
        print("✅ Mixed data expansion working!")
        print("Expanded data:")
        for i, row in enumerate(expanded_mixed['data']):
            print(f"  Row {i+1}: {dict(zip(expanded_mixed['columns'], row))}")
    else:
        print("❌ Mixed data expansion failed")
    
    print("\n🎯 Summary:")
    print(f"Test results:")
    print(f"  Single item: {'✅' if expanded_single.get('items_expanded') else '❌'}")
    print(f"  Multi-item: {'✅' if expanded_multi.get('items_expanded') else '❌'}")
    print(f"  JSON array: {'✅' if expanded_json.get('items_expanded') else '❌'}")
    print(f"  Empty items: {'✅' if expanded_empty.get('items_expanded') else '❌'}")
    print(f"  Mixed data: {'✅' if expanded_mixed.get('items_expanded') else '❌'}")

if __name__ == "__main__":
    test_expansion_with_mock_data()
