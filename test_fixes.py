#!/usr/bin/env python3
"""
Test the fixes for redundant calls and SQL column issues
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.delimited_field_processor import DelimitedFieldProcessor
from utils.enhanced_db_manager import EnhancedDatabaseManager
import sys
sys.path.append('./streamlit/src')
from app import PostgreSQLManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_fixes():
    """Test the fixes for redundant calls and column issues"""
    print("🧪 Testing fixes...")
    
    # Test 1: Verify no redundant method calls
    print("\n1️⃣ Testing redundant call fixes...")
    processor = DelimitedFieldProcessor()
    
    # This should be called only once now
    test_query = "How many invoices do I have?"
    analysis = processor.enhance_llm_understanding_for_items(test_query)
    
    print(f"✅ Query analysis completed once: {analysis['query_intent']}")
    print(f"   Required columns: {analysis['required_columns']}")
    
    # Verify correct column names (should be BILL_DATE, not INVOICE_DATE)
    if 'INVOICE_DATE' in str(analysis):
        print("❌ Still contains INVOICE_DATE references")
    else:
        print("✅ No INVOICE_DATE references found")
    
    # Test 2: Test product query
    print("\n2️⃣ Testing product query...")
    test_query2 = "Does I ever purchased Laptop?"
    analysis2 = processor.enhance_llm_understanding_for_items(test_query2)
    
    print(f"✅ Product query analysis: {analysis2['query_intent']}")
    print(f"   Extracted products: {analysis2['extracted_products']}")
    print(f"   SQL hints: {analysis2['sql_hints']}")
    
    # Test 3: Test database connection handling
    print("\n3️⃣ Testing database operations...")
    try:
        db_manager = PostgreSQLManager()
        db_manager.initialize()
        
        # Test vendor setup
        if db_manager.setup_vendor_context("V002"):
            print("✅ Vendor context setup successful")
            
            # Test enhanced database manager
            enhanced_manager = EnhancedDatabaseManager(db_manager)
            
            # Test simple query without redundant calls
            test_sql = "SELECT CASE_ID, BILL_DATE, AMOUNT FROM AI_INVOICE WHERE vendor_id = 'V002' LIMIT 5"
            result = enhanced_manager.execute_item_aware_query_with_analysis(test_sql, test_query, analysis)
            
            if result.get('success'):
                print(f"✅ Query executed successfully: {len(result.get('data', []))} rows")
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        else:
            print("❌ Failed to setup vendor context")
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
    
    print("\n🎉 Fix testing completed!")

if __name__ == "__main__":
    test_fixes()
