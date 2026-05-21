import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import run_gemini_cli

load_dotenv()

def run_gemini_tailor(master_cv_path, jd_path, prompt_path, output_path):
    """
    Standard tailoring entry point refactored for the new API.
    """
    with open(master_cv_path, 'r', encoding='utf-8') as f:
        master_cv = f.read()
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd = f.read()
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nCONTEXT:\nMaster Resume: {master_cv}\n\nTarget Job Description: {jd}"

    print(f"Executing Gemini Pro for {output_path}...")
    result = run_gemini_cli(full_prompt, model='gemini-3.1-pro-preview', timeout=400)

    if result:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Saved: {output_path}")
    else:
        print("Error: Gemini returned no output.")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python scripts/tailor_with_api.py <master_cv> <jd> <prompt> <output>")
        sys.exit(1)
    run_gemini_tailor(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
