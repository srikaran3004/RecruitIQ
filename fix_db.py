import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    # Change to 384 for the lightning-fast local model
    cursor.execute("ALTER TABLE candidate_embeddings ALTER COLUMN embedding TYPE vector(384);")
    conn.commit()
    print("✅ Database vector size updated to 384!")
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)  