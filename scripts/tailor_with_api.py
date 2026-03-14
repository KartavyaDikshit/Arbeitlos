import os
import subprocess
import tempfile
import sys

def run_gemini_tailor(master_cv_path, jd_path, prompt_path, output_path):
    with open(master_cv_path, 'r', encoding='utf-8') as f:
        master_cv = f.read()
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd = f.read()
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    full_prompt = "SYSTEM INSTRUCTIONS:\n" + system_prompt + "\n\nCONTEXT:\nMaster Resume: " + master_cv + "\n\nTarget Job Description: " + jd

    # Use a temporary file to pass the prompt to gemini CLI
    tmp_path = "temp_prompt.txt"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(full_prompt)

    try:
        print(f"Executing Gemini for {output_path}...")
        # Try direct stdin feeding for the CLI with shell=True
        with open(tmp_path, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                'gemini', 
                input=f.read(), 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                shell=True
            )

        if result.stdout:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            print(f"Saved: {output_path}")
        else:
            print(f"Error from Gemini: {result.stderr}")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python tailor_with_api.py <master_cv> <jd> <prompt> <output>")
        sys.exit(1)
    run_gemini_tailor(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
