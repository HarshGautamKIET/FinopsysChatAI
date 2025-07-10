import psycopg2
import json

try:
    conn = psycopg2.connect(
        host='localhost',
        database='finopsys_db',
        user='postgres',
        password='Harsh@123'
    )
    cursor = conn.cursor()
    
    # Check item data formats
    cursor.execute("SELECT case_id, items_description, items_unit_price, items_quantity FROM ai_invoice WHERE items_description IS NOT NULL LIMIT 5")
    results = cursor.fetchall()
    
    print("✅ Sample item data:")
    for row in results:
        case_id, desc, price, qty = row
        print(f"\nCase: {case_id}")
        print(f"Description: {desc} (Type: {type(desc)})")
        print(f"Unit Price: {price} (Type: {type(price)})")
        print(f"Quantity: {qty} (Type: {type(qty)})")
        
        # Try to detect format
        if desc:
            if desc.strip().startswith('['):
                print("  -> Detected JSON array format")
                try:
                    parsed = json.loads(desc)
                    print(f"  -> Parsed JSON: {parsed}")
                except:
                    print("  -> JSON parse failed")
            elif ',' in desc:
                print("  -> Detected CSV format")
                items = [item.strip() for item in desc.split(',')]
                print(f"  -> Parsed CSV: {items}")
            else:
                print("  -> Single item")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
