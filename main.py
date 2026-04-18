from fastapi import FastAPI, UploadFile, File
import fitz  
import psycopg2
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Import your new Celery task
from worker import process_resume_task

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Only load the embedding model in the main app for the /ask/ endpoint
print("📥 API: Loading Local Search Model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

app = FastAPI(title="RecruitIQ")

@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    try:
        # Read the file
        file_bytes = await file.read()
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        text = " ".join(text.split())
        
        # --- THE CELERY MAGIC ---
        # .delay() pushes the data to Redis. The API doesn't wait for it to finish!
        process_resume_task.delay(text, file.filename)
        
        return {
            "status": "queued",
            "message": "Resume added to the persistent queue. Processing securely in the background.",
            "filename": file.filename
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/candidates/")
def get_candidates(domain: str = None):
    # (Same code as before - keep it exactly the same)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        if domain:
            clean_domain = domain.replace(" ", "")
            cursor.execute("SELECT id, name, email, total_experience, domain FROM candidates WHERE REPLACE(domain, ' ', '') ILIKE %s;", (f"%{clean_domain}%",))
        else:
            cursor.execute("SELECT id, name, email, total_experience, domain FROM candidates;")
            
        candidates = cursor.fetchall()
        result_list = [{"id": c[0], "name": c[1], "email": c[2], "experience": c[3], "domain": c[4]} for c in candidates]
            
        cursor.close()
        conn.close()
        return {"status": "success", "total_found": len(result_list), "data": result_list}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/ask/")
def ask_ai(query: str):
    # (Same code as before - keep it exactly the same)
    try:
        query_vector = embedding_model.encode(query).tolist()
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.name, c.domain, c.total_experience, c.resume_text
            FROM candidate_embeddings ce
            JOIN candidates c ON c.id = ce.candidate_id
            WHERE ce.embedding <=> %s::vector < 0.95
            ORDER BY ce.embedding <=> %s::vector
            LIMIT 6;
        """, (query_vector, query_vector))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not results:
            return {"status": "success", "query": query, "ai_answer": "No relevant candidates found.", "candidates_referenced": []}
            
        unique_candidates = {}
        for row in results:
            name, domain, exp, text = row
            if name not in unique_candidates:
                unique_candidates[name] = {"domain": domain, "exp": exp, "text": text}
                
        context_text = "Here are the top matching candidates from the database:\n\n"
        top_names = []
        for name, data in unique_candidates.items():
            top_names.append(name)
            context_text += f"- Candidate: {name} | Domain: {data['domain']} | Exp: {data['exp']} years\n"
            context_text += f"  Resume snippet: {data['text'][:1200]}...\n\n"
            
        # Initialize a temporary Gemini client just for answering questions
        from google import genai
        client = genai.Client()
        prompt = f"""You are an intelligent HR assistant. Answer the user's query using ONLY the candidate context provided below. User Query: {query} \n Context: {context_text}"""
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return {"status": "success", "query": query, "ai_answer": response.text, "candidates_referenced": top_names}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import shutil

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    try:
        # 1. Read the text for AI processing
        file_bytes = await file.read()
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        text = " ".join(text.split())
        
        # 2. Save the file temporarily to the local disk
        os.makedirs("temp_uploads", exist_ok=True)
        temp_file_path = f"temp_uploads/{file.filename}"
        
        # We write the raw bytes to a temporary PDF file
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file_bytes)
        
        # 3. Pass BOTH the text and the temp file path to Celery
        process_resume_task.delay(text, file.filename, temp_file_path)
        
        return {
            "status": "queued",
            "message": "Resume added to the persistent queue. Processing securely in the background.",
            "filename": file.filename
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

#Terminal 1:uvicorn main:app --reload
#Terminal 2:celery -A worker.celery_app worker --loglevel=info --pool=solo