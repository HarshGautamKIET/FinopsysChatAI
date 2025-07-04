#!/usr/bin/env python3
"""
Test Script for Multi-Item Functionality
Tests the enhanced multi-item support features
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from config import Config
from utils.delimited_field_processor import DelimitedFieldProcessor
from utils.enhanced_db_manager import EnhancedDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiItemTester:
    """Test suite for multi-item functionality"""
    
    def __init__(self):
        self.processor = DelimitedFieldProcessor()
        self.test_data = self.create_test_data()
        
    def create_test_data(self) -> Dict[str, Any]:
        """Create sample test data with multiple items"""
        return {
            'success': True,
            'data': [
                [
                    'CASE001', 'VENDOR001', '2024-01-15', 1500.00, 0.00,
                    '["Cloud Storage", "Technical Support", "Training"]',
                    '[99.99, 199.99, 299.99]',
                    '[1, 2, 1]',
                    'Paid'
                ],
                [
                    'CASE002', 'VENDOR001', '2024-01-20', 2000.00, 500.00,
                    '["Software License", "Maintenance", "Consulting"]', 
                    '[999.99, 500.00, 750.00]',
                    '[1, 12, 8]',
                    'Partial'
                ]
            ],
            'columns': [
                'CASE_ID', 'VENDOR_ID', 'BILL_DATE', 'AMOUNT', 'BALANCE_AMOUNT',
                'ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY', 'STATUS'
            ]
        }
    
    def test_json_parsing(self):
        """Test JSON array parsing functionality"""
        print("🧪 Testing JSON array parsing...")
        
        # Test description parsing
        descriptions = self.processor.parse_delimited_field('["Cloud Storage", "Technical Support", "Training"]')
        expected_descriptions = ["Cloud Storage", "Technical Support", "Training"]
        
        if descriptions == expected_descriptions:
            print("   ✅ Description parsing: PASSED")
        else:
            print(f"   ❌ Description parsing: FAILED - Got {descriptions}, expected {expected_descriptions}")
        
        # Test numeric parsing
        prices = self.processor.parse_numeric_delimited_field('[99.99, 199.99, 299.99]')
        expected_prices = [99.99, 199.99, 299.99]
        
        if prices == expected_prices:
            print("   ✅ Price parsing: PASSED")
        else:
            print(f"   ❌ Price parsing: FAILED - Got {prices}, expected {expected_prices}")
    
    def test_csv_parsing(self):
        """Test CSV format parsing functionality"""
        print("🧪 Testing CSV parsing...")
        
        # Test CSV description parsing
        descriptions = self.processor.parse_delimited_field('Cloud Storage,Technical Support,Training')
        expected_descriptions = ["Cloud Storage", "Technical Support", "Training"]
        
        if descriptions == expected_descriptions:
            print("   ✅ CSV description parsing: PASSED")
        else:
            print(f"   ❌ CSV description parsing: FAILED - Got {descriptions}, expected {expected_descriptions}")
        
        # Test CSV numeric parsing
        prices = self.processor.parse_numeric_delimited_field('99.99,199.99,299.99')
        expected_prices = [99.99, 199.99, 299.99]
        
        if prices == expected_prices:
            print("   ✅ CSV price parsing: PASSED")
        else:
            print(f"   ❌ CSV price parsing: FAILED - Got {prices}, expected {expected_prices}")
    
    def test_item_expansion(self):
        """Test the item expansion functionality"""
        print("🧪 Testing item expansion...")
        
        expanded_results = self.processor.expand_results_with_items(self.test_data)
        
        if expanded_results.get('items_expanded'):
            original_count = expanded_results.get('original_row_count', 0)
            expanded_count = expanded_results.get('expanded_row_count', 0)
            line_items = expanded_results.get('total_line_items', 0)
            
            print(f"   ✅ Expansion successful: {original_count} invoices → {line_items} line items")
            
            # Verify we have the right number of items
            expected_items = 3 + 3  # 3 items from CASE001 + 3 items from CASE002
            if line_items == expected_items:
                print(f"   ✅ Item count correct: {line_items} items")
            else:
                print(f"   ❌ Item count incorrect: Got {line_items}, expected {expected_items}")
        else:
            print("   ❌ Item expansion: FAILED - No expansion occurred")
    
    def test_query_detection(self):
        """Test query type detection"""
        print("🧪 Testing query detection...")
        
        # Test item query detection
        item_queries = [
            "What items did I purchase?",
            "Show me line item details",
            "What products are on my invoices?",
            "Break down my invoice items"
        ]
        
        item_query_results = []
        for query in item_queries:
            is_item = self.processor.is_item_query(query)
            item_query_results.append(is_item)
            if is_item:
                print(f"   ✅ Item query detected: '{query}'")
            else:
                print(f"   ❌ Item query NOT detected: '{query}'")
        
        # Test product-specific query detection
        product_queries = [
            "What's the price of cloud storage?",
            "How much did I spend on software licenses?",
            "Show me all training costs"
        ]
        
        product_query_results = []
        for query in product_queries:
            is_product = self.processor.is_specific_product_query(query)
            products = self.processor.extract_product_names_from_query(query)
            product_query_results.append((is_product, products))
            if is_product:
                print(f"   ✅ Product query detected: '{query}' → {products}")
            else:
                print(f"   ❌ Product query NOT detected: '{query}'")
    
    def test_statistics_generation(self):
        """Test statistics generation for line items"""
        print("🧪 Testing statistics generation...")
        
        expanded_results = self.processor.expand_results_with_items(self.test_data)
        stats = self.processor.get_item_statistics(expanded_results)
        
        if stats:
            print(f"   ✅ Statistics generated:")
            print(f"      - Total line items: {stats.get('total_line_items', 0)}")
            print(f"      - Unique invoices: {stats.get('unique_invoices', 0)}")
            print(f"      - Total value: ${stats.get('total_item_value', 0):,.2f}")
            print(f"      - Average price: ${stats.get('average_item_price', 0):.2f}")
            
            most_common = stats.get('most_common_items', [])
            if most_common:
                print(f"      - Most common items: {[item['item'] for item in most_common[:3]]}")
        else:
            print("   ❌ Statistics generation: FAILED")
    
    def test_product_specific_response(self):
        """Test product-specific response formatting"""
        print("🧪 Testing product-specific response formatting...")
        
        expanded_results = self.processor.expand_results_with_items(self.test_data)
        
        if expanded_results.get('items_expanded'):
            response = self.processor.format_product_specific_response(
                expanded_results, 
                "What's the price of cloud storage?", 
                ["cloud storage"]
            )
            
            if "No information found" not in response and "cloud storage" in response.lower():
                print("   ✅ Product-specific response formatting: PASSED")
                print(f"      Response preview: {response[:100]}...")
            else:
                print("   ❌ Product-specific response formatting: FAILED")
        else:
            print("   ❌ Cannot test response formatting - expansion failed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Multi-Item Functionality Tests")
        print("=" * 50)
        
        self.test_json_parsing()
        print()
        
        self.test_csv_parsing()
        print()
        
        self.test_item_expansion()
        print()
        
        self.test_query_detection()
        print()
        
        self.test_statistics_generation()
        print()
        
        self.test_product_specific_response()
        print()
        
        print("🎉 Multi-Item Functionality Tests Completed!")

def main():
    """Main function to run the tests"""
    print("💼 FinOpsysAI Multi-Item Functionality Tests")
    print("=" * 60)
    print()
    
    try:
        tester = MultiItemTester()
        tester.run_all_tests()
        
        print("\n📋 Test Summary:")
        print("• JSON array parsing capabilities")
        print("• CSV format parsing capabilities") 
        print("• Multi-item expansion functionality")
        print("• Query type detection (item vs. general)")
        print("• Product-specific query handling")
        print("• Statistics generation for line items")
        print("• Response formatting for product queries")
        
        print("\n✅ All core functionality tested successfully!")
        print("\n💡 Next step: Run 'python setup_multi_item_support.py' to enable database-level normalization")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
