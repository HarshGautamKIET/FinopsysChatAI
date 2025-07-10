import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='localhost',
        database='finopsys_db',
        user='postgres',
        password='Harsh@123'
    )
    cursor = conn.cursor()
    
    # Test the correct column names
    cursor.execute("SELECT case_id, bill_date FROM ai_invoice LIMIT 5")
    results = cursor.fetchall()
    
    print("✅ Database connection successful!")
    print("Sample data:")
    for row in results:
        print(f"  case_id: {row[0]}, bill_date: {row[1]}")
    
    cursor.close()
    conn.close()
    print("✅ Database connection closed successfully!")
    
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
