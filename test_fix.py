#!/usr/bin/env python3
"""
Quick test to verify the fix for the limit_data_for_llm method
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'streamlit', 'src'))

from app import ContextAwareChat

def test_limit_data_method():
    """Test that the limit_data_for_llm method exists and works"""
    print("🔍 Testing limit_data_for_llm method...")
    
    # Create instance
    chat = ContextAwareChat()
    
    # Check if method exists
    if hasattr(chat, 'limit_data_for_llm'):
        print("✅ Method exists on ContextAwareChat class")
        
        # Test the method
        test_result = {
            'success': True,
            'data': [['row1'], ['row2'], ['row3'], ['row4'], ['row5']],
            'columns': ['col1']
        }
        
        # Test with small data (should not be truncated)
        limited_small = chat.limit_data_for_llm(test_result, max_rows=10)
        print(f"Small data test: {len(limited_small['data'])} rows, truncated: {limited_small.get('truncated', False)}")
        
        # Test with large data (should be truncated)
        limited_large = chat.limit_data_for_llm(test_result, max_rows=3)
        print(f"Large data test: {len(limited_large['data'])} rows, truncated: {limited_large.get('truncated', False)}")
        
        print("✅ Method working correctly")
        return True
    else:
        print("❌ Method does not exist on ContextAwareChat class")
        return False

if __name__ == "__main__":
    success = test_limit_data_method()
    if success:
        print("\n🎉 All tests passed! The fix is working.")
    else:
        print("\n❌ Tests failed. Need to investigate further.")
