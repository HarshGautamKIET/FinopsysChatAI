import re
from typing import Dict, List

class QueryValidator:
    """Enhanced SQL query validation and security"""
    
    ALLOWED_OPERATIONS = ['SELECT']
    BLOCKED_KEYWORDS = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    MAX_QUERY_LENGTH = 1000
    
    @classmethod
    def validate_query(cls, query: str, vendor_id: str) -> Dict:
        """Comprehensive query validation"""
        query_upper = query.upper().strip()
        
        # Length check
        if len(query) > cls.MAX_QUERY_LENGTH:
            return {"valid": False, "error": "Query too long"}
        
        # Operation check
        if not any(query_upper.startswith(op) for op in cls.ALLOWED_OPERATIONS):
            return {"valid": False, "error": "Only SELECT operations allowed"}
        
        # Blocked keywords
        for keyword in cls.BLOCKED_KEYWORDS:
            if keyword in query_upper:
                return {"valid": False, "error": f"Operation '{keyword}' not permitted"}
        
        # Vendor filtering check
        if f"VENDOR_ID = '{vendor_id}'" not in query.upper():
            return {"valid": False, "error": "Query must include vendor_id filtering"}
        
        # SQL injection patterns
        injection_patterns = [
            r"'.*OR.*'.*'",  # OR injection
            r"'.*UNION.*SELECT",  # UNION injection
            r"--",  # SQL comments
            r"/\*.*\*/"  # Multi-line comments
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_upper):
                return {"valid": False, "error": "Potentially unsafe query pattern detected"}
        
        return {"valid": True, "error": None}