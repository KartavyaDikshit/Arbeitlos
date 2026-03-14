import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

def tailor_lossless(master_cv_path, jd_path, output_path, system_prompt_path):
    with open(master_cv_path, "r", encoding="utf-8") as f:
        master_cv = f.read()
    
    with open(jd_path, "r", encoding="utf-8") as f:
        jd = f.read()
        
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # The prompt for Gemini passes the full LaTeX and the JD
    prompt = (
        f"Master CV (LaTeX):\n{master_cv}\n\n"
        f"Target Job Description:\n{jd}\n\n"
        f"Please generate the fully tailored LaTeX resume according to the system prompt instructions. "
        f"Remember to output ONLY valid LaTeX code."
    )

    # Combine system prompt and main prompt since --system is not supported in this version
    full_prompt = f"{system_prompt}\n\n{prompt}"

    print(f"Calling Gemini to generate tailored LaTeX resume...")
    # Using the 'gemini' CLI tool with stdin to avoid command line length limits
    cmd = ["gemini", "--prompt", "-"]
    try:
        # Pass the prompt via stdin
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
        raw_output, stderr = process.communicate(input=full_prompt)
        
        if process.returncode != 0:
            raise Exception(f"Gemini CLI failed with return code {process.returncode}: {stderr}")
        
        # Extract LaTeX code block if present
        latex_code = raw_output
        if "```latex" in raw_output:
            latex_code = raw_output.split("```latex")[1].split("```")[0].strip()
        elif "```" in raw_output:
            latex_code = raw_output.split("```")[1].split("```")[0].strip()
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        print(f"Tailored LaTeX saved to {output_path}")
        
        # Run pdflatex
        output_dir = os.path.dirname(output_path)
        print(f"Compiling PDF with pdflatex...")
        compile_cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, output_path]
        subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        print(f"PDF successfully generated in {output_dir}")
        
    except Exception as e:
        print(f"Error during tailoring or compilation: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tailor_resume_lossless.py <master_cv> <jd> <output_path>")
        sys.exit(1)
    tailor_lossless(sys.argv[1], sys.argv[2], sys.argv[3], "tailor_prompt.txt")