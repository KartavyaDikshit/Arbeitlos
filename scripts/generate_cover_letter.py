import os
import sys
import subprocess

def generate_cl(master_cv_path, jd_path, output_path):
    with open(master_cv_path, "r", encoding="utf-8") as f:
        master_cv = f.read()
    
    with open(jd_path, "r", encoding="utf-8") as f:
        jd = f.read()

    system_prompt = (
        "You are an expert career coach writing a formal, short, and highly human-sounding cover letter. "
        "Keep it under 3 paragraphs. Emphasize the candidate's Master's at FAU and alignment with the company's technical stack. "
        "Do not use robotic phrasing. Output ONLY the markdown text of the cover letter."
    )

    prompt = (
        f"Master CV:\n{master_cv}\n\n"
        f"Job Description:\n{jd}\n\n"
        f"Write the cover letter for Kartavya Niraj Dikshit."
    )

    full_prompt = f"{system_prompt}\n\n{prompt}"

    cmd = ["gemini", "--prompt", "-"]
    try:
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
        raw_output, stderr = process.communicate(input=full_prompt)
        
        if process.returncode != 0:
            print(f"Gemini CLI failed: {stderr}")
            return False
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(raw_output.strip())
        return True
    except Exception as e:
        print(f"Error generating CL: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_cover_letter.py <master_cv> <jd> <output_path>")
        sys.exit(1)
    generate_cl(sys.argv[1], sys.argv[2], sys.argv[3])
