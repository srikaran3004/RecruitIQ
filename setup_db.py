import os
import psycopg2
from dotenv import load_dotenv

# Load database URL from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# The SQL commands to build our database structure
SCHEMA_SQL = """
-- 1. Enable vector extension for RAG later
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Main Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    total_experience NUMERIC(4,1),
    domain VARCHAR(100),
    resume_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Skills Table (Stores unique skills)
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. Mapping Table (Links Candidates and Skills)
CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (candidate_id, skill_id)
);

-- 5. Embeddings Table for RAG (Semantic Search)
CREATE TABLE IF NOT EXISTS candidate_embeddings (
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    embedding vector(1536), 
    PRIMARY KEY (candidate_id)
);
"""

try:
    print("Connecting to Neon Database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("Creating tables...")
    cursor.execute(SCHEMA_SQL)
    
    # Commit saves the changes to the database
    conn.commit() 

    print("✅ Schema created successfully! All tables are ready.")

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Error creating schema:", e)