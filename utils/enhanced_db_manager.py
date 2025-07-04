"""
Enhanced Database Manager for Multi-Item Support
Extends the existing database functionality to work with normalized line item data
"""

import logging
import psycopg2
from typing import Dict, Any, Optional, List
from utils.delimited_field_processor import DelimitedFieldProcessor

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager:
    """Enhanced database manager that supports both original and normalized line item queries"""
    
    def __init__(self, base_db_manager):
        """Initialize with reference to the base database manager"""
        self.base_manager = base_db_manager
        self.processor = DelimitedFieldProcessor()
        self.schema = "public"  # Default schema, can be updated from config
        self._has_line_items_table = None
        
    def check_line_items_table_exists(self) -> bool:
        """Check if the normalized line items table exists"""
        if self._has_line_items_table is not None:
            return self._has_line_items_table
            
        try:
            # Use the correct connection attribute
            connection = getattr(self.base_manager, 'connection', None) or getattr(self.base_manager, 'conn', None)
            if not connection:
                logger.error("❌ No database connection available")
                self._has_line_items_table = False
                return False
                
            cursor = connection.cursor()
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{self.schema}' 
                    AND table_name = 'ai_invoice_line_items'
                );
            """)
            self._has_line_items_table = cursor.fetchone()[0]
            cursor.close()
            logger.info(f"📋 Line items table exists: {self._has_line_items_table}")
            return self._has_line_items_table
        except Exception as e:
            logger.error(f"❌ Error checking line items table: {str(e)}")
            self._has_line_items_table = False
            return False
    
    def execute_line_item_query(self, sql_query: str, user_question: str = "") -> Dict[str, Any]:
        """Execute query with intelligent line item handling"""
        try:
            # Check if this is an item-specific query
            is_item_query = self.processor.is_item_query(user_question)
            is_product_query = self.processor.is_specific_product_query(user_question)
            
            # If we have a normalized table and this is an item query, try to use it
            if (is_item_query or is_product_query) and self.check_line_items_table_exists():
                # Try to convert the query to use the line items table
                converted_query = self.convert_query_to_line_items(sql_query)
                if converted_query:
                    logger.info("🔄 Using normalized line items table for query")
                    result = self.base_manager.execute_vendor_query(converted_query)
                    if result.get('success'):
                        # Mark as already expanded since we're using the normalized table
                        result['items_expanded'] = True
                        result['source'] = 'normalized_table'
                        return result
                    else:
                        logger.warning("⚠️ Line items query failed, falling back to original table")
            
            # Execute the original query
            result = self.base_manager.execute_vendor_query(sql_query)
            
            # Apply intelligent expansion if needed
            if result.get('success'):
                processed_result = self.processor.process_query_results_intelligently(result, user_question)
                processed_result['source'] = 'original_table_expanded' if processed_result.get('items_expanded') else 'original_table'
                return processed_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced query execution failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def convert_query_to_line_items(self, original_query: str) -> Optional[str]:
        """Convert a query from ai_invoice to ai_invoice_line_items table"""
        try:
            query_lower = original_query.lower().strip()
            
            # Only convert SELECT queries
            if not query_lower.startswith('select'):
                return None
            
            # Replace table name
            converted_query = original_query.replace('ai_invoice', 'ai_invoice_line_items')
            converted_query = converted_query.replace('AI_INVOICE', 'ai_invoice_line_items')
            
            # Replace column mappings
            column_mappings = {
                'amount': 'invoice_amount',
                'balance_amount': 'invoice_balance_amount', 
                'paid': 'invoice_paid',
                'total_tax': 'invoice_total_tax',
                'subtotal': 'invoice_subtotal',
                'items_description': 'item_description',
                'items_unit_price': 'item_unit_price',
                'items_quantity': 'item_quantity'
            }
            
            for old_col, new_col in column_mappings.items():
                converted_query = converted_query.replace(old_col, new_col)
                converted_query = converted_query.replace(old_col.upper(), new_col.upper())
            
            # Add line total column if not present and relevant
            if 'item_unit_price' in converted_query.lower() or 'item_quantity' in converted_query.lower():
                if 'item_line_total' not in converted_query.lower():
                    # Try to add item_line_total to SELECT clause
                    select_pos = converted_query.upper().find('SELECT')
                    from_pos = converted_query.upper().find('FROM')
                    if select_pos != -1 and from_pos != -1:
                        select_clause = converted_query[select_pos + 6:from_pos].strip()
                        if not select_clause.startswith('*'):
                            converted_query = (converted_query[:from_pos] + 
                                             ', item_line_total ' + 
                                             converted_query[from_pos:])
            
            logger.debug(f"🔄 Converted query: {converted_query}")
            return converted_query
            
        except Exception as e:
            logger.error(f"❌ Error converting query: {str(e)}")
            return None
    
    def get_line_item_statistics(self, vendor_id: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about line items for a vendor"""
        if not self.check_line_items_table_exists():
            return self.get_legacy_item_statistics(vendor_id, case_id)
        
        try:
            # Use the correct connection attribute
            connection = getattr(self.base_manager, 'connection', None) or getattr(self.base_manager, 'conn', None)
            if not connection:
                logger.error("❌ No database connection available")
                return {}
                
            cursor = connection.cursor()
            
            # Build WHERE clause
            where_conditions = [f"vendor_id = '{vendor_id}'"]
            if case_id:
                where_conditions.append(f"case_id = '{case_id}'")
            where_clause = " AND ".join(where_conditions)
            
            # Get comprehensive statistics
            stats_query = f"""
            SELECT 
                COUNT(*) as total_line_items,
                COUNT(DISTINCT case_id) as unique_invoices,
                SUM(item_line_total) as total_value,
                AVG(item_unit_price) as avg_unit_price,
                AVG(item_quantity) as avg_quantity,
                COUNT(DISTINCT item_description) as unique_products
            FROM {self.schema}.ai_invoice_line_items
            WHERE {where_clause}
            """
            
            cursor.execute(stats_query)
            stats_row = cursor.fetchone()
            
            # Get top products
            top_products_query = f"""
            SELECT item_description, COUNT(*) as frequency, SUM(item_line_total) as total_value
            FROM {self.schema}.ai_invoice_line_items
            WHERE {where_clause} AND item_description IS NOT NULL AND item_description != ''
            GROUP BY item_description
            ORDER BY frequency DESC, total_value DESC
            LIMIT 5
            """
            
            cursor.execute(top_products_query)
            top_products = cursor.fetchall()
            
            cursor.close()
            
            return {
                'total_line_items': stats_row[0] or 0,
                'unique_invoices': stats_row[1] or 0,
                'total_value': float(stats_row[2] or 0),
                'avg_unit_price': float(stats_row[3] or 0),
                'avg_quantity': float(stats_row[4] or 0),
                'unique_products': stats_row[5] or 0,
                'top_products': [
                    {'name': row[0], 'frequency': row[1], 'total_value': float(row[2])}
                    for row in top_products
                ],
                'source': 'normalized_table'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting line item statistics: {str(e)}")
            return self.get_legacy_item_statistics(vendor_id, case_id)
    
    def get_legacy_item_statistics(self, vendor_id: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics using the original table with expansion"""
        try:
            # Build a query to get item data from original table
            where_conditions = [f"vendor_id = '{vendor_id}'"]
            if case_id:
                where_conditions.append(f"case_id = '{case_id}'")
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            SELECT case_id, items_description, items_unit_price, items_quantity
            FROM {self.schema}.ai_invoice 
            WHERE {where_clause}
            AND (items_description IS NOT NULL OR items_unit_price IS NOT NULL OR items_quantity IS NOT NULL)
            """
            
            result = self.base_manager.execute_vendor_query(query)
            if result.get('success'):
                expanded_result = self.processor.expand_results_with_items(result)
                if expanded_result.get('items_expanded'):
                    stats = self.processor.get_item_statistics(expanded_result)
                    stats['source'] = 'original_table_expanded'
                    return stats
            
            return {'source': 'unavailable', 'error': 'No item data available'}
            
        except Exception as e:
            logger.error(f"❌ Error getting legacy statistics: {str(e)}")
            return {'source': 'error', 'error': str(e)}
    
    def search_products(self, vendor_id: str, product_names: List[str], limit: int = 100) -> Dict[str, Any]:
        """Search for specific products in the database"""
        if not product_names:
            return {'success': False, 'error': 'No product names provided'}
        
        if self.check_line_items_table_exists():
            return self.search_products_normalized(vendor_id, product_names, limit)
        else:
            return self.search_products_legacy(vendor_id, product_names, limit)
    
    def search_products_normalized(self, vendor_id: str, product_names: List[str], limit: int) -> Dict[str, Any]:
        """Search products in the normalized line items table"""
        try:
            # Build LIKE conditions for product search
            like_conditions = []
            for product in product_names:
                escaped_product = product.replace("'", "''")
                like_conditions.append(f"LOWER(item_description) LIKE LOWER('%{escaped_product}%')")
            
            where_clause = " OR ".join(like_conditions)
            
            query = f"""
            SELECT 
                case_id, bill_date, invoice_amount, invoice_balance_amount,
                item_description, item_unit_price, item_quantity, item_line_total,
                status
            FROM {self.schema}.ai_invoice_line_items
            WHERE vendor_id = '{vendor_id}' 
            AND ({where_clause})
            ORDER BY bill_date DESC, case_id DESC
            LIMIT {limit}
            """
            
            result = self.base_manager.execute_vendor_query(query)
            if result.get('success'):
                result['items_expanded'] = True
                result['source'] = 'normalized_table'
                result['search_terms'] = product_names
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error searching products in normalized table: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_products_legacy(self, vendor_id: str, product_names: List[str], limit: int) -> Dict[str, Any]:
        """Search products using the original table with expansion"""
        try:
            # Use the existing product-specific SQL generator
            sql_query = self.processor.generate_product_specific_sql("", vendor_id, product_names)
            if not sql_query:
                return {'success': False, 'error': 'Could not generate search query'}
            
            # Add limit if not present
            if 'limit' not in sql_query.lower():
                sql_query += f" LIMIT {limit}"
            
            result = self.base_manager.execute_vendor_query(sql_query)
            if result.get('success'):
                # Expand the results
                expanded_result = self.processor.expand_results_with_items(result)
                expanded_result['source'] = 'original_table_expanded'
                expanded_result['search_terms'] = product_names
                return expanded_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error searching products in legacy table: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_item_details_for_invoice(self, vendor_id: str, case_id: str) -> Dict[str, Any]:
        """Get detailed line items for a specific invoice"""
        if self.check_line_items_table_exists():
            try:
                query = f"""
                SELECT 
                    item_index, item_description, item_unit_price, 
                    item_quantity, item_line_total
                FROM {self.schema}.ai_invoice_line_items
                WHERE vendor_id = '{vendor_id}' AND case_id = '{case_id}'
                ORDER BY item_index
                """
                
                result = self.base_manager.execute_vendor_query(query)
                if result.get('success'):
                    result['items_expanded'] = True
                    result['source'] = 'normalized_table'
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Error getting invoice line items: {str(e)}")
        
        # Fallback to legacy method
        try:
            query = f"""
            SELECT case_id, items_description, items_unit_price, items_quantity
            FROM {self.schema}.ai_invoice
            WHERE vendor_id = '{vendor_id}' AND case_id = '{case_id}'
            """
            
            result = self.base_manager.execute_vendor_query(query)
            if result.get('success'):
                expanded_result = self.processor.expand_results_with_items(result)
                expanded_result['source'] = 'original_table_expanded'
                return expanded_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting legacy invoice items: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def execute_item_aware_query(self, sql_query: str, user_question: str = "") -> Dict[str, Any]:
        """Execute query with enhanced item-level awareness and intelligent processing"""
        try:
            # Get comprehensive analysis from the delimited processor
            query_analysis = self.processor.enhance_llm_understanding_for_items(user_question)
            
            logger.info(f"🎯 Query analysis: {query_analysis['query_intent']} - Item Query: {query_analysis['is_item_query']}")
            
            # Check if we should use normalized table for item queries
            if (query_analysis['is_item_query'] or query_analysis['is_product_query']) and self.check_line_items_table_exists():
                converted_query = self.convert_query_to_line_items(sql_query)
                if converted_query:
                    logger.info("🔄 Using normalized line items table for enhanced query")
                    result = self.base_manager.execute_vendor_query(converted_query)
                    if result.get('success'):
                        result['items_expanded'] = True
                        result['source'] = 'normalized_table'
                        result['query_analysis'] = query_analysis
                        return result
            
            # Execute original query
            result = self.base_manager.execute_vendor_query(sql_query)
            
            # Apply intelligent processing based on query analysis
            if result.get('success'):
                # For item queries, ensure we get the best possible expansion
                if query_analysis['is_item_query'] or query_analysis['is_product_query']:
                    processed_result = self.processor.expand_results_with_items(result)
                    processed_result['source'] = 'original_table_expanded'
                    processed_result['query_analysis'] = query_analysis
                    
                    # Add enhanced metadata for specific query types
                    if query_analysis['query_intent'] == 'price_analysis':
                        processed_result['supports_price_analysis'] = True
                    elif query_analysis['query_intent'] == 'quantity_inquiry':
                        processed_result['supports_quantity_analysis'] = True
                    
                    return processed_result
                else:
                    # For non-item queries, still check if expansion would be beneficial
                    processed_result = self.processor.process_query_results_intelligently(result, user_question)
                    processed_result['source'] = 'original_table_smart'
                    processed_result['query_analysis'] = query_analysis
                    return processed_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Item-aware query execution failed: {str(e)}")
            return {'success': False, 'error': str(e), 'query_analysis': {}}
    
    def execute_item_aware_query_with_analysis(self, sql_query: str, user_question: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query with pre-computed analysis to avoid redundant method calls"""
        try:
            logger.info(f"🎯 Using cached query analysis: {query_analysis['query_intent']} - Item Query: {query_analysis['is_item_query']}")
            
            # Check if we should use normalized table for item queries
            if (query_analysis['is_item_query'] or query_analysis['is_product_query']) and self.check_line_items_table_exists():
                converted_query = self.convert_query_to_line_items(sql_query)
                if converted_query:
                    logger.info("🔄 Using normalized line items table for enhanced query")
                    result = self.base_manager.execute_vendor_query(converted_query)
                    if result.get('success'):
                        result['items_expanded'] = True
                        result['source'] = 'normalized_table'
                        result['query_analysis'] = query_analysis
                        return result
            
            # Execute original query
            result = self.base_manager.execute_vendor_query(sql_query)
            
            # Apply intelligent processing based on cached query analysis
            if result.get('success'):
                # For item queries, ensure we get the best possible expansion
                if query_analysis['is_item_query'] or query_analysis['is_product_query']:
                    processed_result = self.processor.expand_results_with_items(result)
                    processed_result['source'] = 'original_table_expanded'
                    processed_result['query_analysis'] = query_analysis
                    
                    # Add enhanced metadata for specific query types
                    if query_analysis['query_intent'] == 'price_analysis':
                        processed_result['supports_price_analysis'] = True
                    elif query_analysis['query_intent'] == 'quantity_inquiry':
                        processed_result['supports_quantity_analysis'] = True
                    
                    return processed_result
                else:
                    # For non-item queries, still check if expansion would be beneficial
                    processed_result = self.processor.process_query_results_intelligently(result, user_question)
                    processed_result['source'] = 'original_table_smart'
                    processed_result['query_analysis'] = query_analysis
                    return processed_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Item-aware query execution failed: {str(e)}")
            return {'success': False, 'error': str(e), 'query_analysis': query_analysis}
    
    def get_item_insights_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights summary for item-level results"""
        if not results.get('success') or not results.get('items_expanded'):
            return {}
        
        try:
            # Get basic statistics
            stats = self.processor.get_item_statistics(results)
            
            # Add query-specific insights
            query_analysis = results.get('query_analysis', {})
            insights = {
                'basic_stats': stats,
                'query_intent': query_analysis.get('query_intent', 'unknown'),
                'total_unique_products': 0,
                'price_range': {'min': 0, 'max': 0, 'avg': 0},
                'quantity_insights': {},
                'recommendations': []
            }
            
            # Analyze expanded data for deeper insights
            if results.get('data') and results.get('columns'):
                import pandas as pd
                df = pd.DataFrame(results['data'], columns=results['columns'])
                
                # Product variety analysis
                if 'ITEM_DESCRIPTION' in df.columns:
                    unique_products = df['ITEM_DESCRIPTION'].nunique()
                    insights['total_unique_products'] = unique_products
                    
                    # Get most and least common products
                    product_counts = df['ITEM_DESCRIPTION'].value_counts()
                    insights['most_common_product'] = product_counts.index[0] if len(product_counts) > 0 else None
                    insights['least_common_product'] = product_counts.index[-1] if len(product_counts) > 0 else None
                
                # Price analysis
                if 'ITEM_UNIT_PRICE' in df.columns:
                    prices = df['ITEM_UNIT_PRICE'].dropna()
                    if len(prices) > 0:
                        insights['price_range'] = {
                            'min': float(prices.min()),
                            'max': float(prices.max()),
                            'avg': float(prices.mean())
                        }
                        
                        # Find most and least expensive items
                        max_price_item = df.loc[df['ITEM_UNIT_PRICE'].idxmax(), 'ITEM_DESCRIPTION'] if not prices.empty else None
                        min_price_item = df.loc[df['ITEM_UNIT_PRICE'].idxmin(), 'ITEM_DESCRIPTION'] if not prices.empty else None
                        insights['most_expensive_item'] = max_price_item
                        insights['least_expensive_item'] = min_price_item
                
                # Quantity insights
                if 'ITEM_QUANTITY' in df.columns:
                    quantities = df['ITEM_QUANTITY'].dropna()
                    if len(quantities) > 0:
                        insights['quantity_insights'] = {
                            'total_items_ordered': float(quantities.sum()),
                            'avg_quantity_per_line': float(quantities.mean()),
                            'max_quantity_ordered': float(quantities.max())
                        }
                
                # Generate recommendations based on query intent
                intent = query_analysis.get('query_intent', '')
                if intent == 'price_analysis':
                    insights['recommendations'].append("Consider price optimization for high-cost items")
                elif intent == 'quantity_inquiry':
                    insights['recommendations'].append("Review quantity patterns for bulk purchasing opportunities")
                elif intent == 'product_listing':
                    insights['recommendations'].append("Analyze product diversity for vendor relationship optimization")
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error generating item insights: {str(e)}")
            return {'error': str(e)}
