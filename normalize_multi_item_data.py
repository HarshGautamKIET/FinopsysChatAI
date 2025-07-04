#!/usr/bin/env python3
"""
Multi-Item Data Normalization Script for FinOpsysAI
This script separates multi-item records into individual line item rows
"""

import os
import sys
import psycopg2
import json
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, project_root)

from config import Config
from utils.delimited_field_processor import DelimitedFieldProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
config = Config()
POSTGRES_CONFIG = {
    'host': config.POSTGRES_HOST,
    'port': config.POSTGRES_PORT,
    'user': config.POSTGRES_USER,
    'password': config.POSTGRES_PASSWORD,
    'database': config.POSTGRES_DATABASE,
    'options': f'-c search_path={config.POSTGRES_SCHEMA}'
}

class MultiItemNormalizer:
    """Handles normalization of multi-item invoice data into separate line item rows"""
    
    def __init__(self):
        """Initialize the normalizer with database connection and processor"""
        self.processor = DelimitedFieldProcessor()
        self.conn = None
        self.schema = config.POSTGRES_SCHEMA
        
    def connect_to_database(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**POSTGRES_CONFIG)
            logger.info("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            return False
    
    def create_line_items_table(self):
        """Create a new table for individual line items"""
        try:
            cursor = self.conn.cursor()
            
            # Create the line items table with individual item data
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.schema}.ai_invoice_line_items (
                line_item_id SERIAL PRIMARY KEY,
                case_id TEXT NOT NULL,
                bill_id TEXT,
                customer_id TEXT,
                vendor_id TEXT NOT NULL,
                due_date DATE,
                bill_date DATE,
                decline_date DATE,
                receiving_date DATE,
                approveddate1 DATE,
                approveddate2 DATE,
                invoice_amount NUMERIC(18,2),
                invoice_balance_amount NUMERIC(18,2),
                invoice_paid NUMERIC(18,2),
                invoice_total_tax NUMERIC(18,2),
                invoice_subtotal NUMERIC(18,2),
                item_index INTEGER NOT NULL,
                item_description TEXT,
                item_unit_price NUMERIC(18,2),
                item_quantity NUMERIC(18,2),
                item_line_total NUMERIC(18,2),
                status TEXT,
                decline_reason TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES {self.schema}.ai_invoice(case_id)
            );
            """
            
            logger.info(f"🔨 Creating line items table in schema '{self.schema}'...")
            cursor.execute(create_table_sql)
            
            # Create indexes for better performance
            indexes_sql = [
                f"CREATE INDEX IF NOT EXISTS idx_line_items_vendor_id ON {self.schema}.ai_invoice_line_items(vendor_id);",
                f"CREATE INDEX IF NOT EXISTS idx_line_items_case_id ON {self.schema}.ai_invoice_line_items(case_id);",
                f"CREATE INDEX IF NOT EXISTS idx_line_items_item_desc ON {self.schema}.ai_invoice_line_items(item_description);",
                f"CREATE INDEX IF NOT EXISTS idx_line_items_bill_date ON {self.schema}.ai_invoice_line_items(bill_date);",
                f"CREATE INDEX IF NOT EXISTS idx_line_items_status ON {self.schema}.ai_invoice_line_items(status);"
            ]
            
            logger.info("🔨 Creating performance indexes...")
            for index_sql in indexes_sql:
                cursor.execute(index_sql)
            
            self.conn.commit()
            cursor.close()
            
            logger.info("✅ Line items table and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating line items table: {str(e)}")
            self.conn.rollback()
            return False
    
    def parse_jsonb_field(self, jsonb_value: str) -> List[str]:
        """Parse JSONB field into list of strings"""
        if not jsonb_value:
            return []
        
        try:
            if isinstance(jsonb_value, str):
                data = json.loads(jsonb_value)
            else:
                data = jsonb_value
            
            if isinstance(data, list):
                return [str(item).strip() for item in data if item is not None]
            else:
                return [str(data).strip()]
        except (json.JSONDecodeError, TypeError):
            # Fallback to delimiter-based parsing
            return self.processor.parse_delimited_field(str(jsonb_value))
    
    def parse_numeric_jsonb_field(self, jsonb_value: str) -> List[float]:
        """Parse JSONB field into list of numeric values"""
        if not jsonb_value:
            return []
        
        try:
            if isinstance(jsonb_value, str):
                data = json.loads(jsonb_value)
            else:
                data = jsonb_value
            
            if isinstance(data, list):
                numeric_items = []
                for item in data:
                    try:
                        numeric_items.append(float(item))
                    except (ValueError, TypeError):
                        numeric_items.append(0.0)
                return numeric_items
            else:
                try:
                    return [float(data)]
                except (ValueError, TypeError):
                    return [0.0]
        except (json.JSONDecodeError, TypeError):
            # Fallback to delimiter-based parsing
            return self.processor.parse_numeric_delimited_field(str(jsonb_value))
    
    def normalize_invoice_to_line_items(self, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert a single invoice with multiple items into individual line item records"""
        line_items = []
        
        # Parse the multi-item fields
        descriptions = self.parse_jsonb_field(invoice_data.get('items_description', ''))
        unit_prices = self.parse_numeric_jsonb_field(invoice_data.get('items_unit_price', ''))
        quantities = self.parse_numeric_jsonb_field(invoice_data.get('items_quantity', ''))
        
        # Determine the maximum number of items
        max_items = max(len(descriptions), len(unit_prices), len(quantities))
        
        if max_items == 0:
            # Create a single line item with empty item data
            line_item = self.create_line_item_from_invoice(invoice_data, 1, '', 0.0, 0.0)
            line_items.append(line_item)
        else:
            # Create individual line items
            for i in range(max_items):
                description = descriptions[i] if i < len(descriptions) else ''
                unit_price = unit_prices[i] if i < len(unit_prices) else 0.0
                quantity = quantities[i] if i < len(quantities) else 0.0
                
                line_item = self.create_line_item_from_invoice(
                    invoice_data, i + 1, description, unit_price, quantity
                )
                line_items.append(line_item)
        
        return line_items
    
    def create_line_item_from_invoice(self, invoice_data: Dict[str, Any], item_index: int, 
                                    description: str, unit_price: float, quantity: float) -> Dict[str, Any]:
        """Create a line item record from invoice data"""
        line_total = unit_price * quantity
        
        return {
            'case_id': invoice_data.get('case_id'),
            'bill_id': invoice_data.get('bill_id'),
            'customer_id': invoice_data.get('customer_id'),
            'vendor_id': invoice_data.get('vendor_id'),
            'due_date': invoice_data.get('due_date'),
            'bill_date': invoice_data.get('bill_date'),
            'decline_date': invoice_data.get('decline_date'),
            'receiving_date': invoice_data.get('receiving_date'),
            'approveddate1': invoice_data.get('approveddate1'),
            'approveddate2': invoice_data.get('approveddate2'),
            'invoice_amount': invoice_data.get('amount'),
            'invoice_balance_amount': invoice_data.get('balance_amount'),
            'invoice_paid': invoice_data.get('paid'),
            'invoice_total_tax': invoice_data.get('total_tax'),
            'invoice_subtotal': invoice_data.get('subtotal'),
            'item_index': item_index,
            'item_description': description,
            'item_unit_price': unit_price,
            'item_quantity': quantity,
            'item_line_total': line_total,
            'status': invoice_data.get('status'),
            'decline_reason': invoice_data.get('decline_reason'),
            'department': invoice_data.get('department')
        }
    
    def get_all_invoices(self) -> List[Dict[str, Any]]:
        """Retrieve all invoices from the database"""
        try:
            cursor = self.conn.cursor()
            
            # Get all invoices with their item data
            select_sql = f"""
            SELECT 
                case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
                decline_date, receiving_date, approveddate1, approveddate2,
                amount, balance_amount, paid, total_tax, subtotal,
                items_description, items_unit_price, items_quantity,
                status, decline_reason, department
            FROM {self.schema}.ai_invoice
            ORDER BY case_id
            """
            
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [desc[0] for desc in cursor.description]
            invoices = []
            
            for row in rows:
                invoice_dict = dict(zip(column_names, row))
                invoices.append(invoice_dict)
            
            cursor.close()
            logger.info(f"✅ Retrieved {len(invoices)} invoices from database")
            return invoices
            
        except Exception as e:
            logger.error(f"❌ Error retrieving invoices: {str(e)}")
            return []
    
    def insert_line_items(self, line_items: List[Dict[str, Any]]) -> bool:
        """Insert line items into the line items table"""
        try:
            cursor = self.conn.cursor()
            
            # Clear existing line items first
            cursor.execute(f"DELETE FROM {self.schema}.ai_invoice_line_items")
            logger.info("🧹 Cleared existing line items")
            
            # Insert new line items
            insert_sql = f"""
            INSERT INTO {self.schema}.ai_invoice_line_items (
                case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
                decline_date, receiving_date, approveddate1, approveddate2,
                invoice_amount, invoice_balance_amount, invoice_paid, 
                invoice_total_tax, invoice_subtotal,
                item_index, item_description, item_unit_price, 
                item_quantity, item_line_total,
                status, decline_reason, department
            ) VALUES (
                %(case_id)s, %(bill_id)s, %(customer_id)s, %(vendor_id)s, 
                %(due_date)s, %(bill_date)s, %(decline_date)s, %(receiving_date)s,
                %(approveddate1)s, %(approveddate2)s, %(invoice_amount)s, 
                %(invoice_balance_amount)s, %(invoice_paid)s, %(invoice_total_tax)s,
                %(invoice_subtotal)s, %(item_index)s, %(item_description)s,
                %(item_unit_price)s, %(item_quantity)s, %(item_line_total)s,
                %(status)s, %(decline_reason)s, %(department)s
            )
            """
            
            cursor.executemany(insert_sql, line_items)
            self.conn.commit()
            cursor.close()
            
            logger.info(f"✅ Inserted {len(line_items)} line items successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inserting line items: {str(e)}")
            self.conn.rollback()
            return False
    
    def create_triggers_and_functions(self):
        """Create database triggers to automatically maintain line items when invoices are modified"""
        try:
            cursor = self.conn.cursor()
            
            # Create function to normalize a single invoice into line items
            function_sql = f"""
            CREATE OR REPLACE FUNCTION {self.schema}.normalize_invoice_items()
            RETURNS TRIGGER AS $$
            DECLARE
                item_descriptions TEXT[];
                item_prices NUMERIC[];
                item_quantities NUMERIC[];
                max_items INTEGER;
                i INTEGER;
                description TEXT;
                unit_price NUMERIC;
                quantity NUMERIC;
                line_total NUMERIC;
            BEGIN
                -- Delete existing line items for this invoice
                DELETE FROM {self.schema}.ai_invoice_line_items WHERE case_id = NEW.case_id;
                
                -- Parse JSON arrays or handle NULL values
                item_descriptions := CASE 
                    WHEN NEW.items_description IS NOT NULL THEN 
                        ARRAY(SELECT json_array_elements_text(NEW.items_description))
                    ELSE ARRAY[]::TEXT[]
                END;
                
                item_prices := CASE 
                    WHEN NEW.items_unit_price IS NOT NULL THEN 
                        ARRAY(SELECT (json_array_elements(NEW.items_unit_price))::TEXT::NUMERIC)
                    ELSE ARRAY[]::NUMERIC[]
                END;
                
                item_quantities := CASE 
                    WHEN NEW.items_quantity IS NOT NULL THEN 
                        ARRAY(SELECT (json_array_elements(NEW.items_quantity))::TEXT::NUMERIC)
                    ELSE ARRAY[]::NUMERIC[]
                END;
                
                -- Determine maximum number of items
                max_items := GREATEST(
                    array_length(item_descriptions, 1),
                    array_length(item_prices, 1),
                    array_length(item_quantities, 1)
                );
                
                -- If no items found, create one empty line item
                IF max_items IS NULL OR max_items = 0 THEN
                    INSERT INTO {self.schema}.ai_invoice_line_items (
                        case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
                        decline_date, receiving_date, approveddate1, approveddate2,
                        invoice_amount, invoice_balance_amount, invoice_paid,
                        invoice_total_tax, invoice_subtotal,
                        item_index, item_description, item_unit_price,
                        item_quantity, item_line_total,
                        status, decline_reason, department
                    ) VALUES (
                        NEW.case_id, NEW.bill_id, NEW.customer_id, NEW.vendor_id,
                        NEW.due_date, NEW.bill_date, NEW.decline_date, NEW.receiving_date,
                        NEW.approveddate1, NEW.approveddate2, NEW.amount,
                        NEW.balance_amount, NEW.paid, NEW.total_tax, NEW.subtotal,
                        1, '', 0.0, 0.0, 0.0,
                        NEW.status, NEW.decline_reason, NEW.department
                    );
                ELSE
                    -- Create individual line items
                    FOR i IN 1..max_items LOOP
                        description := COALESCE(item_descriptions[i], '');
                        unit_price := COALESCE(item_prices[i], 0.0);
                        quantity := COALESCE(item_quantities[i], 0.0);
                        line_total := unit_price * quantity;
                        
                        INSERT INTO {self.schema}.ai_invoice_line_items (
                            case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
                            decline_date, receiving_date, approveddate1, approveddate2,
                            invoice_amount, invoice_balance_amount, invoice_paid,
                            invoice_total_tax, invoice_subtotal,
                            item_index, item_description, item_unit_price,
                            item_quantity, item_line_total,
                            status, decline_reason, department
                        ) VALUES (
                            NEW.case_id, NEW.bill_id, NEW.customer_id, NEW.vendor_id,
                            NEW.due_date, NEW.bill_date, NEW.decline_date, NEW.receiving_date,
                            NEW.approveddate1, NEW.approveddate2, NEW.amount,
                            NEW.balance_amount, NEW.paid, NEW.total_tax, NEW.subtotal,
                            i, description, unit_price, quantity, line_total,
                            NEW.status, NEW.decline_reason, NEW.department
                        );
                    END LOOP;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            cursor.execute(function_sql)
            
            # Create triggers for INSERT and UPDATE
            trigger_sql = f"""
            DROP TRIGGER IF EXISTS trg_normalize_invoice_items_insert ON {self.schema}.ai_invoice;
            DROP TRIGGER IF EXISTS trg_normalize_invoice_items_update ON {self.schema}.ai_invoice;
            
            CREATE TRIGGER trg_normalize_invoice_items_insert
                AFTER INSERT ON {self.schema}.ai_invoice
                FOR EACH ROW EXECUTE FUNCTION {self.schema}.normalize_invoice_items();
                
            CREATE TRIGGER trg_normalize_invoice_items_update
                AFTER UPDATE ON {self.schema}.ai_invoice
                FOR EACH ROW EXECUTE FUNCTION {self.schema}.normalize_invoice_items();
            """
            
            cursor.execute(trigger_sql)
            
            # Create trigger for DELETE to clean up line items
            delete_trigger_sql = f"""
            CREATE OR REPLACE FUNCTION {self.schema}.cleanup_invoice_line_items()
            RETURNS TRIGGER AS $$
            BEGIN
                DELETE FROM {self.schema}.ai_invoice_line_items WHERE case_id = OLD.case_id;
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS trg_cleanup_invoice_line_items ON {self.schema}.ai_invoice;
            
            CREATE TRIGGER trg_cleanup_invoice_line_items
                BEFORE DELETE ON {self.schema}.ai_invoice
                FOR EACH ROW EXECUTE FUNCTION {self.schema}.cleanup_invoice_line_items();
            """
            
            cursor.execute(delete_trigger_sql)
            
            self.conn.commit()
            cursor.close()
            
            logger.info("✅ Created triggers and functions for automatic line item normalization")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating triggers: {str(e)}")
            self.conn.rollback()
            return False
    
    def normalize_all_existing_data(self) -> bool:
        """Normalize all existing invoice data into line items"""
        try:
            logger.info("🔄 Starting normalization of existing invoice data...")
            
            # Get all invoices
            invoices = self.get_all_invoices()
            if not invoices:
                logger.warning("⚠️ No invoices found to normalize")
                return True
            
            # Process each invoice into line items
            all_line_items = []
            total_items = 0
            
            for invoice in invoices:
                line_items = self.normalize_invoice_to_line_items(invoice)
                all_line_items.extend(line_items)
                total_items += len(line_items)
                
                if len(line_items) > 1:
                    logger.debug(f"Expanded invoice {invoice['case_id']} into {len(line_items)} line items")
            
            # Insert all line items
            success = self.insert_line_items(all_line_items)
            if success:
                logger.info(f"✅ Successfully normalized {len(invoices)} invoices into {total_items} line items")
                return True
            else:
                logger.error("❌ Failed to insert line items")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during normalization: {str(e)}")
            return False
    
    def create_views_for_compatibility(self):
        """Create database views to maintain compatibility with existing queries"""
        try:
            cursor = self.conn.cursor()
            
            # Create a view that shows expanded line items in the same format as the original table
            view_sql = f"""
            CREATE OR REPLACE VIEW {self.schema}.ai_invoice_expanded AS
            SELECT 
                case_id,
                bill_id,
                customer_id,
                vendor_id,
                due_date,
                bill_date,
                decline_date,
                receiving_date,
                approveddate1,
                approveddate2,
                invoice_amount as amount,
                invoice_balance_amount as balance_amount,
                invoice_paid as paid,
                invoice_total_tax as total_tax,
                invoice_subtotal as subtotal,
                item_index,
                item_description,
                item_unit_price,
                item_quantity,
                item_line_total,
                status,
                decline_reason,
                department,
                created_at,
                updated_at
            FROM {self.schema}.ai_invoice_line_items
            ORDER BY case_id, item_index;
            """
            
            cursor.execute(view_sql)
            
            # Create an aggregated view that shows invoice summaries
            summary_view_sql = f"""
            CREATE OR REPLACE VIEW {self.schema}.ai_invoice_summary AS
            SELECT 
                case_id,
                bill_id,
                customer_id,
                vendor_id,
                due_date,
                bill_date,
                decline_date,
                receiving_date,
                approveddate1,
                approveddate2,
                invoice_amount as amount,
                invoice_balance_amount as balance_amount,
                invoice_paid as paid,
                invoice_total_tax as total_tax,
                invoice_subtotal as subtotal,
                COUNT(*) as total_line_items,
                SUM(item_line_total) as calculated_total,
                STRING_AGG(item_description, ', ' ORDER BY item_index) as items_summary,
                status,
                decline_reason,
                department,
                MAX(created_at) as created_at,
                MAX(updated_at) as updated_at
            FROM {self.schema}.ai_invoice_line_items
            GROUP BY 
                case_id, bill_id, customer_id, vendor_id, due_date, bill_date,
                decline_date, receiving_date, approveddate1, approveddate2,
                invoice_amount, invoice_balance_amount, invoice_paid,
                invoice_total_tax, invoice_subtotal, status, decline_reason, department
            ORDER BY case_id;
            """
            
            cursor.execute(summary_view_sql)
            
            self.conn.commit()
            cursor.close()
            
            logger.info("✅ Created database views for compatibility")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating views: {str(e)}")
            self.conn.rollback()
            return False
    
    def validate_normalization(self) -> bool:
        """Validate that the normalization was successful"""
        try:
            cursor = self.conn.cursor()
            
            # Count original invoices
            cursor.execute(f"SELECT COUNT(*) FROM {self.schema}.ai_invoice")
            original_count = cursor.fetchone()[0]
            
            # Count line items
            cursor.execute(f"SELECT COUNT(*) FROM {self.schema}.ai_invoice_line_items")
            line_items_count = cursor.fetchone()[0]
            
            # Count unique invoices in line items
            cursor.execute(f"SELECT COUNT(DISTINCT case_id) FROM {self.schema}.ai_invoice_line_items")
            unique_invoices_count = cursor.fetchone()[0]
            
            # Check for any inconsistencies
            cursor.execute(f"""
                SELECT COUNT(*) FROM {self.schema}.ai_invoice i
                LEFT JOIN {self.schema}.ai_invoice_line_items li ON i.case_id = li.case_id
                WHERE li.case_id IS NULL
            """)
            missing_line_items = cursor.fetchone()[0]
            
            cursor.close()
            
            logger.info(f"📊 Validation Results:")
            logger.info(f"   Original invoices: {original_count}")
            logger.info(f"   Total line items created: {line_items_count}")
            logger.info(f"   Unique invoices in line items: {unique_invoices_count}")
            logger.info(f"   Missing line items: {missing_line_items}")
            
            if original_count == unique_invoices_count and missing_line_items == 0:
                logger.info("✅ Normalization validation passed!")
                return True
            else:
                logger.error("❌ Normalization validation failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during validation: {str(e)}")
            return False
    
    def run_normalization(self) -> bool:
        """Run the complete normalization process"""
        logger.info("🚀 Starting multi-item data normalization process...")
        
        if not self.connect_to_database():
            return False
        
        try:
            # Step 1: Create line items table
            if not self.create_line_items_table():
                return False
            
            # Step 2: Normalize existing data
            if not self.normalize_all_existing_data():
                return False
            
            # Step 3: Create triggers for future data
            if not self.create_triggers_and_functions():
                return False
            
            # Step 4: Create compatibility views
            if not self.create_views_for_compatibility():
                return False
            
            # Step 5: Validate the normalization
            if not self.validate_normalization():
                return False
            
            logger.info("🎉 Multi-item data normalization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Normalization process failed: {str(e)}")
            return False
        finally:
            if self.conn:
                self.conn.close()
                logger.info("🔌 Database connection closed")

def main():
    """Main function to run the normalization process"""
    print("💼 FinOpsysAI Multi-Item Data Normalization")
    print("=" * 50)
    
    normalizer = MultiItemNormalizer()
    success = normalizer.run_normalization()
    
    if success:
        print("\n✅ Normalization completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Update your application queries to use the new ai_invoice_line_items table")
        print("2. Use ai_invoice_expanded view for line-item queries")
        print("3. Use ai_invoice_summary view for aggregated invoice data")
        print("4. Test your application with the new normalized data structure")
    else:
        print("\n❌ Normalization failed. Please check the logs for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
