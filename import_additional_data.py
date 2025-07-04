#!/usr/bin/env python3
"""
Import Additional Data into PostgreSQL Database
Adds more comprehensive sample data to the ai_invoice table
"""

import psycopg2
import json
from datetime import datetime, timedelta
import random
import sys
import os

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'Harsh@123',
    'database': 'finopsys_db'
}

def generate_additional_sample_data():
    """Generate additional realistic sample data"""
    
    # Vendor configurations
    vendors = [
        'VENDOR001', 'VENDOR002', 'VENDOR003', 'VENDOR004', 'VENDOR005'
    ]
    
    # Sample items and services (all in proper JSON format)
    items_data = {
        'VENDOR001': {
            'descriptions': [
                ["Cloud Hosting", "SSL Certificate", "Domain Renewal"],
                ["Web Development", "UI/UX Design"],
                ["Monthly Hosting", "Backup Service"],
                ["Cloud Storage", "Email Service", "Support"]
            ],
            'prices': [
                [99.99, 49.99, 29.99],
                [2500.00, 1500.00],
                [79.99, 39.99],
                [150.00, 50.00, 200.00]
            ],
            'quantities': [
                [1, 1, 1],
                [1, 1],
                [1, 1],
                [1, 1, 1]
            ]
        },
        'VENDOR002': {
            'descriptions': [
                ["Office Software", "Antivirus License"],
                ["Consulting Hours", "Training Session"],
                ["Hardware Maintenance", "Software Updates"]
            ],
            'prices': [
                [299.99, 99.99],
                [150.00, 300.00],
                [500.00, 200.00]
            ],
            'quantities': [
                [5, 10],
                [8, 2],
                [1, 1]
            ]
        },
        'VENDOR003': {
            'descriptions': [
                ["Marketing Campaign", "Social Media Management"],
                ["Content Creation", "SEO Optimization"],
                ["Digital Advertising", "Analytics Setup"]
            ],
            'prices': [
                [1200.00, 800.00],
                [600.00, 400.00],
                [1500.00, 300.00]
            ],
            'quantities': [
                [1, 3],
                [10, 1],
                [1, 1]
            ]
        },
        'VENDOR004': {
            'descriptions': [
                ["Legal Consultation", "Contract Review"],
                ["Document Preparation", "Filing Services"],
                ["Compliance Audit", "Risk Assessment"]
            ],
            'prices': [
                [350.00, 200.00],
                [150.00, 100.00],
                [2000.00, 1500.00]
            ],
            'quantities': [
                [4, 2],
                [3, 5],
                [1, 1]
            ]
        },
        'VENDOR005': {
            'descriptions': [
                ["Financial Analysis", "Tax Preparation"],
                ["Bookkeeping", "Payroll Services"],
                ["Audit Services", "Financial Planning"]
            ],
            'prices': [
                [800.00, 600.00],
                [400.00, 350.00],
                [3000.00, 1200.00]
            ],
            'quantities': [
                [1, 1],
                [12, 12],
                [1, 1]
            ]
        }
    }
    
    statuses = ['Paid', 'Pending', 'Partial', 'Overdue', 'Draft']
    departments = ['Finance', 'IT', 'Marketing', 'Legal', 'HR', 'Operations']
    
    sample_data = []
    
    # Generate 47 more records (to make total 50 including existing 3)
    for i in range(4, 51):  # CASE004 to CASE050
        vendor_id = random.choice(vendors)
        case_id = f"CASE{i:03d}"
        bill_id = f"BILL{i:03d}"
        customer_id = f"CUST{random.randint(1, 20):03d}"
        
        # Select random item data for this vendor
        vendor_items = items_data.get(vendor_id, items_data['VENDOR001'])
        item_index = random.randint(0, len(vendor_items['descriptions']) - 1)
        
        items_description = vendor_items['descriptions'][item_index]
        items_unit_price = vendor_items['prices'][item_index]
        items_quantity = vendor_items['quantities'][item_index]
        
        # Calculate amounts based on items
        try:
            # Items are already in proper list format
            desc_list = items_description
            price_list = items_unit_price
            qty_list = items_quantity
            
            subtotal = sum(p * q for p, q in zip(price_list, qty_list))
        except:
            subtotal = random.uniform(100, 5000)
        
        total_tax = round(subtotal * 0.08, 2)  # 8% tax
        amount = round(subtotal + total_tax, 2)
        
        status = random.choice(statuses)
        if status == 'Paid':
            paid = amount
            balance_amount = 0.00
        elif status == 'Partial':
            paid = round(amount * random.uniform(0.3, 0.8), 2)
            balance_amount = round(amount - paid, 2)
        else:
            paid = 0.00
            balance_amount = amount
        
        # Generate dates
        base_date = datetime.now() - timedelta(days=random.randint(1, 365))
        bill_date = base_date + timedelta(days=random.randint(0, 5))
        due_date = bill_date + timedelta(days=30)
        
        # Optional approval dates (use correct column names)
        approveddate1 = None
        approveddate2 = None
        if status in ['Paid', 'Partial']:
            approveddate1 = bill_date + timedelta(days=random.randint(1, 10))
            if random.choice([True, False]):
                approveddate2 = approveddate1 + timedelta(days=random.randint(1, 5))
        
        record = {
            'case_id': case_id,
            'bill_id': bill_id,
            'customer_id': customer_id,
            'vendor_id': vendor_id,
            'due_date': due_date.strftime('%Y-%m-%d'),
            'bill_date': bill_date.strftime('%Y-%m-%d'),
            'decline_date': None,  # Most invoices aren't declined
            'receiving_date': (bill_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'approveddate1': approveddate1.strftime('%Y-%m-%d') if approveddate1 else None,
            'approveddate2': approveddate2.strftime('%Y-%m-%d') if approveddate2 else None,
            'amount': amount,
            'balance_amount': balance_amount,
            'paid': paid,
            'total_tax': total_tax,
            'subtotal': subtotal,
            'items_description': json.dumps(items_description),  # Convert to JSON string
            'items_unit_price': json.dumps(items_unit_price),    # Convert to JSON string
            'items_quantity': json.dumps(items_quantity),        # Convert to JSON string
            'status': status,
            'decline_reason': None if status != 'Declined' else 'Budget constraints',
            'department': random.choice(departments)
        }
        
        sample_data.append(record)
    
    return sample_data

def import_data():
    """Import additional data into PostgreSQL database"""
    try:
        print("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check current record count
        cursor.execute("SELECT COUNT(*) FROM ai_invoice;")
        current_count = cursor.fetchone()[0]
        print(f"📊 Current records in database: {current_count}")
        
        # Generate additional sample data
        print("🎲 Generating additional sample data...")
        additional_data = generate_additional_sample_data()
        
        # Prepare insert statement (note: no invoice_id column, approveddate1/approveddate2 instead of approved_date1/approved_date2)
        insert_sql = """
        INSERT INTO ai_invoice (
            case_id, bill_id, customer_id, vendor_id,
            due_date, bill_date, decline_date, receiving_date, 
            approveddate1, approveddate2,
            amount, balance_amount, paid, total_tax, subtotal,
            items_description, items_unit_price, items_quantity,
            status, decline_reason, department
        ) VALUES (
            %(case_id)s, %(bill_id)s, %(customer_id)s, %(vendor_id)s,
            %(due_date)s, %(bill_date)s, %(decline_date)s, %(receiving_date)s,
            %(approveddate1)s, %(approveddate2)s,
            %(amount)s, %(balance_amount)s, %(paid)s, %(total_tax)s, %(subtotal)s,
            %(items_description)s, %(items_unit_price)s, %(items_quantity)s,
            %(status)s, %(decline_reason)s, %(department)s
        )
        """
        
        print(f"💾 Importing {len(additional_data)} additional records...")
        
        # Insert data in batches
        batch_size = 10
        for i in range(0, len(additional_data), batch_size):
            batch = additional_data[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            print(f"   ✓ Inserted batch {i//batch_size + 1}/{(len(additional_data)-1)//batch_size + 1}")
        
        # Commit the transaction
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM ai_invoice;")
        final_count = cursor.fetchone()[0]
        
        # Display summary by vendor
        cursor.execute("""
            SELECT vendor_id, COUNT(*) as record_count, 
                   SUM(amount) as total_amount,
                   COUNT(CASE WHEN status = 'Paid' THEN 1 END) as paid_invoices
            FROM ai_invoice 
            GROUP BY vendor_id 
            ORDER BY vendor_id;
        """)
        
        vendor_summary = cursor.fetchall()
        
        print(f"\n✅ Import completed successfully!")
        print(f"📈 Total records: {current_count} → {final_count} (+{final_count - current_count})")
        print(f"\n📊 Vendor Summary:")
        print("┌─────────────┬─────────┬─────────────┬──────────────┐")
        print("│ Vendor ID   │ Records │ Total Amount│ Paid Invoices│")
        print("├─────────────┼─────────┼─────────────┼──────────────┤")
        for vendor_id, count, total_amt, paid_count in vendor_summary:
            print(f"│ {vendor_id:<11} │ {count:>7} │ ${total_amt:>10.2f} │ {paid_count:>12} │")
        print("└─────────────┴─────────┴─────────────┴──────────────┘")
        
        # Show sample of recent records
        cursor.execute("""
            SELECT case_id, vendor_id, amount, status, bill_date
            FROM ai_invoice 
            ORDER BY case_id DESC 
            LIMIT 5;
        """)
        
        recent_records = cursor.fetchall()
        print(f"\n🔍 Sample of most recent records:")
        print("┌─────────┬───────────┬──────────┬─────────┬────────────┐")
        print("│ Case ID │ Vendor ID │ Amount   │ Status  │ Bill Date  │")
        print("├─────────┼───────────┼──────────┼─────────┼────────────┤")
        for case_id, vendor_id, amount, status, bill_date in recent_records:
            print(f"│ {case_id:<7} │ {vendor_id:<9} │ ${amount:>7.2f} │ {status:<7} │ {bill_date} │")
        print("└─────────┴───────────┴──────────┴─────────┴────────────┘")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Data import completed! Your PostgreSQL database is now ready with comprehensive sample data.")
        print(f"🚀 You can now test the FinOpsysAI application with this expanded dataset.")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error during import: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {str(e)}")
        return False

def verify_data_integrity():
    """Verify the integrity of imported data"""
    try:
        print("\n🔍 Verifying data integrity...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for data consistency
        checks = [
            ("Total records", "SELECT COUNT(*) FROM ai_invoice"),
            ("Records with valid amounts", "SELECT COUNT(*) FROM ai_invoice WHERE amount > 0"),
            ("Records with valid vendor_ids", "SELECT COUNT(*) FROM ai_invoice WHERE vendor_id IS NOT NULL"),
            ("Records with item descriptions", "SELECT COUNT(*) FROM ai_invoice WHERE items_description IS NOT NULL"),
            ("Paid invoices balance check", "SELECT COUNT(*) FROM ai_invoice WHERE status = 'Paid' AND balance_amount = 0"),
        ]
        
        print("\n📋 Data Integrity Report:")
        print("┌─────────────────────────────────┬─────────┐")
        print("│ Check                           │ Count   │")
        print("├─────────────────────────────────┼─────────┤")
        
        for check_name, sql in checks:
            cursor.execute(sql)
            count = cursor.fetchone()[0]
            print(f"│ {check_name:<31} │ {count:>7} │")
        
        print("└─────────────────────────────────┴─────────┘")
        
        cursor.close()
        conn.close()
        
        print("✅ Data integrity verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during data verification: {str(e)}")
        return False

if __name__ == "__main__":
    print("🏦 FinOpsysAI - Additional Data Import Utility")
    print("=" * 50)
    
    # Import additional data
    if import_data():
        # Verify data integrity
        verify_data_integrity()
        print(f"\n🎯 Next Steps:")
        print(f"   1. Start the application: python start_app.py")
        print(f"   2. Test with various vendor queries")
        print(f"   3. Explore the expanded dataset with different AI queries")
    else:
        print("❌ Import failed. Please check the error messages above.")
        sys.exit(1)
