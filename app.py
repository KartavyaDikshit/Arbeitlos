import streamlit as st
import pandas as pd
import os
import json
import subprocess
from datetime import datetime
import scripts.find_contacts as fc
from scripts.find_contacts_gemini import find_hiring_manager
from scripts.scrape_jd import scrape_to_markdown
from scripts.generate_cover_letter import generate_cl
import urllib.parse
import time

st.set_page_config(layout="wide", page_title="Arbeitlos - Professional Job Pipeline")

# Professional UI UX Implementation (Minimalist, No Emojis)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    :root {
        --primary: #0f172a;
        --primary-hover: #1e293b;
        --dark: #0f172a;
        --secondary: #64748b;
        --bg: #ffffff;
        --border: #e2e8f0;
    }

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg);
    }

    h1, h2, h3, .stMarkdown p, .stMarkdown span, label {
        color: var(--dark) !important;
    }

    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: 1px solid var(--primary) !important;
        border-radius: 4px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background-color: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
    }

    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid var(--border);
    }
    
    .result-card {
        padding: 20px;
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-top: 20px;
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)

def extract_job_info(jd_text):
    """Extracts company name and job title from JD text using Gemini."""
    prompt = (
        f"Extract the Company Name and Job Title from the following job description:\n\n"
        f"{jd_text}\n\n"
        f"Return ONLY a JSON object with keys: 'company', 'title'. "
        f"Example: {{\"company\": \"Siemens\", \"title\": \"Working Student AI\"}}"
    )
    try:
        process = subprocess.Popen(
            ["gemini", "-e", "", "--model", "flash-lite", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout, stderr = process.communicate(input=prompt, timeout=120)
        if process.returncode == 0:
            text = stdout.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
    except Exception as e:
        st.error(f"Extraction error: {e}")
    return {"company": "Unknown", "title": "Unknown_Job"}

def main():
    st.title("Arbeitlos: Pipeline")
    st.markdown("Enter the job description to generate a professional application suite.")

    # Initialize session state
    if "pipeline_results" not in st.session_state:
        st.session_state.pipeline_results = None
    if "contact_results" not in st.session_state:
        st.session_state.contact_results = None

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Input Area
    man_jd_text = st.text_area("Job Description Content", height=400, placeholder="Paste the full job description text here...")
    
    col_run, col_clear = st.columns([1, 5])
    with col_run:
        run_btn = st.button("Generate Suite")
    with col_clear:
        if st.button("Clear Pipeline"):
            st.session_state.pipeline_results = None
            st.session_state.contact_results = None
            st.rerun()

    if run_btn:
        if not man_jd_text:
            st.warning("Job description text is required.")
        else:
            with st.status("Processing Application...", expanded=True) as status:
                st.write("Extracting job metadata...")
                job_info = extract_job_info(man_jd_text)
                company = job_info.get("company", "Unknown")
                title = job_info.get("title", "Job")
                
                safe_title = "".join(x for x in title if x.isalnum())
                job_dir = os.path.join(base_dir, "data", "tailored_outputs", safe_title)
                os.makedirs(job_dir, exist_ok=True)
                
                jd_path = os.path.join(base_dir, "data", "raw_jds", f"{safe_title}.md")
                with open(jd_path, "w", encoding="utf-8") as f:
                    f.write(man_jd_text)
                
                st.write(f"Tailoring for {company} - {title}...")
                tex_out = os.path.join(job_dir, "CV.tex")
                subprocess.run(["python", "scripts/tailor_resume_lossless.py", "data/master_cv.md", jd_path, tex_out], shell=True)
                
                pdf_out = os.path.join(job_dir, "Tailored_CV.pdf")
                cl_out = os.path.join(job_dir, "Cover_Letter.pdf")
                
                st.session_state.pipeline_results = {
                    "company": company,
                    "title": title,
                    "pdf_out": pdf_out,
                    "cl_out": cl_out,
                    "job_dir": job_dir,
                    "safe_title": safe_title
                }
                status.update(label="Application Suite Ready", state="complete")

    # Display Results
    if st.session_state.pipeline_results:
        res = st.session_state.pipeline_results
        st.markdown(f"### Application Materials: {res['company']}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("View Optimized Resume"):
                path = os.path.abspath(res["pdf_out"])
                if os.path.exists(path):
                    os.startfile(path)
                else:
                    st.error("Resume file not found.")
        with c2:
            if st.button("View Cover Letter"):
                path = os.path.abspath(res["cl_out"])
                if os.path.exists(path):
                    os.startfile(path)
                else:
                    st.error("Cover letter file not found.")

        st.divider()
        
        # Optional: Discovery
        st.markdown("### Optional: Intelligence Discovery")
        st.markdown("Identify the hiring manager and contact information based on the job details.")
        
        if st.button("Find Hiring Contact"):
            with st.spinner("Searching for contacts..."):
                contact = find_hiring_manager("Manual_Input", res['company'], res['title'], res['job_dir'])
                st.session_state.contact_results = contact
        
        if st.session_state.contact_results:
            con = st.session_state.contact_results
            st.markdown(f"""
            <div class="result-card">
                <strong>Contact:</strong> {con.get('name')}<br>
                <strong>Role:</strong> {con.get('title')}<br>
                <strong>LinkedIn:</strong> <a href="{con.get('linkedin_url')}">{con.get('linkedin_url')}</a><br>
                <strong>Email Guess:</strong> {con.get('email_guess')}
            </div>
            """, unsafe_allow_html=True)
            
            if con.get('cold_email'):
                with st.expander("Draft Outreach Email"):
                    st.text_area("Email Content", value=con['cold_email'], height=200)
            
            if con.get('linkedin_invite'):
                with st.expander("LinkedIn Invitation"):
                    st.text_area("Message", value=con['linkedin_invite'], height=100)

    # Sidebar
    with st.sidebar:
        st.markdown("## Configuration")
        st.markdown("System initialized for professional application tailoring.")
        st.divider()
        st.markdown("Target Sectors: Technology, Engineering, Data Science.")

if __name__ == "__main__":
    main()
