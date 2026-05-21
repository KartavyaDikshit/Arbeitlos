import os
import sys
import re
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import run_gemini_cli

# Load environment variables
load_dotenv()

def get_outreach(company_domain, job_title, tailored_resume_path, explicit_output_path=None):
    """
    Generates outreach messages using the upgraded Gemini API.
    """
    if not os.path.exists(tailored_resume_path):
        print(f"Error: Resume not found at {tailored_resume_path}")
        return

    with open(tailored_resume_path, 'r', encoding='utf-8', errors='ignore') as f:
        resume_content = f.read()

    prompt = f"""
    You are a Networking Specialist. 
    Based on this candidate's resume and target role, generate a high-conversion outreach strategy.
    
    Target: {job_title} at {company_domain}
    Candidate Resume: {resume_content[:4000]}
    
    TASKS:
    1. LinkedIn Invite (max 200 chars).
    2. Cold Email follow-up to HR/Hiring Manager.
    3. Custom 'In-Mail' message.
    
    FORMAT: Use Markdown.
    """
    
    print(f"Generating outreach strategy for {company_domain}...")
    output = run_gemini_cli(prompt, model='gemini-3.1-pro-preview')
    
    if output:
        output_path = explicit_output_path if explicit_output_path else f"data/tailored_outputs/{company_domain}_outreach.md"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
            
        print(f"Outreach messages saved to {output_path}.")
    else:
        print("Error: Failed to generate outreach.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/networker.py <company_domain> <job_title> <tailored_resume_path> [output_path]")
        sys.exit(1)
    
    out_path = sys.argv[4] if len(sys.argv) > 4 else None
    get_outreach(sys.argv[1], sys.argv[2], sys.argv[3], out_path)
