import sys
import os

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from utils.delimited_field_processor import DelimitedFieldProcessor

# Test the auto-expansion logic
processor = DelimitedFieldProcessor()

# Test case: Single item should NOT trigger auto-expansion (based on current logic)
single_item_result = {
    'success': True,
    'data': [
        ['CASE003', 'V002', ['Cloud Storage'], [99.99], [1]]
    ],
    'columns': ['case_id', 'vendor_id', 'items_description', 'items_unit_price', 'items_quantity']
}

# Test case: Multiple items should trigger auto-expansion
multi_item_result = {
    'success': True,
    'data': [
        ['CASE001', 'V002', ['Printer Ink', 'Payroll Service'], [1431.4, 708.12], [1, 5]]
    ],
    'columns': ['case_id', 'vendor_id', 'items_description', 'items_unit_price', 'items_quantity']
}

print("✅ Testing Auto-Expansion Logic")
print("===============================")

# Test 1: Single item
print("\n🔍 Test 1: Single item per invoice")
expanded1 = processor.expand_results_with_items(single_item_result)
print(f"Expanded: {expanded1.get('items_expanded', False)}")
print(f"Row count: {len(single_item_result['data'])} → {expanded1.get('expanded_row_count', 0)}")

# Test 2: Multiple items
print("\n🔍 Test 2: Multiple items per invoice")
expanded2 = processor.expand_results_with_items(multi_item_result)
print(f"Expanded: {expanded2.get('items_expanded', False)}")
print(f"Row count: {len(multi_item_result['data'])} → {expanded2.get('expanded_row_count', 0)}")

print("\n💡 Current Logic: Items are always expanded if item columns are present")
print("   The issue might be in the auto-detection logic in display_results()")

print("\n✅ Test completed!")
