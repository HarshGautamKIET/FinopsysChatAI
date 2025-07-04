import psycopg2
from config import Config

try:
    config = Config()
    conn = psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        database=config.POSTGRES_DATABASE,
        options=f'-c search_path={config.POSTGRES_SCHEMA}'
    )
    cursor = conn.cursor()
    
    # Get column info
    cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ai_invoice' 
    ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print('Current table schema:')
    for col_name, col_type in columns:
        print(f'  {col_name}: {col_type}')
    
    cursor.close()
    conn.close()
    print('\nColumn check completed successfully!')
    
except Exception as e:
    print(f'Error: {e}')
