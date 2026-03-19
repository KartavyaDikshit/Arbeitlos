import os
import json
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "data/company_contacts.json"

def load_company_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def find_hiring_manager(job_url, company_name, job_title, job_dir, timeout=30):
    """
    Uses Gemini CLI to identify the hiring manager. 
    Saves into the job-specific directory.
    """
    cache = load_company_cache()
    
    search_query = (
        f"Find the likely hiring manager, HR contact, or team lead for the position '{job_title}' "
        f"at {company_name} (Job URL: {job_url}). "
        f"Search for LinkedIn profiles or team mentions. "
        f"Provide the results as a JSON object with: name, title, linkedin_url, email_guess, and team_context. "
        f"If you cannot find a specific individual, return 'null' for the fields. "
        f"Gib NUR den JSON-Block zurück."
    )

    print(f"Searching for hiring contacts at {company_name} (Max wait: {timeout}s)...")
    
    contact_info = None
    
    try:
        process = subprocess.Popen(
            ["gemini", "-e", "", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        
        try:
            stdout, stderr = process.communicate(input=search_query, timeout=timeout)
            if process.returncode == 0:
                text = stdout.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                parsed = json.loads(text.strip())
                if parsed.get('name') and parsed.get('name').lower() != "null":
                    contact_info = parsed
        except subprocess.TimeoutExpired:
            print(f"Discovery timed out. Falling back to general contact for {company_name}.")
            process.kill()
            
    except Exception as e:
        print(f"Discovery failed: {e}. Falling back to general contact.")

    if not contact_info:
        print(f"No specific contact found. Using general {company_name} recruitment info.")
        general = cache.get(company_name, {"general_email": "recruiting@company.com", "name": "Hiring Team"})
        contact_info = {
            "name": "Hiring Team",
            "title": f"{company_name} Recruitment",
            "linkedin_url": "N/A",
            "email_guess": general.get("general_email"),
            "team_context": f"General application follow-up for {company_name}"
        }

    # Outreach generation
    outreach_query = (
        f"Based on this contact: {json.dumps(contact_info)}, generate a professional cold email follow-up "
        f"for Kartavya Niraj Dikshit (FAU Data Science) and a 200-char LinkedIn invite. "
        f"Output as JSON with keys: 'cold_email', 'linkedin_invite'."
        f"Gib NUR den JSON-Block zurück."
    )
    
    try:
        process2 = subprocess.Popen(
            ["gemini", "-e", "", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout2, stderr2 = process2.communicate(input=outreach_query, timeout=15)
        
        if process2.returncode == 0:
            text2 = stdout2.strip()
            if "```json" in text2:
                text2 = text2.split("```json")[1].split("```")[0]
            elif "```" in text2:
                text2 = text2.split("```")[1].split("```")[0]
            
            outreach_data = json.loads(text2.strip())
            contact_info.update(outreach_data)
    except:
        contact_info["cold_email"] = f"Dear {contact_info['name']},\n\nI am following up on my application for {job_title}..."
        contact_info["linkedin_invite"] = f"Hi {contact_info['name']}, I applied for the {job_title} role at {company_name} and would love to connect."

    # Save output to job-specific directory
    output_path = os.path.join(job_dir, "Outreach.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(contact_info, f, indent=4, ensure_ascii=False)
        
    print(f"Saved: {output_path}")
    return contact_info

if __name__ == "__main__":
    pass
