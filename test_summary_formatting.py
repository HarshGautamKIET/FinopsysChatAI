#!/usr/bin/env python3
"""
Test script to verify query summary formatting improvements
"""

import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sys
sys.path.append(r'd:\Finopsys\FinopsysChatAI\streamlit\src')
from app import ContextAwareChat, LLMManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_summary_formatting():
    """Test the updated summary formatting"""
    
    print("🧪 Testing Query Summary Formatting...")
    
    # Initialize LLM manager and chat
    llm_manager = LLMManager()
    chat = ContextAwareChat(llm_manager, None)
    
    # Test data simulating a query result
    test_processed_result = {
        'success': True,
        'data': [
            ['INV001', 'Vendor1', 1000.00, 500.00, 500.00, 'Cloud Storage', '2024-01-15'],
            ['INV002', 'Vendor1', 750.00, 0.00, 750.00, 'Support Services', '2024-01-20'],
            ['INV003', 'Vendor1', 1200.00, 1200.00, 0.00, 'Software License', '2024-01-25']
        ],
        'columns': ['invoice_id', 'vendor_id', 'amount', 'balance_amount', 'paid', 'description', 'bill_date'],
        'items_expanded': False,
        'original_row_count': 3
    }
    
    # Test LLM response (simulated)
    test_llm_response = """Based on the query results, your total spending across all invoices is $2,950.00. The data shows that you have 3 invoices. Looking at the payment status, one invoice remains unpaid with a balance of $1,200.00. The average invoice amount is $983.33."""
    
    # Test the format_enhanced_response method
    print("\n📝 Testing format_enhanced_response method...")
    
    formatted_response = chat.format_enhanced_response(
        raw_response=test_llm_response,
        processed_result=test_processed_result,
        user_question="What's my total spending?",
        is_specific_product_query=False,
        extracted_products=[],
        llm_result={'truncated': False}
    )
    
    print("\n" + "="*60)
    print("FORMATTED RESPONSE:")
    print("="*60)
    print(formatted_response)
    print("="*60)
    
    # Test the _clean_llm_response method separately
    print("\n🧹 Testing _clean_llm_response method...")
    
    clean_response = chat._clean_llm_response(test_llm_response)
    
    print("\n" + "-"*40)
    print("CLEAN RESPONSE:")
    print("-"*40)
    print(clean_response)
    print("-"*40)
    
    # Test query summary
    print("\n📊 Testing _create_query_summary method...")
    
    query_summary = chat._create_query_summary("What's my total spending?", test_processed_result)
    
    print("\n" + "-"*30)
    print("QUERY SUMMARY:")
    print("-"*30)
    print(query_summary)
    print("-"*30)
    
    # Verify no "Next Steps" are included
    if "Next Steps" in formatted_response:
        print("\n❌ ERROR: 'Next Steps' found in formatted response!")
        return False
    else:
        print("\n✅ SUCCESS: No 'Next Steps' found in formatted response")
    
    # Verify proper line breaks
    line_count = len(formatted_response.split('\n'))
    if line_count > 1:
        print(f"✅ SUCCESS: Response has {line_count} lines (proper formatting)")
    else:
        print("❌ ERROR: Response appears to be a single line")
        return False
    
    # Verify conciseness (no excessive verbosity)
    if len(formatted_response) < len(test_llm_response) * 3:  # Not more than 3x original
        print(f"✅ SUCCESS: Response is concise ({len(formatted_response)} chars)")
    else:
        print(f"⚠️  WARNING: Response might be too verbose ({len(formatted_response)} chars)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_summary_formatting()
        if success:
            print("\n🎉 All formatting tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some formatting tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
