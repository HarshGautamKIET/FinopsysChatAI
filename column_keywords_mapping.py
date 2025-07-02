"""
Column Keywords Mapping for FinOpSysAI
Comprehensive mapping of database columns to user-friendly keywords and alternative terms
"""

from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)

class ColumnKeywordsMapping:
    """Comprehensive mapping of database columns to user keywords and alternative terms"""
    
    def __init__(self):
        """Initialize with comprehensive column keyword mappings"""
        
        # Complete mapping of database columns to user keywords
        self.column_mappings = {
            # 🔹 Core Identifiers
            'CASE_ID': {
                'keywords': [
                    'case', 'case number', 'get case', 'case detail', 'what is case',
                    'invoice case', 'case reference', 'bill case', 'case id', 'linked case'
                ],
                'category': 'identifiers',
                'description': 'Unique case identifier for invoice grouping'
            },
            
            'BILL_ID': {
                'keywords': [
                    'bill', 'bill id', 'get bill', 'bill reference', 'bill number',
                    'show bill', 'invoice bill', 'billing id', 'what is bill', 'bill detail'
                ],
                'category': 'identifiers',
                'description': 'Unique billing document identifier'
            },
            
            'CUSTOMER_ID': {
                'keywords': [
                    'customer', 'customer id', 'client', 'client number', 'customer reference',
                    'invoice customer', 'who is customer', 'customer info', 'bill to', 'client id'
                ],
                'category': 'identifiers',
                'description': 'Customer or client identifier'
            },
            
            'VENDOR_ID': {
                'keywords': [
                    'vendor', 'vendor id', 'supplier', 'supplier id', 'from whom',
                    'vendor reference', 'seller', 'vendor info', 'invoice from', 'supplier name'
                ],
                'category': 'identifiers',
                'description': 'Vendor or supplier identifier'
            },
            
            'INVOICE_ID': {
                'keywords': [
                    'invoice', 'invoice id', 'invoice number', 'billing id', 'invoice ref',
                    'bill number', 'show invoice', 'get invoice', 'what is invoice', 'invoice detail'
                ],
                'category': 'identifiers',
                'description': 'Unique invoice identifier'
            },
            
            # 🔹 Dates and Timeline
            'DUE_DATE': {
                'keywords': [
                    'due date', 'payment deadline', 'when to pay', 'last date', 'payment due',
                    'invoice due', 'bill due date', 'due on', 'expected payment date', 'invoice deadline'
                ],
                'category': 'dates',
                'description': 'Payment due date for the invoice'
            },
            
            'BILL_DATE': {
                'keywords': [
                    'bill date', 'invoice bill date', 'billing date', 'bill generated on', 'when billed',
                    'vendor billing date', 'invoice issue date', 'date of bill', 'when bill created', 'bill creation date'
                ],
                'category': 'dates',
                'description': 'Date when the bill was generated or issued'
            },            
            'DECLINE_DATE': {
                'keywords': [
                    'decline date', 'rejection date', 'invoice declined on', 'when declined', 'bill rejected date',
                    'date of rejection', 'invoice denial date', 'declined on', 'when rejected', 'bill decline timestamp'
                ],
                'category': 'dates',
                'description': 'Date when the invoice was declined or rejected'
            },
            
            'RECEIVING_DATE': {
                'keywords': [
                    'receiving date', 'date received', 'when received', 'invoice received', 'bill received',
                    'reception date', 'received on', 'document received date', 'received timestamp', 'invoice entry date'
                ],
                'category': 'dates',
                'description': 'Date when the invoice was received in the system'
            },
            
            'APPROVEDDATE1': {
                'keywords': [
                    'first approval date', 'initial approval', 'approved on', 'approval step one', 'invoice approved first',
                    'workflow approval one', 'approval level 1', 'initial verification date', 'bill approved date', 'first pass approval'
                ],
                'category': 'dates',
                'description': 'First level approval date in the workflow'
            },
            
            'APPROVEDDATE2': {
                'keywords': [
                    'second approval date', 'final approval', 'approved stage two', 'workflow approval two', 'date of last approval',
                    'second verified', 'full approval date', 'level 2 approval', 'invoice finalized on', 'second pass approval'
                ],
                'category': 'dates',
                'description': 'Second level or final approval date'
            },
            
            'INVOICE_DATE': {
                'keywords': [
                    'invoice date', 'date created', 'issued on', 'when invoice made', 'invoice generated',
                    'invoice creation date', 'invoice issue date', 'document date', 'date of invoice', 'invoice timestamp'
                ],
                'category': 'dates',
                'description': 'Date when the invoice was originally created or issued'
            },
            
            # 🔹 Financial Details
            'AMOUNT': {
                'keywords': [
                    'total amount', 'bill total', 'invoice value', 'total charge', 'grand total',
                    'invoice amount', 'amount billed', 'full amount', 'net amount', 'payable amount'
                ],
                'category': 'financial',
                'description': 'Total invoice amount including all charges'
            },
            
            'BALANCE_AMOUNT': {
                'keywords': [
                    'balance', 'unpaid amount', 'remaining amount', 'due balance', 'invoice balance',
                    'bill balance', 'outstanding amount', 'amount left', 'payment pending', 'left to pay'
                ],
                'category': 'financial',
                'description': 'Outstanding balance remaining to be paid'
            },
            
            'PAID': {
                'keywords': [
                    'amount paid', 'payment done', 'paid amount', 'received payment', 'paid total',
                    'invoice cleared', 'paid so far', 'cleared value', 'customer paid', 'payment received'
                ],
                'category': 'financial',
                'description': 'Amount that has been paid against the invoice'
            },
            
            'TOTAL_TAX': {
                'keywords': [
                    'total tax', 'tax amount', 'invoice tax', 'tax applied', 'billing tax',
                    'VAT total', 'GST total', 'tax value', 'tax on invoice', 'tax summary'
                ],
                'category': 'financial',
                'description': 'Total tax amount applied to the invoice'
            },
            
            'SUBTOTAL': {
                'keywords': [
                    'subtotal', 'amount before tax', 'pre-tax amount', 'invoice subtotal', 'base amount',
                    'service cost', 'product total', 'before tax', 'subtotal billed', 'initial amount'
                ],
                'category': 'financial',
                'description': 'Invoice amount before taxes and additional charges'
            },
              # 🔹 Invoice Content (Delimited Fields Support)
            'ITEMS_DESCRIPTION': {
                'keywords': [
                    'item description', 'billed items', 'services listed', 'product summary', 'what was billed',
                    'invoice items', 'line item detail', 'service/product detail', 'work done', 'what included',
                    'products', 'services', 'line items', 'individual items', 'item breakdown',
                    'product list', 'service list', 'what did I buy', 'what was purchased',
                    'itemized list', 'detailed breakdown', 'line by line', 'item details',
                    'cloud storage', 'cloud', 'storage', 'support', 'license', 'training', 'software',
                    'consulting', 'hosting', 'backup', 'security', 'email', 'database', 'web hosting',
                    'mobile app', 'data backup', 'ssl certificate', 'domain', 'server', 'subscription',
                    'maintenance', 'premium', 'professional', 'enterprise', 'standard', 'basic'
                ],
                'category': 'content',
                'description': 'Description of items or services billed (supports JSON arrays and CSV formats)'
            },
            
            'ITEMS_UNIT_PRICE': {
                'keywords': [
                    'unit price', 'price per item', 'rate', 'price per unit', 'cost per piece',
                    'per unit rate', 'item rate', 'line item price', 'cost per item', 'service rate',
                    'individual price', 'item cost', 'unit cost', 'pricing', 'rates',
                    'price breakdown', 'cost breakdown', 'unit pricing', 'item pricing'
                ],
                'category': 'content',
                'description': 'Price per unit of each item or service (supports multiple prices separated by delimiters)'
            },
            
            'ITEMS_QUANTITY': {
                'keywords': [
                    'quantity', 'item count', 'units billed', 'how many items', 'product count',
                    'total units', 'service quantity', 'number of units', 'billed units', 'invoice quantity',
                    'quantities', 'amounts', 'volumes', 'counts', 'numbers',
                    'quantity breakdown', 'unit breakdown', 'item counts', 'how much'
                ],
                'category': 'content',
                'description': 'Quantity of items or units of service provided (supports multiple quantities separated by delimiters)'
            },
            
            # 🔹 Status and Processing
            'STATUS': {
                'keywords': [
                    'invoice status', 'current state', 'approval status', 'is paid?', 'pending or approved?',
                    'status update', 'processing state', 'final status', 'payment status', 'invoice stage'
                ],
                'category': 'status',
                'description': 'Current processing status of the invoice'
            },
            
            'DECLINE_REASON': {
                'keywords': [
                    'reason for rejection', 'decline comment', 'why declined', 'invoice reason', 'rejection reason',
                    'comment on decline', 'failed reason', 'declined because', 'error in invoice', 'decline feedback'
                ],
                'category': 'status',
                'description': 'Reason provided when an invoice is declined or rejected'
            },
            
            # 🔹 Organizational and Accounting Info
            'DEPARTMENT': {
                'keywords': [
                    'department name', 'approving team', 'billing department', 'team responsible', 'cost center',
                    'invoice handler', 'processing unit', 'managing group', 'internal unit', 'finance department'
                ],
                'category': 'organization',
                'description': 'Department responsible for processing or approving the invoice'
            }
        }
        
        # Create reverse mapping for quick lookup
        self.keyword_to_column = {}
        for column, data in self.column_mappings.items():
            for keyword in data['keywords']:
                self.keyword_to_column[keyword.lower()] = column
        
        # Categories for organized display
        self.categories = {
            'identifiers': 'Core Identifiers',
            'dates': 'Dates and Timeline',
            'financial': 'Financial Details',
            'content': 'Invoice Content',
            'status': 'Status and Processing',
            'organization': 'Organizational Info'
        }
    
    def find_column_for_keyword(self, keyword: str) -> Optional[str]:
        """Find the database column name for a given user keyword"""
        return self.keyword_to_column.get(keyword.lower())
    
    def get_keywords_for_column(self, column: str) -> List[str]:
        """Get all keywords associated with a database column"""
        return self.column_mappings.get(column, {}).get('keywords', [])
    
    def get_columns_by_category(self, category: str) -> List[str]:
        """Get all columns belonging to a specific category"""
        return [col for col, data in self.column_mappings.items() 
                if data.get('category') == category]
    
    def get_enhanced_prompt_context(self, vendor_id: str, case_id: Optional[str] = None) -> str:
        """Generate comprehensive prompt context with column mappings for LLM"""
        
        context = f"""
DATABASE CONTEXT:
- Database: FINOPSYS_DB
- Schema: PUBLIC  
- Table: AI_INVOICE

COMPREHENSIVE COLUMN MAPPING GUIDE:

🔹 CORE IDENTIFIERS:
"""
        
        # Add identifiers section
        for column in self.get_columns_by_category('identifiers'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:5])  # First 5 keywords
            context += f"   • {column}: {keywords}...\n"
        
        context += "\n🔹 DATES AND TIMELINE:\n"
        for column in self.get_columns_by_category('dates'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:4])
            context += f"   • {column}: {keywords}...\n"
        
        context += "\n🔹 FINANCIAL DETAILS:\n"
        for column in self.get_columns_by_category('financial'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:4])
            context += f"   • {column}: {keywords}...\n"
        
        context += "\n🔹 INVOICE CONTENT:\n"
        for column in self.get_columns_by_category('content'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:4])
            context += f"   • {column}: {keywords}...\n"
        
        context += "\n🔹 STATUS AND PROCESSING:\n"
        for column in self.get_columns_by_category('status'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:4])
            context += f"   • {column}: {keywords}...\n"        
        context += "\n🔹 ORGANIZATIONAL INFO:\n"
        for column in self.get_columns_by_category('organization'):
            keywords = ', '.join(self.get_keywords_for_column(column)[:4])
            context += f"   • {column}: {keywords}...\n"
        
        context += f"""

DELIMITED FIELDS SUPPORT:
The following columns contain multiple items separated by delimiters (comma, semicolon, etc.):
• ITEMS_DESCRIPTION: Multiple product/service names
• ITEMS_UNIT_PRICE: Multiple prices (one per item)  
• ITEMS_QUANTITY: Multiple quantities (one per item)

For item-level queries, include these columns to get detailed breakdowns.

CRITICAL SECURITY REQUIREMENTS:
1. MANDATORY: ALWAYS include WHERE vendor_id = '{vendor_id}' in EVERY query
2. ONLY query the AI_INVOICE table
3. Generate ONLY the SQL query, no explanations
4. Use Snowflake SQL syntax
5. Map user keywords to correct column names using the guide above

KEYWORD MAPPING EXAMPLES:
- "How many invoices" → COUNT(*) FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'
- "Total amount/bill total" → SUM(AMOUNT) WHERE vendor_id = '{vendor_id}'
- "Unpaid/balance/outstanding" → SUM(BALANCE_AMOUNT) WHERE vendor_id = '{vendor_id}'
- "Due date/payment deadline" → DUE_DATE WHERE vendor_id = '{vendor_id}'
- "Invoice status/current state" → STATUS WHERE vendor_id = '{vendor_id}'
- "What items/products" → SELECT ITEMS_DESCRIPTION, ITEMS_UNIT_PRICE, ITEMS_QUANTITY WHERE vendor_id = '{vendor_id}'
- "Item breakdown/line items" → SELECT CASE_ID, ITEMS_* FROM AI_INVOICE WHERE vendor_id = '{vendor_id}'
- "Cloud storage cost" → SELECT * FROM AI_INVOICE WHERE vendor_id = '{vendor_id}' AND LOWER(ITEMS_DESCRIPTION) LIKE '%cloud storage%'
- "Support pricing" → SELECT * FROM AI_INVOICE WHERE vendor_id = '{vendor_id}' AND LOWER(ITEMS_DESCRIPTION) LIKE '%support%'

PRODUCT-SPECIFIC QUERY GUIDANCE:
- For questions about specific products/services, always include ITEMS_DESCRIPTION, ITEMS_UNIT_PRICE, ITEMS_QUANTITY
- Use LIKE clauses to search within JSON arrays and CSV data: LOWER(ITEMS_DESCRIPTION) LIKE '%product_name%'
- Include ORDER BY INVOICE_DATE DESC for recent data first
- Add LIMIT 100 for performance on large datasets

Current vendor context: vendor_id = {vendor_id}"""
        
        if case_id:
            context += f"\nCurrent case context: case_id = {case_id}"
        
        return context
    
    def get_all_columns(self) -> List[str]:
        """Get all available database columns"""
        return list(self.column_mappings.keys())
    
    def search_columns_by_keyword(self, search_term: str) -> List[tuple]:
        """Search for columns that match a keyword or partial keyword"""
        search_term = search_term.lower()
        matches = []
        
        for column, data in self.column_mappings.items():
            for keyword in data['keywords']:
                if search_term in keyword.lower():
                    matches.append((column, keyword, data['category']))
        
        return matches
    
    def get_category_summary(self) -> Dict[str, Dict]:
        """Get summary of all categories and their columns"""
        summary = {}
        for category_key, category_name in self.categories.items():
            columns = self.get_columns_by_category(category_key)
            summary[category_name] = {
                'columns': columns,
                'count': len(columns),
                'key': category_key
            }
        return summary
    
    def validate_column_exists(self, column: str) -> bool:
        """Check if a column exists in the mapping"""
        return column.upper() in self.column_mappings
    
    def get_column_description(self, column: str) -> Optional[str]:
        """Get description for a specific column"""
        return self.column_mappings.get(column.upper(), {}).get('description')
        
        if partial_matches:
            # Return the first partial match
            best_match = partial_matches[0]
            return {
                'found': True,
                'column': best_match['column'],
                'confidence': best_match['confidence'],
                'matched_keyword': best_match['keyword'],
                'alternatives': partial_matches[1:5]  # Show up to 4 alternatives
            }
        
        return {
            'found': False,
            'suggestions': self._get_similar_keywords(user_input_lower)
        }
    
    def _get_similar_keywords(self, user_input: str, limit: int = 5) -> List[str]:
        """Get similar keywords for suggestions"""
        # Simple similarity based on common words
        suggestions = []
        user_words = set(user_input.split())
        
        for keyword in self.keyword_to_column.keys():
            keyword_words = set(keyword.split())
            if user_words.intersection(keyword_words):
                suggestions.append(keyword)
        
        return suggestions[:limit]

# Global instance for easy import
column_keywords = ColumnKeywordsMapping()
