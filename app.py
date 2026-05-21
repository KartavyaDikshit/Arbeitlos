import streamlit as st
import pandas as pd
import os
import json
import subprocess
import re
import time
import sys
from datetime import datetime
from scripts.utils import check_dependency

try:
    import psutil
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

# Set page config
st.set_page_config(layout="wide", page_title="Arbeitlos 2.0 | Executive Dashboard")

# --- EXECUTIVE MINIMALIST STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

    /* Global Typography & Colors */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FDFDFD !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #2C2C2C !important;
    }

    h1, h2, h3 {
        font-family: 'Cormorant+Garamond', serif !important;
        color: #2C2C2C !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #E5E5E5;
        padding-bottom: 10px;
        margin-top: 30px !important;
    }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: #F8F9FB !important;
        border-right: 1px solid #E5E5E5;
    }
    
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #2C2C2C !important;
        font-weight: 500 !important;
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-family: 'Cormorant+Garamond', serif !important;
        color: #2C2C2C !important;
        font-size: 2.5rem !important;
    }

    /* Formal Buttons */
    .stButton > button {
        border-radius: 2px !important;
        border: 1px solid #2C2C2C !important;
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #2C2C2C !important;
    }

    /* Job/Application Cards */
    .job-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E5E5;
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 4px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .job-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILITIES ---

def run_script(cmd_list):
    """Runs a script safely and returns (success, output)."""
    try:
        if cmd_list[0] == "python":
            cmd_list[0] = sys.executable
        
        process = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=(sys.platform == "win32")
        )
        return (process.returncode == 0, process.stdout + process.stderr)
    except Exception as e:
        return (False, str(e))

def run_script_realtime(cmd_list, log_container):
    """Runs a script and streams output to a Streamlit container in real-time."""
    try:
        if cmd_list[0] == "python":
            cmd_list[0] = sys.executable
        
        process = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            shell=(sys.platform == "win32"),
            bufsize=1
        )
        
        full_output = ""
        for line in iter(process.stdout.readline, ""):
            full_output += line
            log_container.code(full_output)
            
        process.wait()
        return (process.returncode == 0, full_output)
    except Exception as e:
        return (False, str(e))

def get_applications():
    md_path = 'data/applications.md'
    if not os.path.exists(md_path): return []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        rows = re.findall(r'\| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|', content)
        if len(rows) < 2: return []
        data = []
        for r in rows[2:]:
            jd_path = ""
            if '(' in r[4]:
                jd_path = re.search(r'\((.*?)\)', r[4]).group(1)
            else:
                jd_path = r[4].strip()
            
            data.append({
                "Role": r[0].strip(),
                "Company": r[1].strip(),
                "Status": r[2].strip(),
                "Files": re.search(r'\((.*?)\)', r[3]).group(1) if '(' in r[3] else r[3],
                "JD": jd_path,
                "Post-Mortem": r[5].strip()
            })
        
        active = [a for a in data if "Rejected" not in a['Status']]
        rejected = [a for a in data if "Rejected" in a['Status']]
        return active + rejected
    except: return []

def update_application_status(role_name, new_status):
    md_path = 'data/applications.md'
    if not os.path.exists(md_path): return
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"| {role_name} |"):
            parts = line.split("|")
            if len(parts) >= 4:
                parts[3] = f" {new_status} "
            new_lines.append("|".join(parts))
        else:
            new_lines.append(line)
            
    with open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def get_lesson_for_role(role_name):
    lessons_path = 'docs/solutions/rejection_lessons.md'
    if not os.path.exists(lessons_path): return "To be learnt"
    try:
        with open(lessons_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.search(rf'## Rejection Analysis: {re.escape(role_name)}.*?-\s\*\*Lesson\*\*:\s(.*?)\n', content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "To be learnt"
    except:
        return "To be learnt"

def log_application_to_excel(company, title, url):
    excel_path = 'data/tracking.xlsx'
    os.makedirs('data', exist_ok=True)
    
    new_entry = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Company": company,
        "Role": title,
        "URL": url,
        "Status": "Applied"
    }
    
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path)
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        except:
            df = pd.DataFrame([new_entry])
    else:
        df = pd.DataFrame([new_entry])
        
    df.to_excel(excel_path, index=False)

