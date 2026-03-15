import os
import requests
import subprocess
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def get_outreach(company_domain, job_title, tailored_resume_path, explicit_output_path=None):
    # ... (existing Hunter logic) ...
    
    # ... (existing Gemini prompt logic) ...
    
    # Using 'gemini' as the command
    try:
        cmd = ["gemini", "--prompt", "-"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
        output, stderr = process.communicate(input=prompt)
        
        if process.returncode != 0:
            print(f"Gemini CLI failed for outreach: {stderr}")
            return
        
        output_path = explicit_output_path if explicit_output_path else f"data/tailored_outputs/{company_domain}_outreach.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
            
        print(f"Outreach messages saved to {output_path}.")
    except Exception as e:
        print(f"Error calling Gemini CLI for outreach: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python networker.py <company_domain> <job_title> <tailored_resume_path> [output_path]")
        sys.exit(1)
    
    out_path = sys.argv[4] if len(sys.argv) > 4 else None
    get_outreach(sys.argv[1], sys.argv[2], sys.argv[3], out_path)
