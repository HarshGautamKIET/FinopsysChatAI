"""
LLM Response Restrictions for FinOpsys ChatAI
This module defines what information the LLM should never reveal to frontend users
for security and privacy compliance.
"""

from typing import List, Dict, Set, Optional
import re
import logging

logger = logging.getLogger(__name__)

class LLMResponseRestrictions:
    """Defines and enforces restrictions on LLM responses to protect sensitive data"""
    
    def __init__(self):
        # Sensitive columns that should NEVER be shown to users
        self.restricted_columns = {
            'CASE_ID',
            'CUSTOMER_ID', 
            'VENDOR_ID',
            'BILL_ID',
            'INVOICE_ID'
        }
        
        # Patterns that indicate sensitive information
        self.sensitive_patterns = [
            r'\bcase_id\s*=\s*[\'"]?([^\'"\s,)]+)',  # case_id = 'value'
            r'\bcustomer_id\s*=\s*[\'"]?([^\'"\s,)]+)',  # customer_id = 'value'
            r'\bvendor_id\s*=\s*[\'"]?([^\'"\s,)]+)',  # vendor_id = 'value'
            r'\bbill_id\s*=\s*[\'"]?([^\'"\s,)]+)',  # bill_id = 'value'
            r'\binvoice_id\s*=\s*[\'"]?([^\'"\s,)]+)',  # invoice_id = 'value'
            r'\bcase\s*:\s*([^,\s]+)',  # case: value
            r'\bcustomer\s*:\s*([^,\s]+)',  # customer: value
            r'\bvendor\s*:\s*([^,\s]+)',  # vendor: value
        ]
        
        # Terms that should be filtered from responses
        self.forbidden_terms = {
            'case_id', 'customer_id', 'vendor_id', 'bill_id', 'invoice_id',
            'case id', 'customer id', 'vendor id', 'bill id', 'invoice id',
            'case identifier', 'customer identifier', 'vendor identifier',
            'filtered for vendor', 'filtered for case', 'filtered for customer'
        }
        
        # Safe replacement terms
        self.safe_replacements = {
            'case_id': 'invoice case',
            'customer_id': 'customer',
            'vendor_id': 'vendor',
            'bill_id': 'invoice',
            'invoice_id': 'invoice number',
            'filtered for vendor id': 'for your account',
            'filtered for case id': 'for your case',
            'filtered for customer id': 'for your records'
        }
    
    def filter_response(self, response: str) -> str:
        """
        Filter LLM response to remove sensitive information
        
        Args:
            response (str): Original LLM response
            
        Returns:
            str: Filtered response with sensitive data removed
        """
        filtered_response = response
        
        # Remove sensitive patterns
        for pattern in self.sensitive_patterns:
            filtered_response = re.sub(pattern, '[FILTERED]', filtered_response, flags=re.IGNORECASE)
        
        # Replace forbidden terms with safe alternatives
        for term, replacement in self.safe_replacements.items():
            filtered_response = re.sub(
                r'\b' + re.escape(term) + r'\b', 
                replacement, 
                filtered_response, 
                flags=re.IGNORECASE
            )
        
        # Remove any remaining forbidden terms
        for term in self.forbidden_terms:
            filtered_response = re.sub(
                r'\b' + re.escape(term) + r'\b', 
                '[FILTERED]', 
                filtered_response, 
                flags=re.IGNORECASE
            )
        
        # Remove specific vendor filtering messages
        vendor_filter_patterns = [
            r'🔒\s*Results filtered for Vendor ID:\s*[^\s\n]+',
            r'Results filtered for Vendor ID:\s*[^\s\n]+',
            r'Filtered for vendor_id\s*[^\s\n]+',
            r'vendor_id\s*=\s*[\'"]?[^\'"\s,)]+',
        ]
        
        for pattern in vendor_filter_patterns:
            filtered_response = re.sub(pattern, '', filtered_response, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and newlines
        filtered_response = re.sub(r'\n\s*\n', '\n', filtered_response)
        filtered_response = re.sub(r'\s+', ' ', filtered_response)
        filtered_response = filtered_response.strip()
        
        # Log if filtering occurred
        if filtered_response != response:
            logger.info("🔒 Sensitive information filtered from LLM response")
        
        return filtered_response
    
    def validate_response_safety(self, response: str) -> Dict[str, any]:
        """
        Validate if a response contains sensitive information
        
        Args:
            response (str): LLM response to validate
            
        Returns:
            dict: Validation results with safety status and issues found
        """
        issues = []
        
        # Check for sensitive patterns
        for i, pattern in enumerate(self.sensitive_patterns):
            matches = re.findall(pattern, response, flags=re.IGNORECASE)
            if matches:
                issues.append({
                    'type': 'sensitive_pattern',
                    'pattern_index': i,
                    'matches': matches
                })
        
        # Check for forbidden terms
        found_terms = []
        for term in self.forbidden_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', response, flags=re.IGNORECASE):
                found_terms.append(term)
        
        if found_terms:
            issues.append({
                'type': 'forbidden_terms',
                'terms': found_terms
            })
        
        is_safe = len(issues) == 0
        
        return {
            'is_safe': is_safe,
            'issues': issues,
            'needs_filtering': not is_safe
        }
    
    def get_response_guidelines(self) -> str:
        """Get guidelines for LLM responses"""
        return """
RESPONSE GUIDELINES - CRITICAL SECURITY REQUIREMENTS:

❌ NEVER INCLUDE IN RESPONSES:
- case_id, customer_id, vendor_id, bill_id, invoice_id values
- Any specific ID numbers or identifiers
- "Results filtered for Vendor ID: XXX" messages
- Database column names ending in "_id"
- References to specific case numbers or vendor codes

✅ SAFE TO INCLUDE:
- Aggregated financial data (totals, counts, averages)
- Status information (paid, pending, approved)
- Date ranges and periods
- General descriptions and categories
- Calculated metrics and summaries

🔄 SAFE REPLACEMENTS:
- Instead of "vendor_id": use "your account" or "your vendor data"
- Instead of "case_id": use "your case" or "your invoices"
- Instead of "customer_id": use "customer" or "client"
- Instead of specific IDs: use "your records" or "your data"

EXAMPLE SAFE RESPONSES:
✅ "You have 15 invoices with a total amount of $45,230"
✅ "Your unpaid balance is $12,500 across 5 outstanding invoices"
✅ "3 invoices are overdue and require immediate attention"

❌ UNSAFE RESPONSES:
❌ "Results filtered for Vendor ID: V123456"
❌ "Found case_id: CASE789 with customer_id: CUST456"
❌ "Your vendor_id V123456 has the following data..."
"""
    
    def create_safe_context_prompt(self, vendor_id: str) -> str:
        """Create a context prompt that encourages safe responses"""
        return f"""
You are a financial data assistant helping users analyze their invoice data.

CRITICAL: Never reveal specific IDs, case numbers, vendor codes, or customer identifiers in your responses.
Always speak in terms of "your data", "your invoices", "your account" rather than showing specific ID values.

Current session: You are helping a user analyze their vendor invoice data.
Data scope: All responses should be filtered to this user's data only.

Focus on providing helpful financial insights while maintaining data privacy and security.
"""

# Global instance for easy import
response_restrictions = LLMResponseRestrictions()
