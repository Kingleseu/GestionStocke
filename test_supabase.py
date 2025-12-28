import os
import sys
import psycopg

def test_connection():
    url = "postgresql://postgres:0iiVSpQqrmJf8tMC@db.zgtfpccwbifxttwidqgv.supabase.co:5432/postgres"
    print(f"Testing connection to: {url.split('@')[1]}")
    try:
        conn = psycopg.connect(url, connect_timeout=10)
        print("✅ Connection successful!")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        print(f"Server version: {cur.fetchone()[0]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"FAILED: Connection failed: {e}")

if __name__ == "__main__":
    try:
        test_connection()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
