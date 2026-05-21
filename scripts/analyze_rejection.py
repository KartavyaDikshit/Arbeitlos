import os
import sys
import subprocess
import re
import difflib
from utils import run_gemini_cli

def analyze_rejection(role_name):
    outputs_dir = 'data/tailored_outputs'
    jds_dir = 'data/raw_jds'
    lessons_file = 'docs/solutions/rejection_lessons.md'
    registry_file = 'data/applications.md'
    
    app_dir = os.path.join(outputs_dir, role_name)
    if not os.path.exists(app_dir):
        # Try to find folder that matches or clean name
        for item in os.listdir(outputs_dir):
            if item.lower() in role_name.lower() or role_name.lower() in item.lower():
                app_dir = os.path.join(outputs_dir, item)
                break

    if not os.path.exists(app_dir):
        print(f"Error: Application directory {app_dir} not found.")
        return

    # Files to analyze
    cv_path = os.path.join(app_dir, "CV.tex")
    cl_path = os.path.join(app_dir, "Cover_Letter.tex")
    
    # ADVANCED JD SEARCH:
    # 1. Exact match
    jd_path = os.path.join(jds_dir, f"{role_name}.md")
    
    # 2. Content search if file not found
    if not os.path.exists(jd_path):
        print(f"JD file {role_name}.md not found. Searching content...")
        found_jd = False
        # Search for unique keywords from the role name in all JDs
        keywords = [w for w in re.split(r'[^a-zA-Z]', role_name) if len(w) > 4]
        if not keywords: keywords = [role_name[:10]]
        
        for f in os.listdir(jds_dir):
            if f.endswith('.md'):
                path = os.path.join(jds_dir, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as jdf:
                        content = jdf.read().lower()
                        # If 2+ keywords match or the full role name string (partial)
                        matches = sum(1 for k in keywords if k.lower() in content)
                        if matches >= 2 or (len(keywords) == 1 and keywords[0].lower() in content):
                            jd_path = path
                            found_jd = True
                            print(f"Matched JD by content: {f}")
                            break
                except: continue
        
        if not found_jd:
            # 3. Last resort fallback
            print("No JD content match found.")
    
    content_to_analyze = ""
    if os.path.exists(jd_path):
        with open(jd_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_to_analyze += f"### JOB DESCRIPTION:\n{f.read()}\n\n"
    
    if os.path.exists(cv_path):
        with open(cv_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_to_analyze += f"### TAILORED CV (LaTeX):\n{f.read()}\n\n"

    if os.path.exists(cl_path):
        with open(cl_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_to_analyze += f"### TAILORED COVER LETTER (LaTeX):\n{f.read()}\n\n"

    if not content_to_analyze:
        print("Error: No content to analyze.")
        return

    # Use Gemini CLI to analyze
    prompt = f"""
    You are a Senior Hiring Manager in the German Tech market.
    We applied for this role and were REJECTED. 
    Analyze the Job Description against the Tailored CV and Cover Letter.
    
    Identify:
    1. CRITICAL GAPS: What key requirements from the JD are missing or weak in the CV?
    2. OVER-HALLUCINATION: Did the AI add projects that seem unrealistic?
    3. CULTURAL MISMATCH: Is the tone off?
    4. REJECTION LESSON: One concise lesson.
    
    FORMAT YOUR RESPONSE AS:
    ## Rejection Analysis: {role_name}
    - **Lesson**: [The concise lesson]
    - **Details**: [Brief analysis]
    ---
    
    {content_to_analyze}
    """
    
    output = run_gemini_cli(prompt, model='gemini-3.1-pro-preview')
    if not output:
        print(f"Error running Gemini for {role_name}")
        return

    clean_stdout = re.sub(r'<[a-z]+.*?>', '', output, flags=re.IGNORECASE)
    clean_stdout = re.sub(r'</[a-z]+>', '', clean_stdout, flags=re.IGNORECASE)

    with open(lessons_file, 'a', encoding='utf-8') as f:
        f.write("\n" + clean_stdout + "\n")
    
    if os.path.exists(registry_file):
        with open(registry_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"| {role_name} |"):
                parts = line.split("|")
                if len(parts) >= 4: parts[3] = " Rejected "
                if len(parts) >= 7: parts[6] = " [Post-Mortem](docs/solutions/rejection_lessons.md) "
                new_lines.append("|".join(parts))
            else:
                new_lines.append(line)
        with open(registry_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    print(f"Analysis complete for {role_name}. Lesson saved.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_rejection.py <role_name>")
    else:
        analyze_rejection(sys.argv[1])
