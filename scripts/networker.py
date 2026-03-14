import os
import requests
import subprocess
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def get_outreach(company_domain, job_title, tailored_resume_path):
    # 1. Hunter.io API to find email format
    hunter_key = os.getenv("HUNTER_API_KEY")
    if not hunter_key:
        print("HUNTER_API_KEY not found in environment variables. Skipping domain search.")
        email_pattern = "{first}.{last}"
    else:
        domain_search = f"https://api.hunter.io/v2/domain-search?domain={company_domain}&api_key={hunter_key}"
        try:
            res = requests.get(domain_search).json()
            email_pattern = res.get('data', {}).get('pattern', '{first}.{last}')
            print(f"Company {company_domain} uses email pattern: {email_pattern}")
        except Exception as e:
            print(f"Error fetching email pattern: {e}. Defaulting to '{first}.{last}'.")
            email_pattern = "{first}.{last}"
    
    # 2. Use Gemini CLI to draft messages
    print(f"Drafting outreach messages for {company_domain}...")
    
    # We should use read_file to get the resume content first
    with open(tailored_resume_path, "r", encoding="utf-8") as f:
        resume_content = f.read()

    # Define the prompt for Gemini to draft outreach
    prompt = (
        f"Based on the tailored resume below, draft a highly customized cold email and a 300-character LinkedIn "
        f"connection request to the Hiring Manager or Team Lead for the {job_title} role at {company_domain}. "
        f"The company's email pattern is {email_pattern}. Ensure the tone is professional, shows deep interest "
        f"in their specific tech stack, and highlights 1 key achievement from the resume.\n\n"
        f"ALSO: Generate a LinkedIn search query URL to find the right person for this role (e.g., 'site:linkedin.com {company_domain} Hiring Manager {job_title}').\n\n"
        f"Tailored Resume:\n{resume_content}"
    )
    
    # Using 'gemini' as the command (assuming it's installed as a CLI)
    try:
        # Pass the prompt to gemini (make sure to handle potential issues with shell escaping)
        # Use shell=True for Windows to find .cmd/.ps1 binaries
        cmd = ["gemini", "--prompt", "-"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
        output, stderr = process.communicate(input=prompt)
        
        if process.returncode != 0:
            print(f"Gemini CLI failed for outreach: {stderr}")
            return
        
        output_path = f"data/tailored_outputs/{company_domain}_outreach.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
            
        print(f"Outreach messages saved to {output_path}.")
    except Exception as e:
        print(f"Error calling Gemini CLI for outreach: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python networker.py <company_domain> <job_title> <tailored_resume_path>")
        sys.exit(1)
    get_outreach(sys.argv[1], sys.argv[2], sys.argv[3])
