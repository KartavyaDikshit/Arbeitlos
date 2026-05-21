import os
import json
import subprocess
import time
import sys
from dotenv import load_dotenv
from utils import run_gemini_cli

load_dotenv()

CACHE_FILE = "data/company_contacts.json"

def load_company_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def find_hiring_manager(company_name, job_title, job_url="N/A", timeout=60):
    """
    Uses Gemini CLI to identify the hiring manager. 
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
    
    raw_output = run_gemini_cli(search_query, timeout=timeout, use_grounding=True)
    if raw_output:
        try:
            text = raw_output.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            parsed = json.loads(text.strip())
            if parsed.get('name') and str(parsed.get('name')).lower() != "null":
                contact_info = parsed
        except Exception as e:
            print(f"Failed to parse contact info: {e}")

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
    
    raw_outreach = run_gemini_cli(outreach_query, timeout=timeout)
    if raw_outreach:
        try:
            text2 = raw_outreach.strip()
            if "```json" in text2:
                text2 = text2.split("```json")[1].split("```")[0]
            elif "```" in text2:
                text2 = text2.split("```")[1].split("```")[0]
            
            outreach_data = json.loads(text2.strip())
            contact_info.update(outreach_data)
        except Exception as e:
            print(f"Failed to parse outreach data: {e}")
            contact_info["cold_email"] = f"Dear {contact_info['name']},\n\nI am following up on my application for {job_title}..."
            contact_info["linkedin_invite"] = f"Hi {contact_info['name']}, I applied for the {job_title} role at {company_name} and would love to connect."
    else:
        contact_info["cold_email"] = f"Dear {contact_info['name']},\n\nI am following up on my application for {job_title}..."
        contact_info["linkedin_invite"] = f"Hi {contact_info['name']}, I applied for the {job_title} role at {company_name} and would love to connect."

    # Save output to job-specific directory
    safe_title = "".join(x for x in job_title if x.isalnum())
    job_dir = os.path.join("data", "tailored_outputs", safe_title)
    if not os.path.exists(job_dir):
        # Alternative save location if specific job dir not found
        output_path = os.path.join("data", "tailored_outputs", f"{safe_title}_Outreach.json")
    else:
        output_path = os.path.join(job_dir, "Outreach.json")
        # Also copy to root of tailored_outputs for easier matching in app.py if needed
        alt_path = os.path.join("data", "tailored_outputs", f"{safe_title}_Outreach.json")
        with open(alt_path, "w", encoding="utf-8") as f:
            json.dump({"contacts": [contact_info]}, f, indent=4, ensure_ascii=False)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"contacts": [contact_info]}, f, indent=4, ensure_ascii=False)
        
    print(f"Saved: {output_path}")
    return contact_info

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/find_contacts_gemini.py <company_name> <job_title> [job_url]")
    else:
        company = sys.argv[1]
        title = sys.argv[2]
        url = sys.argv[3] if len(sys.argv) > 3 else "N/A"
        find_hiring_manager(company, title, url)
