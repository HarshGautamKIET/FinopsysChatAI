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
                    'case', 'case number', 'get case', 'case detail', 'what is case', 'case info',
                    'invoice case', 'case reference', 'bill case', 'case id', 'linked case',
                    'case identifier', 'show case', 'find case', 'case data', 'case record',
                    'which case', 'case associated', 'case related', 'case belong', 'case file',
                    'matter', 'matter number', 'ticket', 'ticket number', 'issue number',
                    'case code', 'case ref', 'linked to case', 'associated case', 'grouped case'
                ],
                'category': 'identifiers',
                'description': 'Unique case identifier for invoice grouping'
            },
            
            'BILL_ID': {
                'keywords': [
                    'bill', 'bill id', 'get bill', 'bill reference', 'bill number', 'bill no',
                    'show bill', 'invoice bill', 'billing id', 'what is bill', 'bill detail',
                    'bill identifier', 'find bill', 'bill data', 'bill record', 'which bill',
                    'billing document', 'bill ref', 'billing reference', 'bill code',
                    'bill associated', 'statement', 'statement number', 'billing statement',
                    'document id', 'document number', 'bill doc', 'billing doc'
                ],
                'category': 'identifiers',
                'description': 'Unique billing document identifier'
            },
            
            'CUSTOMER_ID': {
                'keywords': [
                    'customer', 'customer id', 'client', 'client number', 'customer reference',
                    'invoice customer', 'who is customer', 'customer info', 'bill to', 'client id',
                    'customer identifier', 'customer code', 'customer name', 'client name',
                    'buyer', 'purchaser', 'account holder', 'customer account', 'client account',
                    'billed to', 'invoiced to', 'customer detail', 'client detail', 'who bought',
                    'who ordered', 'customer ref', 'client ref', 'account number', 'account id',
                    'customer number', 'client code', 'end customer', 'final customer'
                ],
                'category': 'identifiers',
                'description': 'Customer or client identifier'
            },
            
            'VENDOR_ID': {
                'keywords': [
                    'vendor', 'vendor id', 'supplier', 'supplier id', 'from whom', 'who sent',
                    'vendor reference', 'seller', 'vendor info', 'invoice from', 'supplier name',
                    'vendor identifier', 'vendor code', 'vendor name', 'supplier name',
                    'provider', 'service provider', 'company', 'vendor company', 'supplier company',
                    'billing vendor', 'invoice vendor', 'vendor detail', 'supplier detail',
                    'who provided', 'who delivered', 'vendor ref', 'supplier ref', 'source',
                    'vendor number', 'supplier number', 'merchant', 'contractor', 'vendor firm'
                ],
                'category': 'identifiers',
                'description': 'Vendor or supplier identifier'
            },
            
            'INVOICE_ID': {
                'keywords': [
                    'invoice', 'invoice id', 'invoice number', 'billing id', 'invoice ref',
                    'bill number', 'show invoice', 'get invoice', 'what is invoice', 'invoice detail',
                    'invoice identifier', 'invoice no', 'find invoice', 'invoice data', 'invoice record',
                    'which invoice', 'invoice code', 'invoice reference', 'inv number', 'inv id',
                    'document number', 'receipt number', 'transaction id', 'billing number',
                    'invoice doc', 'billing doc', 'payment request', 'charge number', 'inv ref'
                ],
                'category': 'identifiers',
                'description': 'Unique invoice identifier'
            },
            
            # 🔹 Dates and Timeline
            'DUE_DATE': {
                'keywords': [
                    'due date', 'payment deadline', 'when to pay', 'last date', 'payment due',
                    'invoice due', 'bill due date', 'due on', 'expected payment date', 'invoice deadline',
                    'deadline', 'pay by', 'payment by', 'due by', 'expire date', 'expiry date',
                    'final date', 'last day', 'cutoff date', 'payment cutoff', 'when due',
                    'maturity date', 'payment maturity', 'settlement date', 'overdue date',
                    'payment schedule', 'due timeline', 'payment timeline', 'when expires',
                    'term date', 'payment term', 'net due', 'payable by', 'must pay by'
                ],
                'category': 'dates',
                'description': 'Payment due date for the invoice'
            },
            
            'BILL_DATE': {
                'keywords': [
                    'bill date', 'invoice bill date', 'billing date', 'bill generated on', 'when billed',
                    'vendor billing date', 'invoice issue date', 'date of bill', 'when bill created', 'bill creation date',
                    'billed on', 'generated on', 'created on', 'issued on', 'bill issued',
                    'invoice date', 'billing timestamp', 'date billed', 'bill time', 'bill stamp',
                    'when generated', 'generation date', 'origin date', 'bill origin', 'source date',
                    'vendor date', 'supplier date', 'issue timestamp', 'document date', 'bill document date'
                ],
                'category': 'dates',
                'description': 'Date when the bill was generated or issued'
            },
            
            'DECLINE_DATE': {
                'keywords': [
                    'decline date', 'rejection date', 'invoice declined on', 'when declined', 'bill rejected date',
                    'date of rejection', 'invoice denial date', 'declined on', 'when rejected', 'bill decline timestamp',
                    'rejected on', 'denied on', 'refusal date', 'when refused', 'denial timestamp',
                    'decline time', 'rejection time', 'when denied', 'disapproval date', 'rejection timestamp',
                    'declined timestamp', 'refused date', 'when disapproved', 'negative response date',
                    'decline response', 'rejection response', 'when said no', 'no date', 'veto date'
                ],
                'category': 'dates',
                'description': 'Date when the invoice was declined or rejected'
            },
            
            'RECEIVING_DATE': {
                'keywords': [
                    'receiving date', 'date received', 'when received', 'invoice received', 'bill received',
                    'reception date', 'received on', 'document received date', 'received timestamp', 'invoice entry date',
                    'arrival date', 'when arrived', 'delivered date', 'delivery date', 'intake date',
                    'submission date', 'when submitted', 'received time', 'receipt time', 'arrival time',
                    'when delivered', 'entry date', 'input date', 'upload date', 'when uploaded',
                    'processing date', 'when processed', 'logged date', 'when logged', 'recorded date'
                    'date created', 'issued on', 'when invoice made', 'invoice generated',
                    'invoice creation date', 'invoice issue date', 'document date', 'date of invoice', 'invoice timestamp',
                    'created on', 'generated on', 'made on', 'when created', 'when issued', 'when made',
                    'invoice originated', 'origin date', 'invoice origin', 'creation timestamp', 'issue timestamp',
                    'document timestamp', 'invoice time', 'creation time', 'issue time', 'when originated',
                    'invoice start date', 'start date', 'initiation date', 'when initiated', 'invoice birth date'
                ],
                'category': 'dates',
                'description': 'Date when the invoice was received in the system'
            },
            
            'APPROVEDDATE1': {
                'keywords': [
                    'first approval date', 'initial approval', 'approved on', 'approval step one', 'invoice approved first',
                    'workflow approval one', 'approval level 1', 'initial verification date', 'bill approved date', 'first pass approval',
                    'primary approval', 'level one approval', 'step 1 approval', 'first stage approval', 'initial sign off',
                    'first review date', 'preliminary approval', 'stage 1 date', 'first authorized', 'initial authorized',
                    'first verified', 'primary verification', 'first clearance', 'initial clearance', 'first green light',
                    'initial consent', 'first consent', 'primary consent', 'level 1 date', 'tier 1 approval'
                ],
                'category': 'dates',
                'description': 'First level approval date in the workflow'
            },
            
            'APPROVEDDATE2': {
                'keywords': [
                    'second approval date', 'final approval', 'approved stage two', 'workflow approval two', 'date of last approval',
                    'second verified', 'full approval date', 'level 2 approval', 'invoice finalized on', 'second pass approval',
                    'final verification', 'stage 2 approval', 'step 2 approval', 'second stage approval', 'final sign off',
                    'second review date', 'ultimate approval', 'stage 2 date', 'second authorized', 'final authorized',
                    'complete approval', 'full verification', 'final clearance', 'complete clearance', 'final green light',
                    'final consent', 'complete consent', 'level 2 date', 'tier 2 approval', 'conclusive approval'
                ],
                'category': 'dates',
                'description': 'Second level or final approval date'
            },
                        
            # 🔹 Financial Details
            'AMOUNT': {
                'keywords': [
                    'total amount', 'bill total', 'invoice value', 'total charge', 'grand total',
                    'invoice amount', 'amount billed', 'full amount', 'net amount', 'payable amount',
                    'total value', 'total cost', 'total price', 'overall amount', 'complete amount',
                    'sum total', 'aggregate amount', 'total due', 'invoice total', 'bill amount',
                    'full cost', 'entire amount', 'whole amount', 'complete cost', 'total bill',
                    'money owed', 'amount owed', 'total owing', 'final amount', 'gross amount',
                    'full value', 'invoice value', 'billed amount', 'charged amount', 'total charged'
                ],
                'category': 'financial',
                'description': 'Total invoice amount including all charges'
            },
            
            'BALANCE_AMOUNT': {
                'keywords': [
                    'balance', 'unpaid amount', 'remaining amount', 'due balance', 'invoice balance',
                    'bill balance', 'outstanding amount', 'amount left', 'payment pending', 'left to pay',
                    'remaining balance', 'unpaid balance', 'amount remaining', 'still owe', 'still due',
                    'outstanding balance', 'pending amount', 'amount outstanding', 'unsettled amount',
                    'open balance', 'current balance', 'account balance', 'what is owed', 'money left',
                    'unpaid portion', 'remaining portion', 'balance due', 'amount due', 'overdue amount',
                    'arrears', 'debt', 'liability', 'current debt', 'pending payment', 'open amount'
                ],
                'category': 'financial',
                'description': 'Outstanding balance remaining to be paid'
            },
            
            'PAID': {
                'keywords': [
                    'amount paid', 'payment done', 'paid amount', 'received payment', 'paid total',
                    'invoice cleared', 'paid so far', 'cleared value', 'customer paid', 'payment received',
                    'payments made', 'money received', 'amount received', 'settled amount', 'cleared amount',
                    'paid portion', 'payment portion', 'remittance', 'money paid', 'cash received',
                    'payment total', 'sum paid', 'total payments', 'cumulative payment', 'payment sum',
                    'received money', 'collected amount', 'payment collected', 'funds received', 'paid value',
                    'settled portion', 'payment applied', 'credit received', 'money collected', 'payment credited'
                ],
                'category': 'financial',
                'description': 'Amount that has been paid against the invoice'
            },
            
            'TOTAL_TAX': {
                'keywords': [
                    'total tax', 'tax amount', 'invoice tax', 'tax applied', 'billing tax',
                    'VAT total', 'GST total', 'tax value', 'tax on invoice', 'tax summary',
                    'tax charge', 'tax portion', 'tax component', 'sales tax', 'service tax',
                    'government tax', 'tax levy', 'taxation', 'tax liability', 'tax due',
                    'tax owed', 'withholding tax', 'income tax', 'excise tax', 'duty tax',
                    'customs tax', 'import tax', 'tax total', 'aggregate tax', 'combined tax',
                    'all taxes', 'tax sum', 'cumulative tax', 'tax breakdown', 'tax details'
                ],
                'category': 'financial',
                'description': 'Total tax amount applied to the invoice'
            },
            
            'SUBTOTAL': {
                'keywords': [
                    'subtotal', 'amount before tax', 'pre-tax amount', 'invoice subtotal', 'base amount',
                    'service cost', 'product total', 'before tax', 'subtotal billed', 'initial amount',
                    'net amount', 'gross amount', 'principal amount', 'core amount', 'basic amount',
                    'raw amount', 'pure amount', 'untaxed amount', 'tax-free amount', 'pre-levy amount',
                    'cost before tax', 'price before tax', 'value before tax', 'charge before tax',
                    'baseline amount', 'foundation amount', 'original amount', 'primary amount',
                    'sub amount', 'partial total', 'line total', 'item total', 'service subtotal'
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
                    'product list', 'service list', 'what did I buy', 'what was purchased', 'purchased items',
                    'itemized list', 'detailed breakdown', 'line by line', 'item details', 'product details',
                    'service details', 'what services', 'what products', 'items bought', 'goods purchased',
                    'deliverables', 'offerings', 'merchandise', 'inventory', 'catalog items', 'order items',
                    'purchased goods', 'billed services', 'work performed', 'tasks completed', 'services rendered',
                    'product names', 'service names', 'item names', 'description list', 'product catalog',
                    'service catalog', 'item catalog', 'goods description', 'service description',
                    # Technology/Cloud Services
                    'cloud storage', 'cloud', 'storage', 'support', 'license', 'training', 'software',
                    'consulting', 'hosting', 'backup', 'security', 'email', 'database', 'web hosting',
                    'mobile app', 'data backup', 'ssl certificate', 'domain', 'server', 'subscription',
                    'maintenance', 'premium', 'professional', 'enterprise', 'standard', 'basic',
                    'SaaS', 'platform', 'infrastructure', 'monitoring', 'analytics', 'API', 'CDN',
                    'bandwidth', 'computing', 'virtual machine', 'instance', 'container', 'kubernetes',
                    # Additional common service types
                    'development', 'design', 'marketing', 'advertising', 'management', 'administration',
                    'integration', 'implementation', 'migration', 'deployment', 'configuration', 'setup',
                    'customization', 'optimization', 'performance', 'scalability', 'reliability',
                    'availability', 'disaster recovery', 'business continuity', 'compliance', 'audit'
                ],
                'category': 'content',
                'description': 'Description of items or services billed (supports JSON arrays and CSV formats)'
            },
            
            'ITEMS_UNIT_PRICE': {
                'keywords': [
                    'unit price', 'price per item', 'rate', 'price per unit', 'cost per piece',
                    'per unit rate', 'item rate', 'line item price', 'cost per item', 'service rate',
                    'individual price', 'item cost', 'unit cost', 'pricing', 'rates', 'price each',
                    'price breakdown', 'cost breakdown', 'unit pricing', 'item pricing', 'per piece cost',
                    'single unit price', 'cost each', 'rate per unit', 'individual cost', 'per item cost',
                    'hourly rate', 'daily rate', 'monthly rate', 'annual rate', 'subscription rate',
                    'license cost', 'per license price', 'seat cost', 'user cost', 'per user price',
                    'service price', 'product price', 'unit charge', 'individual charge', 'per unit charge',
                    'cost per service', 'price per service', 'rate card', 'tariff', 'fee structure',
                    'pricing model', 'cost model', 'charge rate', 'billing rate', 'standard rate'
                ],
                'category': 'content',
                'description': 'Price per unit of each item or service (supports multiple prices separated by delimiters)'
            },
            
            'ITEMS_QUANTITY': {
                'keywords': [
                    'quantity', 'item count', 'units billed', 'how many items', 'product count',
                    'total units', 'service quantity', 'number of units', 'billed units', 'invoice quantity',
                    'quantities', 'amounts', 'volumes', 'counts', 'numbers', 'how many',
                    'quantity breakdown', 'unit breakdown', 'item counts', 'how much', 'volume billed',
                    'units ordered', 'units delivered', 'units purchased', 'units provided', 'units consumed',
                    'usage quantity', 'consumption', 'utilization', 'hours worked', 'hours billed',
                    'days billed', 'months billed', 'licenses', 'seats', 'users', 'instances',
                    'GB used', 'TB used', 'MB used', 'bandwidth used', 'storage used', 'compute hours',
                    'transaction count', 'API calls', 'requests', 'operations', 'executions',
                    'number purchased', 'amount used', 'total consumed', 'aggregate quantity'
                ],
                'category': 'content',
                'description': 'Quantity of items or units of service provided (supports multiple quantities separated by delimiters)'
            },
            
            # 🔹 Status and Processing
            'STATUS': {
                'keywords': [
                    'invoice status', 'current state', 'approval status', 'is paid?', 'pending or approved?',
                    'status update', 'processing state', 'final status', 'payment status', 'invoice stage',
                    'current status', 'bill status', 'document status', 'workflow status', 'approval state',
                    'payment state', 'processing stage', 'invoice condition', 'bill condition', 'state',
                    'condition', 'phase', 'stage', 'step', 'level', 'position', 'standing',
                    'approval level', 'review status', 'verification status', 'clearance status',
                    'authorization status', 'completion status', 'progress status', 'workflow state',
                    'is approved', 'is pending', 'is declined', 'is paid', 'is processed', 'is complete',
                    'what status', 'which status', 'current phase', 'where is invoice', 'invoice position'
                ],
                'category': 'status',
                'description': 'Current processing status of the invoice'
            },
            
            'DECLINE_REASON': {
                'keywords': [
                    'reason for rejection', 'decline comment', 'why declined', 'invoice reason', 'rejection reason',
                    'comment on decline', 'failed reason', 'declined because', 'error in invoice', 'decline feedback',
                    'rejection comment', 'denial reason', 'refusal reason', 'why rejected', 'why denied',
                    'decline note', 'rejection note', 'denial note', 'refusal note', 'disapproval reason',
                    'negative feedback', 'rejection feedback', 'decline explanation', 'rejection explanation',
                    'denial explanation', 'refusal explanation', 'why refused', 'what went wrong',
                    'error reason', 'problem reason', 'issue reason', 'failure reason', 'decline cause',
                    'rejection cause', 'denial cause', 'refusal cause', 'decline justification',
                    'rejection justification', 'denial justification', 'refusal justification'
                ],
                'category': 'status',
                'description': 'Reason provided when an invoice is declined or rejected'
            },
            
            # 🔹 Organizational and Accounting Info
            'DEPARTMENT': {
                'keywords': [
                    'department name', 'approving team', 'billing department', 'team responsible', 'cost center',
                    'invoice handler', 'processing unit', 'managing group', 'internal unit', 'finance department',
                    'department', 'dept', 'division', 'unit', 'section', 'group', 'team', 'organization',
                    'business unit', 'cost centre', 'profit center', 'profit centre', 'functional area',
                    'work group', 'working group', 'organizational unit', 'org unit', 'branch',
                    'office', 'facility', 'location', 'site', 'center', 'centre', 'hub',
                    'responsible department', 'owning department', 'managing department', 'handling department',
                    'processing department', 'accounting department', 'finance unit', 'admin department',
                    'which department', 'what department', 'department responsible', 'department handling'
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
