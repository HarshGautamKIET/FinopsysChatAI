"""
FinOpsysAI Database Column Context Loader
Utility module for loading and managing database column reference information
"""

import os
from typing import Dict, List, Optional
from column_keywords_mapping import column_keywords
from config import Config

config = Config()

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
                'columns': ['case_id', 'bill_id', 'customer_id', 'vendor_id'],
                'keywords': {
                    'case_id': ['case', 'case number', 'case detail', 'case reference'],
                    'bill_id': ['bill', 'bill id', 'bill reference', 'bill number'],
                    'customer_id': ['customer', 'client', 'customer id', 'client number'],
                    'vendor_id': ['vendor', 'supplier', 'vendor id', 'supplier id']
                }
            },
            'dates': {
                'columns': ['due_date', 'bill_date', 'decline_date', 'receiving_date', 'approveddate1', 'approveddate2'],
                'keywords': {
                    'due_date': ['due date', 'payment deadline', 'when to pay'],
                    'bill_date': ['bill date', 'billing date', 'when billed', 'invoice date', 'date created', 'issued on'],
                    'decline_date': ['decline date', 'rejected date', 'when declined'],
                    'receiving_date': ['receiving date', 'received date', 'when received'],
                    'approveddate1': ['first approval date', 'initial approval'],
                    'approveddate2': ['second approval date', 'final approval']
                }
            },
            'financial': {
                'columns': ['amount', 'balance_amount', 'paid', 'total_tax', 'subtotal'],
                'keywords': {
                    'amount': ['total amount', 'bill total', 'invoice value', 'grand total'],
                    'balance_amount': ['balance', 'unpaid amount', 'outstanding amount'],
                    'paid': ['amount paid', 'payment received', 'paid amount'],
                    'total_tax': ['total tax', 'tax amount', 'VAT total', 'GST total'],
                    'subtotal': ['subtotal', 'amount before tax', 'pre-tax amount']
                }
            },
            'content': {
                'columns': ['items_description', 'items_unit_price', 'items_quantity'],
                'keywords': {
                    'items_description': ['item description', 'billed items', 'services listed'],
                    'items_unit_price': ['unit price', 'price per item', 'rate', 'cost per piece'],
                    'items_quantity': ['quantity', 'item count', 'units billed', 'how many items']
                }
            },
            'status': {
                'columns': ['status', 'decline_reason'],
                'keywords': {
                    'status': ['invoice status', 'current state', 'approval status', 'is paid'],
                    'decline_reason': ['reason for rejection', 'decline comment', 'why declined']
                }
            },
            'organization': {
                'columns': ['department'],
                'keywords': {
                    'department': ['department name', 'approving team', 'billing department', 'finance department']
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
- Database: {config.POSTGRES_DATABASE}
- Schema: {config.POSTGRES_SCHEMA}
- Table: AI_INVOICE

COLUMN MAPPING GUIDE:
Core Identifiers: {', '.join(self.column_mappings['identifiers']['columns'])}
Dates: {', '.join(self.column_mappings['dates']['columns'])}
Financial: {', '.join(self.column_mappings['financial']['columns'])}
Content: {', '.join(self.column_mappings['content']['columns'])}
Status: {', '.join(self.column_mappings['status']['columns'])}
Organization: {', '.join(self.column_mappings['organization']['columns'])}

KEYWORD MAPPING EXAMPLES:
- "total amount/bill total/invoice value" → amount
- "unpaid/balance/outstanding" → balance_amount
- "paid amount/payment received" → paid
- "due date/payment deadline" → due_date
- "invoice status/current state" → status
- "customer/client" → customer_id
- "vendor/supplier" → vendor_id
- "case/case number" → case_id

CRITICAL SECURITY REQUIREMENTS:
1. MANDATORY: ALWAYS include WHERE vendor_id = '{vendor_id}' in EVERY query
2. ONLY query the AI_INVOICE table
3. Generate ONLY the SQL query, no explanations
4. Use PostgreSQL SQL syntax
5. Map user keywords to correct column names using the guide above

Current vendor context: vendor_id = {vendor_id}"""
        
        if case_id:
            context += f"\nCurrent case context: case_id = {case_id}"
        
        return context
    
    def get_example_queries(self, vendor_id: str) -> List[str]:
        """Get example SQL queries with proper vendor filtering"""
        return [
            f"SELECT COUNT(*) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'",
            f"SELECT SUM(amount) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'",
            f"SELECT * FROM AI_INVOICE WHERE balance_amount > 0 AND vendor_id = '{vendor_id}'",
            f"SELECT * FROM AI_INVOICE WHERE status = 'Pending' AND vendor_id = '{vendor_id}'",
            f"SELECT SUM(total_tax) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'"
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