def launch_background_task(company, title, jd_text, url=""):
    safe_title = "".join(x for x in title if x.isalnum())
    timestamp = int(time.time())
    task_id = f"{safe_title}_{timestamp}"
    
    jd_path = f"data/raw_jds/{task_id}.md"
    os.makedirs("data/raw_jds", exist_ok=True)
    with open(jd_path, "w", encoding="utf-8") as f: f.write(jd_text)
    
    output_path = f"data/tailored_outputs/{safe_title}/CV.tex"
    log_path = f"data/logs/{task_id}.log"
    os.makedirs("data/logs", exist_ok=True)
    
    cmd = [
        sys.executable, "scripts/background_tailor.py",
        "data/master_cv.md", jd_path, output_path, log_path
    ]
    
    process = subprocess.Popen(cmd, start_new_session=True)
    
    task_info = {
        "id": task_id,
        "pid": process.pid,
        "company": company,
        "role": title,
        "url": url,
        "log_path": log_path,
        "status": "Running",
        "start_time": datetime.now().strftime("%H:%M:%S")
    }
    
    if 'background_tasks' not in st.session_state:
        st.session_state.background_tasks = {}
    
    st.session_state.background_tasks[task_id] = task_info
    return task_id

# --- PAGES ---

def page_find_jobs():
    st.header("Strategic Discovery")
    st.write("Scan career portals of Tier-1 German engineering and tech firms.")
    
    if st.button("Initialize Search"):
        log_container = st.empty()
        with st.status("Accessing career sites...") as status:
            success, output = run_script_realtime(["python", "scripts/search_jobs_gemini.py"], log_container)
            if success:
                status.update(label="Search complete!", state="complete", expanded=False)
                st.rerun()
            else:
                status.update(label="Search failed!", state="error", expanded=True)
                st.code(output)

    if os.path.exists('data/jobs_found.json'):
        with open('data/jobs_found.json', 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        for i, job in enumerate(jobs):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"### {job['company']}")
                c1.markdown(f"**{job['title']}** | {job.get('location', 'Germany')}")
                c1.write(job.get('snippet', ''))
                
                if 'url' in job and job['url']:
                    c2.link_button("Portal", job['url'], use_container_width=True)
                
                if c2.button("Tailor Suite", key=f"use_{i}", use_container_width=True):
                    launch_background_task(job['company'], job['title'], job.get('snippet', ''), job.get('url', ''))
                    st.toast(f"Launched tailoring for {job['title']}", icon="🚀")
                    time.sleep(1)
                    st.rerun()

