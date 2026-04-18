import os
import json
import psycopg2
import cloudinary
import cloudinary.uploader
from celery import Celery
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Cloudinary will automatically pick up CLOUDINARY_URL from your .env file!
cloudinary.config(secure=True)

celery_app = Celery("resume_tasks", broker=REDIS_URL, backend=REDIS_URL)

client = genai.Client()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_text_chunks(text: str, chunk_size=200, overlap=30):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
    return chunks

# --- NOTE THE NEW PARAMETER: temp_file_path ---
@celery_app.task(bind=True, max_retries=3)
def process_resume_task(self, text: str, filename: str, temp_file_path: str):
    try:
        print(f"⚙️ [CELERY] Starting AI processing for {filename}...")
        
        # 1. Upload the file to Cloudinary
        print("☁️ Uploading PDF to Cloud Storage...")
        upload_result = cloudinary.uploader.upload(temp_file_path, resource_type="auto")
        resume_cloud_url = upload_result.get("secure_url")
        print(f"✅ Uploaded! URL: {resume_cloud_url}")
        
        # 2. Delete the local temporary file now that it's safe in the cloud
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # 3. AI JSON Extraction
        prompt = f"""
        You are an expert technical recruiter. Extract the following information from the resume text.
        Respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.
        
        Use this exact JSON structure:
        {{
            "name": "Full Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "total_experience": 2.5,
            "domain": "Backend",
            "skills": ["Python", "React", "SQL"]
        }}
        Resume Text:
        {text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        extracted_data = json.loads(response.text)
        
        # 4. Save to DB (Notice we added resume_url to the INSERT statement!)
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO candidates (name, email, phone, total_experience, domain, resume_text, resume_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            extracted_data.get('name', 'Unknown'),
            extracted_data.get('email', 'Unknown'),
            extracted_data.get('phone', 'Unknown'),
            extracted_data.get('total_experience', 0),
            extracted_data.get('domain', 'Unknown'),
            text,
            resume_cloud_url  # <--- THE NEW CLOUD URL
        ))
        candidate_id = cursor.fetchone()[0]
        
        # Insert Skills
        skills = extracted_data.get('skills', [])
        for skill_name in skills:
            skill_name = skill_name.strip().title()
            cursor.execute("INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (skill_name,))
            cursor.execute("SELECT id FROM skills WHERE name = %s;", (skill_name,))
            skill_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO candidate_skills (candidate_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (candidate_id, skill_id))
            
        # 5. Generate Vector Embeddings
        chunks = get_text_chunks(text)
        for chunk in chunks:
            embedding_vector = embedding_model.encode(chunk).tolist() 
            cursor.execute("""
                INSERT INTO candidate_embeddings (candidate_id, embedding)
                VALUES (%s, %s);
            """, (candidate_id, embedding_vector))
            
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ [CELERY] Successfully finished {filename}!")
        return "Success"
        
    except Exception as e:
        print(f"❌ [CELERY ERROR] {filename}: {e}")
        raise self.retry(exc=e, countdown=30)