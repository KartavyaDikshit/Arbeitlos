import streamlit as st
import pandas as pd
import os
import json
import subprocess
from datetime import datetime
import scripts.find_contacts as fc
from scripts.scrape_jd import scrape_to_markdown
from scripts.generate_cover_letter import generate_cl
import urllib.parse
import time

st.set_page_config(layout="wide", page_title="Arbeitlos - Job Pipeline")

# Strict Professional UI UX Implementation
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    :root {
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --dark: #1e293b;
        --secondary: #64748b;
        --bg: #f8fafc;
        --border: #e2e8f0;
    }

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg);
    }

    /* Standardized Text Colors */
    h1, h2, h3, .stMarkdown p, .stMarkdown span, label {
        color: var(--dark) !important;
    }

    /* Tab Refinement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--secondary) !important;
        font-weight: 500;
        background-color: transparent;
        border: none;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }

    /* Standardized Buttons */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: 1px solid var(--primary) !important;
        border-radius: 4px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: background-color 0.2s !important;
    }
    .stButton > button:hover {
        background-color: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
    }

    /* Link Buttons */
    [data-testid="stLinkButton"] a {
        background-color: white !important;
        color: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 4px !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        display: inline-flex !important;
        padding: 8px 20px !important;
    }

    /* Job Card Styling */
    .job-card { 
        background-color: white; 
        padding: 24px; 
        border-radius: 8px; 
        border: 1px solid var(--border);
        margin-bottom: 16px;
    }
    .job-card h3 {
        margin-top: 0;
        color: var(--dark) !important;
        font-size: 1.1rem;
    }
    .job-info {
        color: var(--secondary) !important;
        font-size: 0.85rem;
        margin-bottom: 12px;
    }
    .job-snippet {
        color: var(--dark) !important;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stMarkdown {
        color: var(--dark) !important;
    }
    
    /* Error and Warning Overrides */
    .stAlert {
        background-color: white !important;
        border: 1px solid var(--border) !important;
        color: var(--dark) !important;
    }
    </style>
""", unsafe_allow_html=True)

TRACKING_FILE = "data/tracking.xlsx"

def load_tracker():
    cols = ["Date", "Company", "Title", "Contact Person", "Email", "LinkedIn", "Resume", "Cover Letter", "Gmail Link", "Status"]
    if os.path.exists(TRACKING_FILE):
        try:
            return pd.read_excel(TRACKING_FILE)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_to_tracker(data_dict):
    df = load_tracker()
    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    try:
        df.to_excel(TRACKING_FILE, index=False)
    except PermissionError:
        st.error("Action Required: Close tracking.xlsx in Excel to allow file update.")

def generate_gmail_link(recipient, subject, body):
    params = {
        "to": recipient,
        "subject": subject,
        "body": body
    }
    return f"https://mail.google.com/mail/?view=cm&fs=1&{urllib.parse.urlencode(params)}"

st.title("Arbeitlos: Job Application Pipeline")

# Sidebar
with st.sidebar:
    st.header("Control Panel")
    if st.button("Search Werkstudent Roles"):
        with st.spinner("Scanning job boards..."):
            subprocess.run(["python", "scripts/search_jobs.py"], shell=True)
        st.success("Search complete.")
        st.rerun()
    st.divider()
    st.markdown("Targets: Siemens, BMW, SAP, Bosch, Zalando, Infineon, Adidas, Allianz, Google DE.")

# Main Content
tabs = st.tabs(["Job Discovery", "Application History"])

with tabs[0]:
    jobs = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "jobs_found.json")

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            jobs = json.load(f)


    if not jobs:
        st.info("No leads available. Initiate search from the sidebar.")
    else:
        for idx, job in enumerate(jobs):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3>{job.get('title')}</h3>
                    <div class="job-info">
                        Company: {job.get('company')} | <b>Job Reference ID: {job.get('job_id')}</b>
                    </div>
                    <div class="job-info">Date: {job.get('published')}</div>
                    <div class="job-snippet">{job.get('snippet')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.link_button("Apply via Official Portal", job.get('url'))
                with col2:
                    if st.button("Initialize Application Suite", key=f"gen_{idx}"):
                        raw_title = job.get('title')
                        safe_title = "".join(x for x in raw_title if x.isalnum())
                        company = job.get('company')
                        domain = fc.get_domain_from_url(job.get('url'))
                        
                        with st.status("Generating Application Suite...", expanded=True) as status:
                            st.write("Phase 1: Identifying hiring contacts...")
                            contacts = fc.find_contacts(job.get('url'), raw_title, company)
                            best_contact = contacts[0] if contacts else None
                            
                            st.write("Phase 2: Tailoring professional resume...")
                            jd_path = f"data/raw_jds/{safe_title}.md"
                            subprocess.run(["python", "scripts/scrape_jd.py", job.get('url'), safe_title], shell=True)
                            
                            tex_out = f"data/tailored_outputs/{safe_title}_CV.tex"
                            subprocess.run(["python", "scripts/tailor_resume_lossless.py", "data/master_cv.tex", jd_path, tex_out], shell=True)
                            pdf_out = os.path.abspath(tex_out.replace(".tex", ".pdf"))
                            
                            st.write("Phase 3: Drafting formal cover letter...")
                            cl_out = os.path.abspath(f"data/tailored_outputs/{safe_title}_CL.md")
                            generate_cl("data/master_cv.tex", jd_path, cl_out)
                            
                            outreach_link = None
                            contact_info = "N/A"
                            contact_name = "Hiring Team"
                            contact_linkedin = "N/A"
                            
                            if best_contact:
                                contact_name = best_contact.get('name')
                                contact_linkedin = best_contact.get('linkedin')
                                st.write(f"Contact Persona Found: {contact_name}")
                                
                                st.write("Phase 4: Drafting personalized outreach...")
                                outreach_path = f"data/tailored_outputs/{safe_title}_Outreach.md"
                                subprocess.run(["python", "scripts/networker.py", domain, safe_title, tex_out, outreach_path], shell=True)
                                
                                if os.path.exists(outreach_path):
                                    with open(outreach_path, "r", encoding="utf-8") as f:
                                        outreach_body = f.read()
                                    
                                    email_addr = best_contact.get('email') if best_contact.get('email') else ""
                                    contact_info = f"{email_addr} | {contact_linkedin}"
                                    
                                    outreach_link = generate_gmail_link(
                                        email_addr,
                                        f"Application for {raw_title} - Kartavya Niraj Dikshit",
                                        outreach_body
                                    )
                            else:
                                st.warning("Notice: No specific persona identified. Outreach generation skipped.")

                            tracking_data = {
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Company": company,
                                "Title": raw_title,
                                "Contact Person": contact_name,
                                "Email": best_contact.get('email', 'N/A') if best_contact else 'N/A',
                                "LinkedIn": contact_linkedin,
                                "Resume": f'=HYPERLINK("{pdf_out}", "PDF")',
                                "Cover Letter": f'=HYPERLINK("{cl_out}", "Letter")',
                                "Gmail Link": f'=HYPERLINK("{outreach_link}", "Draft Gmail")' if outreach_link else "N/A",
                                "Status": "Ready"
                            }
                            save_to_tracker(tracking_data)
                            status.update(label="Application Suite Generated Successfully", state="complete")
                            
                            st.divider()
                            st.write("Action Required: Review Materials")
                            action_col1, action_col2 = st.columns(2)
                            with action_col1:
                                if st.button("Open Tailored Resume", key=f"open_res_{idx}"):
                                    os.startfile(pdf_out)
                            with action_col2:
                                if st.button("Open Cover Letter", key=f"open_cl_{idx}"):
                                    os.startfile(cl_out)
                            
                            if outreach_link:
                                st.link_button("Review Gmail Draft", outreach_link)
                            if contact_linkedin != "N/A":
                                st.link_button("View LinkedIn Profile", contact_linkedin)
                st.write("")

with tabs[1]:
    st.subheader("Application Tracking History")
    df = load_tracker()
    st.dataframe(df, width="stretch")
    if st.button("Open Spreadsheet File"):
        os.startfile(os.path.abspath(TRACKING_FILE))