def page_active_operations():
    st.header("Active Operations")
    st.write("Monitor parallel tailoring missions in real-time.")
    
    if 'background_tasks' not in st.session_state or not st.session_state.background_tasks:
        st.info("No active operations found.")
        return

    for task_id, task in list(st.session_state.background_tasks.items()):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            
            # Check status via PID
            is_running = psutil.pid_exists(task['pid'])
            if is_running:
                try:
                    p = psutil.Process(task['pid'])
                    if p.status() == psutil.STATUS_ZOMBIE:
                        is_running = False
                except:
                    is_running = False

            if not is_running:
                if os.path.exists(task['log_path']):
                    with open(task['log_path'], 'r', encoding='utf-8') as f:
                        log_content = f.read()
                        if "✅ Operation completed successfully." in log_content:
                            task['status'] = "Complete"
                        elif "❌" in log_content:
                            task['status'] = "Failed"
                        else:
                            task['status'] = "Interrupted"
                else:
                    task['status'] = "Unknown"

            status_color = "blue" if task['status'] == "Running" else "green" if task['status'] == "Complete" else "red"
            c1.markdown(f"### {task['role']} @ {task['company']}")
            c1.markdown(f"Status: :{status_color}[{task['status']}] | Started: {task['start_time']}")
            
            if os.path.exists(task['log_path']):
                with open(task['log_path'], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    tail = "".join(lines[-10:])
                    with c1.expander("View Logs"):
                        st.code(tail)
            
            if task['status'] == "Complete":
                if c2.button("Mark Applied", key=f"app_{task_id}", use_container_width=True):
                    log_application_to_excel(task['company'], task['role'], task['url'])
                    update_application_status(task['role'], "Applied")
                    del st.session_state.background_tasks[task_id]
                    st.toast("Application logged!", icon="✅")
                    st.rerun()
            
            if c2.button("Clear", key=f"clr_{task_id}", use_container_width=True):
                if task_id in st.session_state.background_tasks:
                    del st.session_state.background_tasks[task_id]
                st.rerun()

def page_my_applications():
    st.header("Executive Registry")
    apps = get_applications()
    
    if not apps:
        st.info("The registry is currently empty.")
        return

    total = len(apps)
    rejected_count = len([a for a in apps if "Rejected" in a['Status']])
    active_count = total - rejected_count
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Missions", total)
    c2.metric("Active", active_count)
    c3.metric("Concluded", rejected_count)
    st.divider()

    for i, app in enumerate(apps):
        with st.container(border=True):
            r1, r2, r3 = st.columns([3, 1, 1])
            r1.markdown(f"**{app['Role']}** at **{app['Company']}**")
            
            is_rejected = "Rejected" in app['Status']
            status_label = "Concluded" if is_rejected else "Active"
            r2.write(f"Status: {status_label}")
            
            if not is_rejected:
                if r3.button("Conclude", key=f"rej_{i}"):
                    update_application_status(app['Role'], "Rejected")
                    with st.spinner(f"Analyzing mission conclusion for {app['Role']}..."):
                        success, output = run_script(["python", "scripts/analyze_rejection.py", app['Role']])
                        if success:
                            st.toast(f"✅ Neural feedback loop complete for {app['Role']}.", icon="🧠")
                        else:
                            st.toast(f"⚠️ Learning interrupted for {app['Role']}.", icon="❌")
                    time.sleep(1)
                    st.rerun()
            else:
                if r3.button("Re-learn", key=f"relearn_{i}"):
                    with st.spinner(f"Re-analyzing failure patterns for {app['Role']}..."):
                        success, output = run_script(["python", "scripts/analyze_rejection.py", app['Role']])
                        if success:
                            st.toast(f"✅ Strategy updated based on {app['Role']}.", icon="🧠")
                        else:
                            st.toast(f"❌ Failed to extract new lessons.", icon="⚠️")
                    st.rerun()
            
            sr1, sr2, sr3 = st.columns([3, 1, 1])
            if is_rejected:
                lesson = get_lesson_for_role(app['Role'])
                sr1.info(f"Strategic Insight: {lesson}")
            
            if sr2.button("Files", key=f"dir_{i}"):
                abs_path = os.path.abspath(app['Files'])
                if os.path.exists(abs_path):
                    st.toast("Opening secure archives...", icon="📁")
                    os.startfile(abs_path)
            
            if sr3.button("Network", key=f"net_{i}"):
                st.session_state.net_role = app['Role']
                st.session_state.net_company = app['Company']
                st.session_state.nav = "Networking"
                st.rerun()

def page_tailor():
    st.header("Precision Tailoring")
    
    if not check_dependency("pdflatex"):
        st.warning("⚠️ **pdflatex** not found. PDF compilation will be skipped.")

    title = st.text_input("Role Designation", value=st.session_state.get('target_title', ''))
    company = st.text_input("Company", value=st.session_state.get('target_company', ''))
    jd = st.text_area("Job Description", value=st.session_state.get('target_jd', ''), height=300)
    
    if st.button("Trigger Background Tailoring"):
        if not title or not jd or not company:
            st.error("Incomplete mission parameters. Title, Company, and JD are required.")
            return
            
        task_id = launch_background_task(company, title, jd)
        st.success(f"Operation {task_id} launched in background.")
        st.session_state.nav = "Active Operations"
        st.rerun()

def page_networking():
    role = st.session_state.get('net_role', '')
    company = st.session_state.get('net_company', '')
    
    st.header("Relationship Intelligence")
    if not role or not company:
        st.info("Select an application from the Registry to initialize networking.")
        return

    st.subheader(f"Mapping {company}")
    st.write(f"Objective: Identify hiring personas for **{role}**.")
    
    if st.button("Search Key Contacts"):
        with st.status("Scanning LinkedIn & Career Portals...") as status:
            success, output = run_script(["python", "scripts/find_contacts_gemini.py", company, role])
            if success:
                status.update(label="Contacts mapped!", state="complete", expanded=False)
            else:
                status.update(label="Search failed!", state="error", expanded=True)
                st.code(output)

    safe_title = "".join(x for x in role if x.isalnum())
    outreach_path = f"data/tailored_outputs/{safe_title}_Outreach.json"
    if os.path.exists(outreach_path):
        with open(outreach_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for person in data.get('contacts', []):
            with st.container(border=True):
                st.markdown(f"### {person['name']}")
                st.write(f"**{person['title']}**")
                st.write(f"LinkedIn: {person.get('url', 'N/A')}")
                
                with st.expander("Outreach Templates"):
                    st.write("**Cold Email**")
                    st.code(person.get('email_draft', ''))
                    st.write("**LinkedIn Invite**")
                    st.code(person.get('linkedin_invite', ''))

def page_lessons():
    st.header("Intelligence Repository")
    t1, t2 = st.tabs(["Global Strategy", "Mission Archives"])
    
    with t1:
        if st.button("Synthesize Strategy"):
            with st.status("Analyzing rejection patterns..."):
                run_script(["python", "scripts/synthesize_master_lesson.py"])
                st.rerun()
        path = 'docs/solutions/master_rejection_lesson.md'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                st.markdown(f.read())

    with t2:
        path = 'docs/solutions/rejection_lessons.md'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                st.markdown(f.read())

def main():
    if "nav" not in st.session_state: st.session_state.nav = "Find Jobs"
    if 'background_tasks' not in st.session_state: st.session_state.background_tasks = {}

    with st.sidebar:
        st.title("ARBEITLOS 2.0")
        st.session_state.nav = st.radio("Menu", 
            ["Find Jobs", "Active Operations", "My Applications", "Tailor CV", "Networking", "Lessons learned"],
            label_visibility="collapsed")
        
        active_count = sum(1 for t in st.session_state.background_tasks.values() if t['status'] == "Running")
        ready_count = sum(1 for t in st.session_state.background_tasks.values() if t['status'] == "Complete")
        
        if active_count > 0 or ready_count > 0:
            st.markdown("---")
            st.header("⚙️ Status")
            if active_count > 0:
                st.info(f"🏃 {active_count} Operations Running")
            if ready_count > 0:
                st.success(f"✅ {ready_count} Suites Ready")
            if st.button("Go to Operations", use_container_width=True):
                st.session_state.nav = "Active Operations"
                st.rerun()
        
    if st.session_state.nav == "Find Jobs": page_find_jobs()
    elif st.session_state.nav == "Active Operations": page_active_operations()
    elif st.session_state.nav == "My Applications": page_my_applications()
    elif st.session_state.nav == "Tailor CV": page_tailor()
    elif st.session_state.nav == "Networking": page_networking()
    elif st.session_state.nav == "Lessons learned": page_lessons()

if __name__ == "__main__":
    main()
