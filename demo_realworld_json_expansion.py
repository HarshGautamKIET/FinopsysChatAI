#!/usr/bin/env python3
"""
Real-World JSON Virtual Row Expansion Demo for FinOpsys ChatAI
Demonstrates how users can query individual items from JSON array data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.delimited_field_processor import DelimitedFieldProcessor
import json

def simulate_database_query(sql_query: str, vendor_id: str = 'V001'):
    """Simulate a database query that returns JSON array data"""
    
    # Mock database with realistic invoice data containing JSON arrays
    mock_database = [
        {
            'CASE_ID': 'INV001',
            'VENDOR_ID': 'V001',
            'VENDOR_NAME': 'TechCorp Solutions',
            'BILL_DATE': '2023-12-01',
            'TOTAL_AMOUNT': 2850.00,
            'ITEMS_DESCRIPTION': '["Office Chair", "Standing Desk", "Monitor"]',
            'ITEMS_UNIT_PRICE': '["250.00", "800.00", "300.00"]',
            'ITEMS_QUANTITY': '["4", "2", "3"]'
        },
        {
            'CASE_ID': 'INV002',
            'VENDOR_ID': 'V001',
            'VENDOR_NAME': 'Business Services Inc',
            'BILL_DATE': '2023-12-05',
            'TOTAL_AMOUNT': 3500.00,
            'ITEMS_DESCRIPTION': '["Audit Report", "Consulting Services", "Training Materials"]',
            'ITEMS_UNIT_PRICE': '["1500.00", "1800.00", "200.00"]',
            'ITEMS_QUANTITY': '["1", "1", "1"]'
        },
        {
            'CASE_ID': 'INV003',
            'VENDOR_ID': 'V001',
            'VENDOR_NAME': 'Software Solutions Ltd',
            'BILL_DATE': '2023-12-10',
            'TOTAL_AMOUNT': 1950.00,
            'ITEMS_DESCRIPTION': '["Software License", "Cloud Storage", "Technical Support"]',
            'ITEMS_UNIT_PRICE': '["1200.00", "500.00", "250.00"]',
            'ITEMS_QUANTITY': '["1", "2", "1"]'
        }
    ]
    
    # Filter by vendor_id if specified in query
    if f"vendor_id = '{vendor_id}'" in sql_query.lower():
        filtered_data = [row for row in mock_database if row['VENDOR_ID'] == vendor_id]
    else:
        filtered_data = mock_database
    
    # Convert to query result format
    columns = list(filtered_data[0].keys()) if filtered_data else []
    data = [[row[col] for col in columns] for row in filtered_data]
    
    return {
        'success': True,
        'data': data,
        'columns': columns
    }

def demo_user_query(user_question: str, processor: DelimitedFieldProcessor):
    """Demonstrate how a user query would be processed with virtual row expansion"""
    
    print(f"\n💬 User asks: \"{user_question}\"")
    print("-" * 80)
    
    # Analyze the query
    is_item_query = processor.is_item_query(user_question)
    is_product_query = processor.is_specific_product_query(user_question)
    extracted_products = processor.improve_product_extraction(user_question)
    
    print(f"🔍 Query Analysis:")
    print(f"   • Item-level query: {is_item_query}")
    print(f"   • Product-specific query: {is_product_query}")
    print(f"   • Extracted products: {extracted_products}")
    
    # Simulate SQL generation and execution
    base_sql = "SELECT * FROM AI_INVOICE WHERE vendor_id = 'V001'"
    if extracted_products:
        # Add product filtering for specific products
        product_conditions = " OR ".join([
            f"ITEMS_DESCRIPTION LIKE '%{product}%'" for product in extracted_products
        ])
        base_sql += f" AND ({product_conditions})"
    
    print(f"\n📝 Generated SQL:")
    print(f"   {base_sql}")
    
    # Execute mock query
    results = simulate_database_query(base_sql)
    
    print(f"\n📊 Raw Query Results: {len(results['data'])} invoices found")
    for i, row in enumerate(results['data']):
        case_id = row[0]
        items_desc = row[5]  # ITEMS_DESCRIPTION
        print(f"   Invoice {case_id}: {items_desc}")
    
    # Apply virtual row expansion
    if is_item_query or is_product_query:
        print(f"\n🔄 Applying virtual row expansion...")
        expanded_results = processor.expand_results_with_items(results)
        
        if expanded_results.get('items_expanded'):
            print(f"✨ Expanded to {expanded_results['total_line_items']} individual line items:")
            
            columns = expanded_results['columns']
            data = expanded_results['data']
            
            # Find relevant column indices
            case_id_idx = columns.index('CASE_ID')
            item_desc_idx = columns.index('ITEM_DESCRIPTION')
            item_price_idx = columns.index('ITEM_UNIT_PRICE')
            item_qty_idx = columns.index('ITEM_QUANTITY')
            item_total_idx = columns.index('ITEM_LINE_TOTAL')
            
            for i, row in enumerate(data):
                case_id = row[case_id_idx]
                item_desc = row[item_desc_idx]
                item_price = row[item_price_idx]
                item_qty = row[item_qty_idx]
                item_total = row[item_total_idx]
                
                # Filter results based on extracted products if any
                if extracted_products:
                    if not any(product.lower() in item_desc.lower() for product in extracted_products):
                        continue
                
                print(f"   🔸 {case_id}: {item_desc} - ${item_price} × {item_qty} = ${item_total}")
            
            # Generate statistics
            stats = processor.get_item_statistics(results)
            if stats:
                print(f"\n📈 Item Statistics:")
                print(f"   • Total line items: {stats['total_line_items']}")
                print(f"   • Total value: ${stats['total_item_value']:,.2f}")
                print(f"   • Average item price: ${stats['average_item_price']:.2f}")
                if stats['most_common_items']:
                    print(f"   • Most common items:")
                    for item_info in stats['most_common_items'][:3]:
                        print(f"     - {item_info['item']} ({item_info['count']} times)")
        else:
            print("   No expansion performed - displaying invoice-level results")
    else:
        print("   📄 Displaying invoice-level results (no item expansion needed)")
    
    return results

def main():
    """Run the real-world demonstration"""
    print("🌟 Real-World JSON Virtual Row Expansion Demo")
    print("=" * 80)
    print("This demo shows how users can query individual items from invoices")
    print("where item data is stored as JSON arrays in database fields.")
    print()
    
    processor = DelimitedFieldProcessor()
    
    # Test various real-world user queries
    user_queries = [
        "Show me Office Chair details",
        "What is the price of Audit Report?",
        "List all items with Software in the description",
        "Find all purchases of Standing Desk",
        "How much did we spend on Cloud Storage?",
        "Show me all invoices with Monitor",
        "What items cost more than $500?",
        "List all Training Materials purchases",
        "Show me all line items for December 2023",
        "Find all items with quantity greater than 1"
    ]
    
    for query in user_queries:
        try:
            demo_user_query(query, processor)
            print("\n" + "=" * 80)
        except Exception as e:
            print(f"❌ Error processing query '{query}': {e}")
            import traceback
            traceback.print_exc()
            print("\n" + "=" * 80)
    
    print("\n🎯 Key Benefits of Virtual Row Expansion:")
    print("   ✅ Users can ask about specific products/items independently")
    print("   ✅ Each item becomes a queryable 'virtual row' with its own data")
    print("   ✅ Supports both JSON arrays and CSV/delimited formats")
    print("   ✅ Automatic product detection and query classification")
    print("   ✅ Rich statistics and analytics on item-level data")
    print("   ✅ Seamless integration with existing invoice data structure")
    
    print("\n💡 Users can now ask natural questions like:")
    print("   • 'How many Office Chairs did we buy this month?'")
    print("   • 'What's the average price of Software Licenses?'")
    print("   • 'Show me all Training Materials purchases'")
    print("   • 'Find items with quantity greater than 5'")
    print("   • 'What was the total spent on Cloud Storage?'")

if __name__ == "__main__":
    main()
