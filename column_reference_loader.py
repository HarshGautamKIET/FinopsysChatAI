"""
FinOpsysAI Database Column Context Loader
Utility module for loading and managing database column reference information
"""

import os
from typing import Dict, List, Optional
from column_keywords_mapping import column_keywords

class ColumnReferenceLoader:
    """Loads and manages database column reference context for LLM queries"""
    
    def __init__(self, reference_file_path: Optional[str] = None):
        """Initialize with optional custom reference file path"""
        if reference_file_path is None:
            # Use the enhanced column keywords mapping
            self.keywords_mapping = column_keywords
            # Default to DATABASE_COLUMN_REFERENCE.md in the same directory as this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            reference_file_path = os.path.join(current_dir, 'DATABASE_COLUMN_REFERENCE.md')
        
        self.reference_file_path = reference_file_path
        self.column_mappings = self._load_column_mappings()
    
    def _load_column_mappings(self) -> Dict[str, Dict]:
        """Load column mappings from the reference file"""
        # This is a simplified mapping - in production, you could parse the full MD file
        return {
            'identifiers': {
                'columns': ['CASE_ID', 'BILL_ID', 'CUSTOMER_ID', 'VENDOR_ID', 'INVOICE_ID'],
                'keywords': {
                    'CASE_ID': ['case', 'case number', 'case detail', 'case reference'],
                    'BILL_ID': ['bill', 'bill id', 'bill reference', 'bill number'],
                    'CUSTOMER_ID': ['customer', 'client', 'customer id', 'client number'],
                    'VENDOR_ID': ['vendor', 'supplier', 'vendor id', 'supplier id'],
                    'INVOICE_ID': ['invoice', 'invoice id', 'invoice number']
                }
            },
            'dates': {
                'columns': ['DUE_DATE', 'BILL_DATE', 'DECLINE_DATE', 'RECEIVING_DATE', 'APPROVEDDATE1', 'APPROVEDDATE2', 'INVOICE_DATE'],
                'keywords': {
                    'DUE_DATE': ['due date', 'payment deadline', 'when to pay'],
                    'BILL_DATE': ['bill date', 'billing date', 'when billed'],
                    'INVOICE_DATE': ['invoice date', 'date created', 'issued on']
                }
            },
            'financial': {
                'columns': ['AMOUNT', 'BALANCE_AMOUNT', 'PAID', 'TOTAL_TAX', 'SUBTOTAL'],
                'keywords': {
                    'AMOUNT': ['total amount', 'bill total', 'invoice value', 'grand total'],
                    'BALANCE_AMOUNT': ['balance', 'unpaid amount', 'outstanding amount'],
                    'PAID': ['amount paid', 'payment received', 'paid amount'],
                    'TOTAL_TAX': ['total tax', 'tax amount', 'VAT total', 'GST total'],
                    'SUBTOTAL': ['subtotal', 'amount before tax', 'pre-tax amount']
                }
            },
            'content': {
                'columns': ['ITEMS_DESCRIPTION', 'ITEMS_UNIT_PRICE', 'ITEMS_QUANTITY'],
                'keywords': {
                    'ITEMS_DESCRIPTION': ['item description', 'billed items', 'services listed'],
                    'ITEMS_UNIT_PRICE': ['unit price', 'price per item', 'rate', 'cost per piece'],
                    'ITEMS_QUANTITY': ['quantity', 'item count', 'units billed', 'how many items']
                }
            },
            'status': {
                'columns': ['STATUS', 'DECLINE_REASON'],
                'keywords': {
                    'STATUS': ['invoice status', 'current state', 'approval status', 'is paid'],
                    'DECLINE_REASON': ['reason for rejection', 'decline comment', 'why declined']
                }
            },
            'organization': {
                'columns': ['DEPARTMENT'],
                'keywords': {                    'DEPARTMENT': ['department name', 'approving team', 'billing department', 'finance department']
                }
            }
        }
    
    def get_enhanced_prompt_context(self, vendor_id: str, case_id: Optional[str] = None) -> str:
        """Generate enhanced prompt context with column reference information"""
        
        # Use the enhanced keywords mapping if available
        if hasattr(self, 'keywords_mapping'):
            return self.keywords_mapping.get_enhanced_prompt_context(vendor_id, case_id)
        
        # Fallback to original implementation
        context = f"""
DATABASE CONTEXT:
- Database: FINOPSYS_DB
- Schema: PUBLIC  
- Table: AI_INVOICE

COLUMN MAPPING GUIDE:
Core Identifiers: {', '.join(self.column_mappings['identifiers']['columns'])}
Dates: {', '.join(self.column_mappings['dates']['columns'])}
Financial: {', '.join(self.column_mappings['financial']['columns'])}
Content: {', '.join(self.column_mappings['content']['columns'])}
Status: {', '.join(self.column_mappings['status']['columns'])}
Organization: {', '.join(self.column_mappings['organization']['columns'])}

KEYWORD MAPPING EXAMPLES:
- "total amount/bill total/invoice value" → AMOUNT
- "unpaid/balance/outstanding" → BALANCE_AMOUNT
- "paid amount/payment received" → PAID
- "due date/payment deadline" → DUE_DATE
- "invoice status/current state" → STATUS
- "customer/client" → CUSTOMER_ID
- "vendor/supplier" → VENDOR_ID
- "case/case number" → CASE_ID

CRITICAL SECURITY REQUIREMENTS:
1. MANDATORY: ALWAYS include WHERE vendor_id = '{vendor_id}' in EVERY query
2. ONLY query the AI_INVOICE table
3. Generate ONLY the SQL query, no explanations
4. Use Snowflake SQL syntax
5. Map user keywords to correct column names using the guide above

Current vendor context: vendor_id = {vendor_id}"""
        
        if case_id:
            context += f"\nCurrent case context: case_id = {case_id}"
        
        return context
    
    def get_example_queries(self, vendor_id: str) -> List[str]:
        """Get example SQL queries with proper vendor filtering"""
        return [
            f"SELECT COUNT(*) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'",
            f"SELECT SUM(AMOUNT) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'",
            f"SELECT * FROM AI_INVOICE WHERE BALANCE_AMOUNT > 0 AND vendor_id = '{vendor_id}'",
            f"SELECT * FROM AI_INVOICE WHERE STATUS = 'Pending' AND vendor_id = '{vendor_id}'",
            f"SELECT SUM(TOTAL_TAX) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'"
        ]
    
    def find_column_for_keyword(self, keyword: str) -> Optional[str]:
        """Find the correct column name for a given keyword"""
        keyword_lower = keyword.lower()
        
        for category in self.column_mappings.values():
            for column, keywords in category.get('keywords', {}).items():
                if keyword_lower in [k.lower() for k in keywords]:
                    return column
        
        return None
    
    def get_all_columns(self) -> List[str]:
        """Get all available column names"""
        all_columns = []
        for category in self.column_mappings.values():
            all_columns.extend(category['columns'])
        return all_columns
    
    def validate_query_security(self, sql_query: str, vendor_id: str) -> tuple[bool, str]:
        """Validate that the query meets security requirements"""
        sql_lower = sql_query.lower()
        
        # Check for vendor_id filtering
        if f"vendor_id = '{vendor_id}'" not in sql_query and f'vendor_id = "{vendor_id}"' not in sql_query:
            return False, "Query must include vendor_id filtering for security compliance"
        
        # Check for AI_INVOICE table only
        if 'from ai_invoice' not in sql_lower:
            return False, "Query must only access the AI_INVOICE table"
        
        # Check for potential dangerous operations
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False, f"Operation '{keyword}' is not permitted"
        
        return True, "Query passes security validation"

# Global instance for easy import
column_reference = ColumnReferenceLoader()
