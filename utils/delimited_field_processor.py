"""
Delimited Field Processor for FinOpsys ChatAI
Handles parsing and processing of delimited text fields containing multiple items
Supports both JSON arrays and comma-separated values
"""

import logging
import re
import json
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd

logger = logging.getLogger(__name__)

class DelimitedFieldProcessor:
    """Processes delimited text fields containing multiple item entries"""
    
    def __init__(self):
        """Initialize the processor with common delimiters and patterns"""
        self.common_delimiters = [',', ';', '|', '\n', '\t', '||', ';;']
        self.item_columns = ['items_description', 'items_unit_price', 'items_quantity']
        self.numeric_columns = ['items_unit_price', 'items_quantity']
        
    def detect_delimiter(self, text: str) -> str:
        """Detect the most likely delimiter used in the text"""
        if not text or not isinstance(text, str):
            return ','
        
        delimiter_counts = {}
        for delimiter in self.common_delimiters:
            delimiter_counts[delimiter] = text.count(delimiter)
          # Return the delimiter with the highest count, default to comma
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        return best_delimiter if delimiter_counts[best_delimiter] > 0 else ','
    
    def parse_delimited_field(self, text, delimiter: Optional[str] = None) -> List[str]:
        """Parse a delimited text field into individual items - supports Python lists, JSON arrays and CSV"""
        if not text:
            return []
        
        # If it's already a Python list, return it directly (converted to strings)
        if isinstance(text, list):
            return [str(item).strip() for item in text if item is not None and str(item).strip()]
        
        # If it's not a string, convert it to string first
        if not isinstance(text, str):
            text = str(text)
        
        # First, try to parse as JSON array
        try:
            if text.strip().startswith('[') and text.strip().endswith(']'):
                json_data = json.loads(text)
                if isinstance(json_data, list):
                    # Convert all items to strings and clean them
                    return [str(item).strip() for item in json_data if item is not None and str(item).strip()]
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, fall back to delimiter-based parsing
            logger.debug(f"JSON parsing failed for: {text[:100]}... Falling back to delimiter parsing")
        
        # Fallback to delimiter-based parsing
        if delimiter is None:
            delimiter = self.detect_delimiter(text)
        
        # Split by delimiter and clean up each item
        items = [item.strip() for item in text.split(delimiter)]
          # Remove empty items and clean quotes
        items = [item.strip('"\'') for item in items if item.strip()]
        
        return items
    
    def parse_numeric_delimited_field(self, text, delimiter: Optional[str] = None) -> List[float]:
        """Parse a delimited numeric field into individual numeric values - supports Python lists, JSON arrays and CSV"""
        if not text:
            return []
        
        # If it's already a Python list, convert directly to floats
        if isinstance(text, list):
            numeric_items = []
            for item in text:
                try:
                    if isinstance(item, (int, float)):
                        numeric_items.append(float(item))
                    elif isinstance(item, str):
                        # Remove currency symbols and other non-numeric characters
                        cleaned_item = re.sub(r'[^\d.-]', '', item)
                        if cleaned_item:
                            numeric_items.append(float(cleaned_item))
                        else:
                            numeric_items.append(0.0)
                    else:
                        numeric_items.append(float(item))
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert list item to float: {item}")
                    numeric_items.append(0.0)
            return numeric_items
        
        # If it's not a string, convert it to string first
        if not isinstance(text, str):
            text = str(text)
        
        # First, try to parse as JSON array
        try:
            if text.strip().startswith('[') and text.strip().endswith(']'):
                json_data = json.loads(text)
                if isinstance(json_data, list):
                    numeric_items = []
                    for item in json_data:
                        try:
                            if isinstance(item, (int, float)):
                                numeric_items.append(float(item))
                            elif isinstance(item, str):
                                # Remove currency symbols and other non-numeric characters
                                cleaned_item = re.sub(r'[^\d.-]', '', item)
                                if cleaned_item:
                                    numeric_items.append(float(cleaned_item))
                                else:
                                    numeric_items.append(0.0)
                            else:
                                numeric_items.append(0.0)
                        except (ValueError, TypeError):
                            numeric_items.append(0.0)
                    return numeric_items
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, fall back to delimiter-based parsing
            logger.debug(f"JSON parsing failed for numeric field: {text[:100]}...")
        
        # Fallback to delimiter-based parsing
        items = self.parse_delimited_field(text, delimiter)
        numeric_items = []
        
        for item in items:
            try:
                # Remove currency symbols and other non-numeric characters
                cleaned_item = re.sub(r'[^\d.-]', '', item)
                if cleaned_item:
                    numeric_items.append(float(cleaned_item))
                else:
                    numeric_items.append(0.0)
            except (ValueError, TypeError):
                numeric_items.append(0.0)
        
        return numeric_items
    
    def process_item_row(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single row containing delimited item fields into individual item records"""
        items = []
        
        # Extract delimited fields
        descriptions = self.parse_delimited_field(row.get('items_description', ''))
        unit_prices = self.parse_numeric_delimited_field(row.get('items_unit_price', ''))
        quantities = self.parse_numeric_delimited_field(row.get('items_quantity', ''))
        
        # Determine the maximum number of items
        max_items = max(len(descriptions), len(unit_prices), len(quantities))
        
        if max_items == 0:
            return []
        
        # Create individual item records
        for i in range(max_items):
            item = {}
            
            # Copy non-item fields from the original row
            for key, value in row.items():
                if key not in self.item_columns:
                    item[key] = value
            
            # Add parsed item data
            item['ITEM_INDEX'] = i + 1
            item['ITEM_DESCRIPTION'] = descriptions[i] if i < len(descriptions) else ''
            item['ITEM_UNIT_PRICE'] = unit_prices[i] if i < len(unit_prices) else 0.0
            item['ITEM_QUANTITY'] = quantities[i] if i < len(quantities) else 0.0
            
            # Calculate line total
            item['ITEM_LINE_TOTAL'] = item['ITEM_UNIT_PRICE'] * item['ITEM_QUANTITY']
            
            items.append(item)
        
        return items
    
    def expand_results_with_items(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Expand query results to show individual line items"""
        if not results.get('success') or not results.get('data'):
            return results
        
        # Check if any item columns are present
        columns = results.get('columns', [])
        has_item_columns = any(col in self.item_columns for col in columns)
        
        if not has_item_columns:
            return results
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(results['data'], columns=columns)
        expanded_rows = []
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            item_rows = self.process_item_row(row_dict)
            
            if item_rows:
                expanded_rows.extend(item_rows)
            else:
                # Keep original row if no items found
                expanded_rows.append(row_dict)
        
        if not expanded_rows:
            return results
        
        # Create new column list
        new_columns = []
        for col in columns:
            if col not in self.item_columns:
                new_columns.append(col)
        
        # Add new item columns
        new_columns.extend(['ITEM_INDEX', 'ITEM_DESCRIPTION', 'ITEM_UNIT_PRICE', 'ITEM_QUANTITY', 'ITEM_LINE_TOTAL'])
        
        # Convert back to list format
        expanded_data = []
        for row in expanded_rows:
            data_row = []
            for col in new_columns:
                data_row.append(row.get(col, ''))
            expanded_data.append(data_row)
        
        return {
            'success': True,
            'data': expanded_data,
            'columns': new_columns,
            'original_row_count': len(results['data']),
            'expanded_row_count': len(expanded_data),
            'items_expanded': True
        }
    
    def get_item_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistics for item-level data"""
        if not results.get('success') or not results.get('data'):
            return {}
        
        expanded_results = self.expand_results_with_items(results)
        if not expanded_results.get('items_expanded'):
            return {}
        
        df = pd.DataFrame(expanded_results['data'], columns=expanded_results['columns'])
        
        stats = {
            'total_line_items': len(df),
            'unique_invoices': len(df['CASE_ID'].unique()) if 'CASE_ID' in df.columns else 0,
            'total_item_value': df['ITEM_LINE_TOTAL'].sum() if 'ITEM_LINE_TOTAL' in df.columns else 0,
            'average_item_price': df['ITEM_UNIT_PRICE'].mean() if 'ITEM_UNIT_PRICE' in df.columns else 0,
            'average_quantity': df['ITEM_QUANTITY'].mean() if 'ITEM_QUANTITY' in df.columns else 0,
            'most_common_items': []
        }
        
        # Find most common items
        if 'ITEM_DESCRIPTION' in df.columns:
            item_counts = df['ITEM_DESCRIPTION'].value_counts().head(5)
            stats['most_common_items'] = [
                {'item': item, 'count': count} 
                for item, count in item_counts.items()
            ]
        
        return stats
    
    def generate_item_queries(self, user_question: str, vendor_id: str) -> List[str]:
        """Generate SQL queries that are optimized for item-level analysis"""
        item_keywords = [
            'items', 'products', 'services', 'line items', 'individual items',
            'what was billed', 'what did I buy', 'product list', 'service list',
            'item details', 'breakdown', 'line by line'
        ]
        
        question_lower = user_question.lower()
        is_item_query = any(keyword in question_lower for keyword in item_keywords)
        
        if not is_item_query:
            return []
        
        # Generate item-focused queries
        queries = [
            f"SELECT case_id, items_description, items_unit_price, items_quantity FROM AI_INVOICE WHERE vendor_id = '{vendor_id}' AND items_description IS NOT NULL",
            f"SELECT case_id, bill_date, items_description, items_unit_price, items_quantity FROM AI_INVOICE WHERE vendor_id = '{vendor_id}' ORDER BY bill_date DESC LIMIT 10"
        ]
        
        return queries
    
    def is_item_query(self, user_question: str) -> bool:
        """Determine if a user question is asking about individual items/products"""
        item_keywords = [
            'items', 'products', 'services', 'line items', 'individual items',
            'what was billed', 'what did I buy', 'product list', 'service list',
            'item details', 'breakdown', 'line by line', 'itemized', 'what items',
            'what products', 'what services', 'item breakdown', 'product breakdown',
            'service breakdown', 'unit price', 'quantity', 'per item', 'each item',
            'individual cost', 'line item detail', 'item wise', 'product wise'
        ]
        
        question_lower = user_question.lower()
        
        # Check for general item keywords
        has_item_keywords = any(keyword in question_lower for keyword in item_keywords)
        
        # Check for specific product queries
        has_specific_product_query = self.is_specific_product_query(user_question)
        
        return has_item_keywords or has_specific_product_query
    
    def format_item_response(self, results: Dict[str, Any], user_question: str) -> str:
        """Format the response for item-level queries in a user-friendly way"""
        if not results.get('success'):
            return "Unable to retrieve item details."
        
        expanded_results = self.expand_results_with_items(results)
        
        if not expanded_results.get('items_expanded'):
            return "No detailed item information found in the query results."
        
        stats = self.get_item_statistics(results)
        
        response_parts = []
        
        # Add summary statistics
        if stats:
            response_parts.append(f"📊 **Item Summary:**")
            response_parts.append(f"• Total line items: {stats['total_line_items']}")
            if stats['unique_invoices'] > 0:
                response_parts.append(f"• Across {stats['unique_invoices']} invoices")
            if stats['total_item_value'] > 0:
                response_parts.append(f"• Total item value: ${stats['total_item_value']:,.2f}")
            if stats['average_item_price'] > 0:
                response_parts.append(f"• Average item price: ${stats['average_item_price']:.2f}")
            
            # Most common items
            if stats['most_common_items']:
                response_parts.append(f"\n📦 **Most Common Items:**")
                for item_info in stats['most_common_items'][:3]:
                    response_parts.append(f"• {item_info['item']} ({item_info['count']} times)")
        
        # Add note about expanded view
        response_parts.append(f"\n💡 The table below shows individual line items. Each row represents one item from an invoice.")
        
        return '\n'.join(response_parts)
    
    def extract_product_names_from_query(self, user_question: str) -> List[str]:
        """Extract potential product/service names from user questions"""
        import re
        
        # Enhanced patterns for product references
        product_patterns = [
            r'price of ([^?,.!]+)',
            r'cost of ([^?,.!]+)', 
            r'how much.*?(?:is|for|does)\s+([^?,.!]+)',
            r'(\w+(?:\s+\w+)*)\s+(?:cost|price|pricing)',
            r'buy.*?(\w+(?:\s+\w+)*)',
            r'purchased.*?(\w+(?:\s+\w+)*)',
            r'(?:what|show|find).*?([a-zA-Z][a-zA-Z\s]*)\s+(?:item|product|service)',
            r'spend on ([^?,.!]+)',
            r'spent on ([^?,.!]+)',
            r'with ([a-zA-Z][a-zA-Z\s]*) (?:in their|products|services)',
            r'contain ([a-zA-Z][a-zA-Z\s]*) in',
            r'([a-zA-Z][a-zA-Z\s]*) (?:cost|price|pricing)',
        ]
        
        extracted_products = []
        question_lower = user_question.lower()
        
        # First, look for quoted product names (highest priority)
        quoted_pattern = r'["\']([^"\']+)["\']'
        quoted_matches = re.findall(quoted_pattern, user_question)
        extracted_products.extend([match.strip() for match in quoted_matches if len(match.strip()) > 2])
        
        # Then look for pattern-based extraction
        for pattern in product_patterns:
            matches = re.findall(pattern, question_lower, re.IGNORECASE)
            for match in matches:
                # Clean up the extracted product name
                if isinstance(match, tuple):
                    product = ' '.join(match).strip()
                else:
                    product = match.strip()
                
                # Remove common words that aren't product names
                filter_words = ['is', 'the', 'of', 'for', 'did', 'i', 'me', 'my', 'we', 'our', 'much', 'many', 
                               'does', 'do', 'are', 'were', 'was', 'have', 'has', 'had', 'this', 'that', 'these', 'those',
                               'what', 'how', 'when', 'where', 'why', 'who', 'which', 'all', 'any', 'some', 'more',
                               'most', 'many', 'few', 'several', 'show', 'find', 'get', 'give', 'take', 'make',
                               'items', 'with', 'contain', 'their', 'description']
                words = product.split()
                cleaned_words = [w for w in words if w.lower() not in filter_words and len(w) > 2]
                if cleaned_words:
                    cleaned_product = ' '.join(cleaned_words)
                    if len(cleaned_product) > 2:  # Only consider reasonable product names
                        extracted_products.append(cleaned_product)
        
        # Also look for common technology/service terms directly
        tech_terms = [
            'cloud storage', 'cloud', 'storage', 'support', 'license', 'training', 'software', 
            'consulting', 'hosting', 'backup', 'security', 'email', 'database', 'web hosting',
            'mobile app', 'data backup', 'ssl certificate', 'domain', 'server', 'licenses'
        ]
        
        for term in tech_terms:
            if term in question_lower:
                extracted_products.append(term)
        
        # Remove duplicates and filter out very short terms
        unique_products = []
        seen_products = set()
        
        # Sort by length (longest first) to prefer longer, more specific terms
        sorted_products = sorted(extracted_products, key=len, reverse=True)
        
        for product in sorted_products:
            product = product.strip()
            product_lower = product.lower()
            
            # Skip very short terms or already seen terms
            if len(product) < 3 or product_lower in seen_products:
                continue
                
            # Skip if this product is a subset of an already added longer product
            is_subset = False
            for existing in unique_products:
                if product_lower in existing.lower() and len(product) < len(existing):
                    is_subset = True
                    break
            
            if not is_subset:
                unique_products.append(product)
                seen_products.add(product_lower)
                
                # Limit to max 5 products to avoid overly complex queries
                if len(unique_products) >= 5:
                    break
        
        logger.info(f"🔍 Extracted products from '{user_question}': {unique_products}")
        return unique_products
    
    def is_specific_product_query(self, user_question: str) -> bool:
        """Determine if user is asking about a specific product/service"""
        specific_patterns = [
            r'price of',
            r'cost of', 
            r'how much.*?(?:is|for|does)',
            r'(?:cloud|storage|support|license|training|software|consulting|hosting|backup|security).*?(?:cost|price)',
            r'buy.*?(?:cloud|storage|support|license|training|software|consulting)',
            r'purchased.*?(?:cloud|storage|support|license|training|software|consulting)',
            r'what.*?(?:cloud|storage|support|license|training|software|consulting)',
            r'show.*?(?:cloud|storage|support|license|training|software|consulting)',
            r'find.*?(?:cloud|storage|support|license|training|software|consulting)',
            r'(?:item|product|service).*?(?:price|cost)',
            r'how much.*?(?:item|product|service)',
            r'["\'][^"\']+["\']',  # Quoted product names
        ]
        
        question_lower = user_question.lower()
        
        # Check if any specific patterns match
        for pattern in specific_patterns:
            if re.search(pattern, question_lower):
                logger.info(f"🎯 Detected specific product query pattern: {pattern}")
                return True
        
        # Also check if we can extract any product names
        extracted_products = self.extract_product_names_from_query(user_question)
        if extracted_products:
            logger.info(f"🎯 Detected specific product query due to extracted products: {extracted_products}")
            return True
            
        return False
    
    def generate_product_specific_sql(self, user_question: str, vendor_id: str, product_names: List[str]) -> str:
        """Generate SQL that can search for specific products within JSON arrays and CSV data"""
        if not product_names:
            return ""
        
        # Create comprehensive SQL conditions to search within both JSON arrays and CSV data
        like_conditions = []
        for product in product_names:
            # Escape single quotes in product names
            escaped_product = product.replace("'", "''")
            
            # Search for the product name within the items_description field
            # Handle JSONB data by converting to text first
            like_conditions.append(f"LOWER(items_description::text) LIKE LOWER('%{escaped_product}%')")
        
        where_clause = " OR ".join(like_conditions)
        
        # Enhanced SQL with better ordering and more comprehensive selection
        sql_query = f"""
        SELECT 
            case_id, 
            bill_date, 
            amount, 
            balance_amount,
            items_description, 
            items_unit_price, 
            items_quantity,
            status
        FROM AI_INVOICE 
        WHERE vendor_id = '{vendor_id}' 
        AND ({where_clause})
        ORDER BY bill_date DESC, case_id DESC
        LIMIT 100
        """
        
        logger.info(f"🔍 Generated product-specific SQL for products {product_names}: {sql_query}")
        return sql_query.strip()
    
    def format_product_specific_response(self, results: Dict[str, Any], user_question: str, product_names: List[str]) -> str:
        """Format response for specific product queries"""
        if not results.get('success') or not results.get('data'):
            return f"No information found for the requested product(s): {', '.join(product_names)}"
        
        # Expand the results to get individual items
        expanded_results = self.expand_results_with_items(results)
        
        if not expanded_results.get('items_expanded'):
            return "Unable to process item details for your query."
        
        response_parts = []
        expanded_data = expanded_results.get('data', [])
        columns = expanded_results.get('columns', [])
        
        # Filter expanded data to only show relevant products
        relevant_items = []
        for row_data in expanded_data:
            row_dict = dict(zip(columns, row_data))
            item_desc = row_dict.get('ITEM_DESCRIPTION', '').lower()
            
            # Check if this item matches any of the requested products
            for product in product_names:
                if product.lower() in item_desc:
                    relevant_items.append(row_dict)
                    break
        
        if not relevant_items:
            return f"No specific items found matching: {', '.join(product_names)}"
        
        # Group by product for better presentation
        product_summary = {}
        total_value = 0
        total_quantity = 0
        
        for item in relevant_items:
            desc = item.get('ITEM_DESCRIPTION', '')
            price = item.get('ITEM_UNIT_PRICE', 0)
            quantity = item.get('ITEM_QUANTITY', 0)
            line_total = item.get('ITEM_LINE_TOTAL', 0)
            
            if desc not in product_summary:
                product_summary[desc] = {
                    'total_quantity': 0,
                    'total_value': 0,
                    'prices': [],
                    'invoices': []
                }
            
            product_summary[desc]['total_quantity'] += quantity
            product_summary[desc]['total_value'] += line_total
            product_summary[desc]['prices'].append(price)
            product_summary[desc]['invoices'].append(item.get('CASE_ID', ''))
            
            total_value += line_total
            total_quantity += quantity
        
        # Build response
        response_parts.append("🔍 **Product Analysis Results:**")
        response_parts.append(f"Found {len(relevant_items)} line items matching your query")
        response_parts.append(f"Total value: ${total_value:,.2f}")
        response_parts.append(f"Total quantity: {total_quantity:,.0f}")
        
        response_parts.append("\n📦 **Product Details:**")
        for product, details in product_summary.items():
            avg_price = sum(details['prices']) / len(details['prices']) if details['prices'] else 0
            unique_invoices = len(set(details['invoices']))
            
            response_parts.append(f"• **{product}**:")
            response_parts.append(f"  - Total quantity: {details['total_quantity']:,.0f}")
            response_parts.append(f"  - Total value: ${details['total_value']:,.2f}")
            response_parts.append(f"  - Average price: ${avg_price:.2f}")
            response_parts.append(f"  - Appears in {unique_invoices} invoice(s)")
        
        response_parts.append(f"\n💡 The table below shows all matching line items.")
        
        return '\n'.join(response_parts)

# Global instance for easy import
delimited_processor = DelimitedFieldProcessor()
