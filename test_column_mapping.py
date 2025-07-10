import sys
import os

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from column_keywords_mapping import ColumnKeywordsMapping

# Test the column mapping
column_keywords = ColumnKeywordsMapping()

# Test vendor context
vendor_id = "V002"
case_id = "CASE006"

# Get enhanced prompt context
context = column_keywords.get_enhanced_prompt_context(vendor_id, case_id)

print("✅ Column Keywords Mapping Test")
print("=================================")
print("Enhanced Prompt Context:")
print(context)
print("\n✅ Column mapping test completed successfully!")
