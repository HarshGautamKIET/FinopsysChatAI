import sys
import os

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from utils.delimited_field_processor import DelimitedFieldProcessor

# Test the item expansion functionality
processor = DelimitedFieldProcessor()

# Simulate database result with Python lists (as returned by PostgreSQL)
test_result = {
    'success': True,
    'data': [
        ['CASE001', 'V002', ['Printer Ink', 'Payroll Service'], [1431.4, 708.12], [1, 5]],
        ['CASE002', 'V002', ['Cloud Storage'], [99.99], [1]]
    ],
    'columns': ['case_id', 'vendor_id', 'items_description', 'items_unit_price', 'items_quantity']
}

print("✅ Testing Item Expansion")
print("==========================")
print("Original data:")
for i, row in enumerate(test_result['data']):
    print(f"  Row {i+1}: {row}")

print(f"\nOriginal columns: {test_result['columns']}")
print(f"Original row count: {len(test_result['data'])}")

# Test expansion
expanded_result = processor.expand_results_with_items(test_result)

print(f"\n🔍 Expansion Results:")
print(f"Items expanded: {expanded_result.get('items_expanded', False)}")
print(f"Original row count: {expanded_result.get('original_row_count', 0)}")
print(f"Expanded row count: {expanded_result.get('expanded_row_count', 0)}")
print(f"New columns: {expanded_result.get('columns', [])}")

if expanded_result.get('items_expanded'):
    print(f"\nExpanded data (first 5 rows):")
    for i, row in enumerate(expanded_result['data'][:5]):
        print(f"  Row {i+1}: {row}")
else:
    print("❌ Expansion failed!")

print("\n✅ Test completed!")
