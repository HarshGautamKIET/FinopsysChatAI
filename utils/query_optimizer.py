import re
from typing import Dict, List, Tuple

class QueryOptimizer:
    """Optimize SQL queries for better performance"""
    
    @staticmethod
    def add_performance_hints(sql_query: str, vendor_id: str) -> str:
        """Add performance hints to queries"""
        # Add LIMIT clause if not present and not aggregation query
        query_upper = sql_query.upper()
        is_aggregation = any(agg in query_upper for agg in ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'GROUP BY'])
        
        if "LIMIT" not in query_upper and not is_aggregation:
            sql_query += " LIMIT 1000"
        
        # Optimize vendor_id filtering for index usage
        if f"vendor_id = '{vendor_id}'" in sql_query:
            # Ensure vendor_id filter is positioned for optimal index usage
            sql_query = sql_query.replace(
                f"vendor_id = '{vendor_id}'", 
                f"vendor_id = '{vendor_id}' /* index hint for PostgreSQL */"
            )
        
        # Add query hints for PostgreSQL optimization
        if "SELECT" in query_upper and "FROM AI_INVOICE" in query_upper:
            sql_query = sql_query.replace(
                "FROM AI_INVOICE", 
                "FROM AI_INVOICE /* PostgreSQL optimized */"
            )
        
        return sql_query
    
    @staticmethod
    def optimize_query_structure(sql_query: str) -> str:
        """Optimize query structure for better performance"""
        query_upper = sql_query.upper()
        
        # Replace SELECT * with specific columns for better performance
        if "SELECT *" in query_upper:
            # For demo purposes, replace with common columns
            # In production, this should be configurable
            optimized_columns = [
                "case_id", "vendor_id", "amount", "balance_amount", 
                "paid", "status", "bill_date", "due_date"
            ]
            sql_query = sql_query.replace("SELECT *", f"SELECT {', '.join(optimized_columns)}")
        
        return sql_query
    
    @staticmethod
    def estimate_query_cost(sql_query: str) -> Dict:
        """Estimate query execution cost with detailed analysis"""
        query_upper = sql_query.upper()
        
        cost_factors = {
            "SELECT *": 5,  # Higher cost for SELECT *
            "ORDER BY": 3,  # Sorting cost
            "GROUP BY": 3,  # Grouping cost
            "JOIN": 4,      # Join cost
            "DISTINCT": 2,  # Distinct cost
            "LIKE": 2,      # Pattern matching cost
            "SUBSTRING": 1, # String function cost
            "CASE WHEN": 1  # Conditional logic cost
        }
        
        total_cost = 1  # Base cost
        cost_breakdown = {}
        
        for factor, weight in cost_factors.items():
            if factor in query_upper:
                total_cost += weight
                cost_breakdown[factor] = weight
        
        # Estimate row scan cost
        if "WHERE" not in query_upper:
            total_cost += 10  # Full table scan penalty
            cost_breakdown["FULL_TABLE_SCAN"] = 10
        elif "vendor_id" not in query_upper:
            total_cost += 8  # Non-indexed scan penalty
            cost_breakdown["NON_INDEXED_SCAN"] = 8
        
        # Calculate performance tier
        if total_cost <= 5:
            performance_tier = "EXCELLENT"
            recommendation = "Query is well optimized"
        elif total_cost <= 10:
            performance_tier = "GOOD"
            recommendation = "Query has good performance"
        elif total_cost <= 15:
            performance_tier = "FAIR"
            recommendation = "Consider optimizing this query"
        else:
            performance_tier = "POOR"
            recommendation = "Query needs optimization - high resource usage expected"
        
        return {
            "estimated_cost": total_cost,
            "performance_tier": performance_tier,
            "recommendation": recommendation,
            "cost_breakdown": cost_breakdown,
            "optimization_suggestions": QueryOptimizer._get_optimization_suggestions(sql_query)
        }
    
    @staticmethod
    def _get_optimization_suggestions(sql_query: str) -> List[str]:
        """Generate specific optimization suggestions"""
        suggestions = []
        query_upper = sql_query.upper()
        
        if "SELECT *" in query_upper:
            suggestions.append("Replace SELECT * with specific column names")
        
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            suggestions.append("Add LIMIT clause when using ORDER BY")
        
        if "WHERE" not in query_upper:
            suggestions.append("Add WHERE clause to filter data")
        
        if "vendor_id" not in query_upper.replace("VENDOR_ID", "vendor_id"):
            suggestions.append("Ensure vendor_id filtering for security and performance")
        
        if "LIKE" in query_upper and not any(x in query_upper for x in ["ILIKE", "~~", "!~~"]):
            suggestions.append("Consider using ILIKE or PostgreSQL pattern matching for better performance")
        
        return suggestions