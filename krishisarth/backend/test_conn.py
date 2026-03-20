import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5433,
        user='krishisarth',
        password='password',
        dbname='krishisarth'
    )
    print("SUCCESS: Connected to PostgreSQL")
    conn.close()
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
