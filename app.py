import streamlit as st
import requests
import json
import base64

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RecruitIQ - Enterprise Applicant Tracking", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Premium Custom CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Background & Glassmorphism */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgb(14, 21, 38) 0%, rgb(4, 7, 16) 90%);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 30px;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Glassmorphic Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 2rem;
    margin-bottom: 1.5rem;
    transition: transform 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-5px);
    border: 1px solid rgba(56, 189, 248, 0.3);
}

/* Headings */
h1 {
    background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem !important;
    font-weight: 700 !important;
    text-align: center;
    padding-bottom: 0.5rem;
}

h2, h3 {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    color: white;
    border-radius: 8px;
    padding: 0.6rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    width: 100%;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6);
    color: white !important;
    border: none !important;
}

/* File Uploader area */
[data-testid="stFileUploaderDropzone"] {
    background-color: rgba(255, 255, 255, 0.02) !important;
    border: 2px dashed rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    padding: 3rem !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #8b5cf6 !important;
    background-color: rgba(139, 92, 246, 0.05) !important;
}

/* Input Fields */
.stTextInput>div>div>input {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
}

.stTextInput>div>div>input:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 1px #8b5cf6 !important;
}

/* Dataframe/Table */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Make tabs nice */
.stTabs [data-baseweb="tab"] {
    color: #cbd5e1 !important;
    border-radius: 8px 8px 0px 0px;
}
.stTabs [aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🧠 RecruitIQ System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;'>Intelligent Candidate Retrieval & Semantic Engine</p>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Upload & Process", "📂 Candidate Directory", "💬 Semantic AI Search"])

with tab1:
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <h3>Enterprise Workflow</h3>
            <p style="color: #94a3b8; margin-top: 10px;">
                Our robust pipeline guarantees speed and accuracy:
            </p>
            <ul style="color: #cbd5e1; list-style-type: '⚡ '; margin-top: 15px; line-height: 1.8;">
                <li>Uploads mapped to secure Cloud Storage</li>
                <li>Async Worker nodes process data cleanly</li>
                <li>Generative AI extracts profile variables</li>
                <li>RAG Embeddings orchestrate deep context</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📥 Secure Resume Intake")
        uploaded_file = st.file_uploader("Drop your PDF application here", type="pdf")
        
        if st.button("Initialize Processing Pipeline", use_container_width=True):
            if uploaded_file is not None:
                with st.spinner("Connecting to ingestion queue..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    try:
                        response = requests.post(f"{API_URL}/upload-resume/", files=files)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✨ Success! {data['message']}")
                            st.info("Worker nodes are actively extracting text and creating vector embeddings!")
                        else:
                            st.error(f"Ingestion failed: {response.text}")
                    except requests.exceptions.ConnectionError:
                         st.error("Engine offline. Please start FastAPI Server & Redis Services.")
            else:
                st.warning("Please attach a valid PDF document to continue.")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("👥 Global Directory Core")
    
    col_search, col_stats = st.columns([3, 1])
    with col_search:
         domain_filter = st.text_input("Refine Query (e.g., Data Science, Engineering)", placeholder="Enter domain keyword constraint...")
    
    with col_stats:
         st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
         fetch_btn = st.button("Execute Core Search", use_container_width=True)
         
    if fetch_btn:
        url = f"{API_URL}/candidates/"
        if domain_filter:
            url += f"?domain={domain_filter}"
            
        try:
            with st.spinner("Querying vector relational records..."):
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("data", [])
                    st.markdown(f"<p style='color: #4ade80;'>✅ Found {data.get('total_found', 0)} strong candidate matches</p>", unsafe_allow_html=True)
                    if candidates:
                        st.dataframe(candidates, use_container_width=True)
                    else:
                         st.info("No records matching your pipeline limits. Try a broader search keyword.")
                else:
                    st.error("Relational Engine Error")
        except Exception as e:
            st.error("Connection failed.")
            
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("🤖 Context-Aware AI Recruiter")
    st.markdown("<p style='color: #94a3b8;'>Formulate deep semantic queries matching candidate profiles. Example: 'Find me someone with exactly 5+ years of experience who knows React Native and has handled deployment.'</p>", unsafe_allow_html=True)
    
    query = st.text_input("Generative Prompt Request", placeholder="Synthesize candidate request...")
    
    if st.button("Synthesize Best Matches", use_container_width=True):
        if query:
            with st.spinner("Computing semantic vectors and pinging LLM layer..."):
                try:
                    response = requests.get(f"{API_URL}/ask/", params={"query": query})
                    if response.status_code == 200:
                        data = response.json()
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 2rem 0;'>", unsafe_allow_html=True)
                        st.markdown("### ✨ Output Synthesis Decision")
                        
                        col_ans, col_refs = st.columns([2, 1])
                        
                        with col_ans:
                             st.markdown(f"<div style='background: rgba(139, 92, 246, 0.1); padding: 1.5rem; border-radius: 8px; border-left: 4px solid #8b5cf6; line-height: 1.7; color: #f8fafc; font-size: 1.05rem;'>{data.get('ai_answer', 'No suitable answer found.')}</div>", unsafe_allow_html=True)
                             
                        with col_refs:
                             refs = data.get("candidates_referenced", [])
                             st.markdown("**🔗 Highest Match Confidence Candidates:**")
                             if refs:
                                 for ref in refs:
                                     st.markdown(f"""
                                     <div style='background: rgba(255,255,255,0.03); padding: 0.8rem; margin-bottom: 0.5rem; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; font-weight: 500;'>
                                        👤 {ref}
                                     </div>
                                     """, unsafe_allow_html=True)
                             else:
                                  st.caption("No strong candidate constraints mapped.")
                    else:
                        st.error("Vector constraint failed to execute.")
                except Exception as e:
                    st.error(f"Cannot orchestrate AI context endpoints: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<br/><br/>
<div style='text-align: center; color: #475569; font-size: 0.85rem; font-weight: 500; letter-spacing: 0.5px;'>
    Powered by pgvector Vectors • Google Gemini LLMs • Asynchronous Queue Distribution Pipeline
</div>
""", unsafe_allow_html=True)