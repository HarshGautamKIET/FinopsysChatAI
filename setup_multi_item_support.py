#!/usr/bin/env python3
"""
Quick Setup Script for Multi-Item Support
This script sets up the necessary database structures for handling multiple items per invoice
"""

import os
import sys
import logging
from normalize_multi_item_data import MultiItemNormalizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("🚀 FinOpsysAI Multi-Item Support Setup")
    print("=" * 50)
    print()
    print("This script will set up your database to handle multiple items per invoice.")
    print("Each product item will be separated into individual rows for better querying.")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Setup cancelled.")
        return 0
    
    print()
    print("🔄 Starting setup process...")
    
    try:
        # Create and run the normalizer
        normalizer = MultiItemNormalizer()
        success = normalizer.run_normalization()
        
        if success:
            print()
            print("✅ Multi-item support setup completed successfully!")
            print()
            print("📋 What was created:")
            print("• ai_invoice_line_items table - stores individual line items")
            print("• ai_invoice_expanded view - shows all line items in a flat view")
            print("• ai_invoice_summary view - shows aggregated invoice data")
            print("• Automatic triggers - keep line items synchronized with invoices")
            print()
            print("🎯 Benefits:")
            print("• Better support for item-level queries")
            print("• Accurate responses to product-specific questions")
            print("• Improved analytics and reporting capabilities")
            print("• Automatic processing of future multi-item invoices")
            print()
            print("⚡ Your application will now automatically use this enhanced structure!")
            
        else:
            print()
            print("❌ Setup failed. Please check the error messages above.")
            print("💡 Common issues:")
            print("• Database connection problems")
            print("• Insufficient database permissions")
            print("• Missing environment variables")
            return 1
    
    except Exception as e:
        print(f"❌ Setup failed with error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
