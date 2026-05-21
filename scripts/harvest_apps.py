import os
import json
import re
import subprocess

def run_gemini_extract(jd_text):
    """Uses Gemini to extract company and title from JD text."""
    prompt = (
        f"Extract the Company Name and Job Title from the following job description:\n\n"
        f"{jd_text[:3000]}\n\n"
        f"Return ONLY a JSON object with keys: 'company', 'title'. "
        f"Example: {{\"company\": \"Siemens\", \"title\": \"Working Student AI\"}}"
    )
    try:
        cmd = 'gemini --prompt -'
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8', 
            shell=True
        )
        stdout, stderr = process.communicate(input=prompt, timeout=60)
        
        # Clean up stdout from potential diagnostic messages
        if "MCP issues detected" in stdout:
            lines = stdout.splitlines()
            stdout = "\n".join([l for l in lines if "MCP issues detected" not in l]).strip()
            
        json_match = re.search(r'\{.*\}', stdout, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except subprocess.TimeoutExpired:
        print("Gemini extract timed out.")
        process.kill()
        return None
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None

def get_safe_title(title):
    # Remove characters that cause issues in paths but keep it readable
    return re.sub(r'[^a-zA-Z0-9]', '', title)

def harvest_applications():
    outputs_dir = 'data/tailored_outputs'
    jds_dir = 'data/raw_jds'
    registry_file = 'data/applications.md'
    
    applications = []
    
    if not os.path.exists(outputs_dir):
        print(f"Error: {outputs_dir} not found.")
        return

    # Pre-cache JD contents for matching
    jd_cache = {}
    if os.path.exists(jds_dir):
        for f in os.listdir(jds_dir):
            if f.endswith('.md'):
                path = os.path.join(jds_dir, f)
                try:
                    with open(path, 'r', encoding='utf-8') as jdf:
                        jd_cache[path] = jdf.read()
                except: pass

    # Scan tailored_outputs
    for item in os.listdir(outputs_dir):
        item_path = os.path.join(outputs_dir, item)
        if os.path.isdir(item_path):
            role_name = item
            jd_path = "Not Found"
            
            # 1. Direct filename match
            check_path = os.path.join(jds_dir, f"{role_name}.md")
            if os.path.exists(check_path):
                jd_path = check_path
            else:
                # 2. Safe title match
                safe = get_safe_title(role_name)
                check_path = os.path.join(jds_dir, f"{safe}.md")
                if os.path.exists(check_path):
                    jd_path = check_path
                else:
                    # 3. Content-based match (search role name in JD text)
                    for path, content in jd_cache.items():
                        # Simple fuzzy match: if 70% of words in role_name are in the JD first 500 chars
                        words = [w for w in re.split(r'[^a-zA-Z]', role_name) if len(w) > 3]
                        if words:
                            matches = sum(1 for w in words if w.lower() in content[:1000].lower())
                            if matches / len(words) >= 0.7:
                                jd_path = path
                                break
            
            status = "Tailored"
            company = "Unknown"

            # Check existing registry for status/company
            if os.path.exists(registry_file):
                with open(registry_file, 'r', encoding='utf-8') as f:
                    reg_content = f.read()
                    # Check for Rejected status
                    if re.search(rf'\| {re.escape(role_name)} \| .*? \| Rejected \|', reg_content):
                        status = "Rejected"
                    
                    # Try to extract existing company
                    comp_match = re.search(rf'\| {re.escape(role_name)} \| (.*?) \|', reg_content)
                    if comp_match and comp_match.group(1).strip() != "Unknown":
                        company = comp_match.group(1).strip()

            # If still Unknown, try Gemini extract
            if company == "Unknown" and jd_path != "Not Found":
                print(f"Extracting metadata for {role_name} from {os.path.basename(jd_path)}...")
                meta = run_gemini_extract(jd_cache[jd_path])
                if meta:
                    company = meta.get('company', 'Unknown')

            applications.append({
                "Role": role_name,
                "Company": company,
                "Status": status,
                "Tailored_Path": item_path.replace('\\', '/'),
                "JD_Path": jd_path.replace('\\', '/') if jd_path != "Not Found" else "Not Found"
            })

    # Write registry with strict UTF-8
    with open(registry_file, 'w', encoding='utf-8') as f:
        f.write("# Master Application Registry\n\n")
        f.write("| Role | Company | Status | Tailored Files | JD | Post-Mortem |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for app in applications:
            pm = "docs/solutions/rejection_lessons.md" if app['Status'] == "Rejected" else "N/A"
            pm_link = f"[Post-Mortem]({pm})" if pm != "N/A" else "[N/A](#)"
            f.write(f"| {app['Role']} | {app['Company']} | {app['Status']} | [View]({app['Tailored_Path']}) | [JD]({app['JD_Path']}) | {pm_link} |\n")

    print(f"Cleaned and harvested {len(applications)} applications into {registry_file}")

if __name__ == "__main__":
    harvest_applications()
