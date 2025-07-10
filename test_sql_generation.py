import sys
import os

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from utils.delimited_field_processor import DelimitedFieldProcessor

# Test the delimited field processor
processor = DelimitedFieldProcessor()

# Test product-specific SQL generation
vendor_id = "V002"
products = ["cloud storage", "hosting"]
user_question = "Show me all cloud storage and hosting services"

sql_query = processor.generate_product_specific_sql(user_question, vendor_id, products)

print("✅ Delimited Field Processor Test")
print("=================================")
print(f"User Question: {user_question}")
print(f"Vendor ID: {vendor_id}")
print(f"Products: {products}")
print(f"Generated SQL:")
print(sql_query)
print("\n✅ SQL generation test completed successfully!")
