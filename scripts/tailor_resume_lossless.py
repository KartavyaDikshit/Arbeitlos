import os
import sys
import time
import subprocess
import json
import re
from dotenv import load_dotenv

load_dotenv()

def run_gemini_cli(prompt, timeout=300):
    """Runs the gemini CLI with the given prompt and returns the output."""
    try:
        process = subprocess.Popen(
            ["gemini", "-e", "", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout, stderr = process.communicate(input=prompt, timeout=timeout)
        
        if process.returncode != 0:
            print(f"Gemini CLI Error: {stderr}")
            return None
        return stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Gemini CLI Timeout after {timeout}s")
        process.kill()
        return None
    except Exception as e:
        print(f"Error running Gemini CLI: {e}")
        return None

def scrutinize_resume(jd, latex_code):
    """Ruthlessly scores the resume and provides feedback."""
    print("Scrutinizing tailored resume against JD...")
    prompt = (
        f"You are a ruthless Senior Technical Recruiter at a top-tier tech company. "
        f"Your job is to find reasons to REJECT this candidate. "
        f"Scrutinize this tailored resume against the provided Job Description.\n\n"
        f"JD:\n{jd}\n\n"
        f"Resume LaTeX:\n{latex_code}\n\n"
        f"CRITICAL EVALUATION CRITERIA:\n"
        f"1. KEYWORD DENSITY: Does it have all technical terms from the JD? List missing ones.\n"
        f"2. GOOGLE XYZ FORMAT: Are bullet points quantified? (Accomplished [X] as measured by [Y], by doing [Z]).\n"
        f"3. RELEVANCE: Do the projects directly solve problems mentioned in the JD?\n"
        f"4. SUMMARY: Is it a generic objective or a powerful, value-driven profile?\n\n"
        f"SCORING RUBRIC:\n"
        f"- 0-5: Generic, missing key skills, weak bullets.\n"
        f"- 6-8: Good, but needs more impact or specific keywords.\n"
        f"- 9-10: Perfect alignment, highly quantified, non-rejectable.\n\n"
        f"TASK: Return ONLY a JSON object with keys: 'score' (float) and 'feedback' (detailed string).\n"
        f"JSON output should be clean without any extra text."
    )
    raw = run_gemini_cli(prompt)
    if not raw: return {"score": 0, "feedback": "Failed to get feedback."}
    
    try:
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {"score": 5, "feedback": "Could not parse recruiter feedback."}
    except Exception as e:
        print(f"Scrutinizer Error: {e}")
        return {"score": 5, "feedback": f"Error parsing feedback: {str(e)}"}

def retailor_resume(master_cv, jd, latex_code, feedback, system_prompt):
    """Applies feedback to the resume to reach the next level."""
    print("Applying feedback for re-tailoring...")
    prompt = (
        f"{system_prompt}\n\n"
        f"RECRUITER FEEDBACK (ADDRESS ALL POINTS):\n{feedback}\n\n"
        f"CURRENT RESUME VERSION:\n{latex_code}\n\n"
        f"MASTER CV DATA (SOURCE FOR NEW DETAILS):\n{master_cv}\n\n"
        f"TASK:\n"
        f"Rewrite the LaTeX code to be a 10/10 match. "
        f"1. Integrate all missing keywords identified in feedback.\n"
        f"2. Upgrade every bullet point to follow the Google XYZ format strictly.\n"
        f"3. If projects are weak, find relevant details in the Master CV and expand them to fit the JD context.\n"
        f"4. Ensure the LaTeX remains valid and compilable.\n\n"
        f"RETURN ONLY THE UPDATED LATEX CODE WRAPPED IN ```latex BLOCKS."
    )
    raw = run_gemini_cli(prompt, timeout=400)
    if not raw: return latex_code
    
    if "```latex" in raw:
        return raw.split("```latex")[1].split("```")[0].strip()
    return raw.strip()

def identify_gaps(jd, latex_code):
    """Identifies specific missing keywords or terminology gaps from the JD."""
    print("Analyzing for specific terminology gaps...")
    prompt = (
        f"Identify specific missing keywords, methodologies, or stakeholder-related terminology from the Job Description "
        f"that are NOT explicitly present in the current tailored resume, but could be added based on the candidate's background.\n\n"
        f"JD:\n{jd}\n\n"
        f"CURRENT RESUME:\n{latex_code}\n\n"
        f"TASK:\n"
        f"List exactly 2-3 high-impact additions. "
        f"Example: 'The keyword Agile is missing. Action: Add Agile/Scrum to skills.' "
        f"Example: 'Stakeholder requirements terminology is missing. Action: Tweak freelance points to mention translating requirements.'\n\n"
        f"Return ONLY a plain text list of these actions. No emojis."
    )
    raw = run_gemini_cli(prompt)
    return raw.strip() if raw else ""

def integrate_gaps(master_cv, jd, latex_code, gaps, system_prompt):
    """Final pass to weave in missing terminology while retaining Master CV depth."""
    print("Integrating identified gaps and maximizing info retention...")
    prompt = (
        f"{system_prompt}\n\n"
        f"SPECIFIC GAPS TO FILL:\n{gaps}\n\n"
        f"CURRENT RESUME VERSION:\n{latex_code}\n\n"
        f"MASTER CV DATA (SOURCE FOR DEPTH):\n{master_cv}\n\n"
        f"TARGET JD:\n{jd}\n\n"
        f"FINAL TASK:\n"
        f"1. Weave the SPECIFIC GAPS terminology into the resume naturally.\n"
        f"2. Ensure MAXIMUM information retention from the Master CV. Do not over-summarize. "
        f"If the Master CV has technical details or specific projects that were shortened, expand them back "
        f"while maintaining the JD alignment.\n"
        f"3. Ensure every section feels substantial and technically 'dense'.\n"
        f"4. The LaTeX must remain valid.\n\n"
        f"RETURN ONLY THE FINAL, PERFECTED LATEX CODE WRAPPED IN ```latex BLOCKS."
    )
    raw = run_gemini_cli(prompt, timeout=400)
    if not raw: return latex_code
    
    if "```latex" in raw:
        return raw.split("```latex")[1].split("```")[0].strip()
    return raw.strip()

def compile_latex(tex_path, job_dir):
    """Compiles a LaTeX file to PDF and handles standard error cases."""
    print(f"Compiling: {os.path.basename(tex_path)}...")
    
    # Delete old PDF to avoid false positives on existence check
    old_pdf = tex_path.replace(".tex", ".pdf")
    if os.path.exists(old_pdf):
        os.remove(old_pdf)
        
    compile_cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", job_dir, tex_path]
    
    # Run twice for references/formatting stability
    subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    return os.path.exists(old_pdf)

def tailor_lossless(master_cv_path, jd_path, output_tex_path, system_prompt_path):
    """
    Tailors a resume and cover letter into LaTeX format, polishes them, and compiles them to PDF.
    """
    with open(master_cv_path, "r", encoding="utf-8") as f:
        master_cv = f.read()
    
    with open(jd_path, "r", encoding="utf-8") as f:
        jd = f.read()
        
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Determine the job-specific directory
    job_dir = os.path.abspath(os.path.dirname(output_tex_path))
    if not os.path.exists(job_dir):
        os.makedirs(job_dir, exist_ok=True)

    # Phase 1: Tailored LaTeX Resume
    print(f"Phase 1: Generating Initial Tailored Resume...")
    resume_prompt = (
        f"{system_prompt}\n\n"
        f"Master CV Content:\n{master_cv}\n\n"
        f"Target Job Description:\n{jd}\n\n"
        f"TASK: Generate the fully tailored LaTeX resume code. "
        f"STRICTLY FOLLOW 'RESUME-SPECIFIC CONSTRAINTS'. Ignore Cover Letter instructions for this task."
    )
    
    resume_raw = run_gemini_cli(resume_prompt)
    if not resume_raw: return False

    # Extract LaTeX
    latex_code = ""
    if "```latex" in resume_raw:
        latex_code = resume_raw.split("```latex")[1].split("```")[0].strip()
    elif "```" in resume_raw:
        parts = resume_raw.split("```")
        for part in parts:
            if "\\documentclass" in part:
                latex_code = part.strip()
                break
    if not latex_code: latex_code = resume_raw.strip()

    # Phase 1.5: Iterative Feedback & Polishing Loop
    print(f"Phase 1.5: Entering Iterative Scrutiny Loop...")
    max_iterations = 3
    current_iteration = 0
    target_score = 9.0
    
    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"Loop {current_iteration}/{max_iterations}: Evaluating resume...")
        
        scrutiny_result = scrutinize_resume(jd, latex_code)
        score = scrutiny_result.get("score", 0)
        feedback = scrutiny_result.get("feedback", "No feedback provided.")
        
        print(f"Current Scrutinizer Score: {score}/10")
        
        if score > target_score:
            print(f"Target score reached ({score} > {target_score}). Proceeding to compilation.")
            break
        
        if current_iteration < max_iterations:
            print(f"Score {score} is below target {target_score}. Re-tailoring based on feedback...")
            latex_code = retailor_resume(master_cv, jd, latex_code, feedback, system_prompt)
            time.sleep(10) # Prevent rate limiting/give breather
        else:
            print(f"Reached max iterations ({max_iterations}). Proceeding with current version (Score: {score}).")

    # Phase 1.6: Final Gap Filling & Information Maximization
    print("Phase 1.6: Final Gap Filling and Maximizing Master CV Retention...")
    gaps = identify_gaps(jd, latex_code)
    if gaps:
        print(f"Gaps identified:\n{gaps}")
        latex_code = integrate_gaps(master_cv, jd, latex_code, gaps, system_prompt)
    else:
        print("No significant gaps found. Maximizing retention only.")
        latex_code = integrate_gaps(master_cv, jd, latex_code, "None. Focus on maximizing technical depth from Master CV.", system_prompt)

    # Save Final LaTeX
    with open(output_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_code)
    
    # Compile Resume PDF
    if compile_latex(output_tex_path, job_dir):
        gen_pdf = output_tex_path.replace(".tex", ".pdf")
        final_pdf = os.path.join(job_dir, "Kartavya Dikshit CV.pdf")
        if os.path.abspath(gen_pdf).lower() != os.path.abspath(final_pdf).lower():
            try:
                if os.path.exists(final_pdf): os.remove(final_pdf)
                os.rename(gen_pdf, final_pdf)
            except PermissionError:
                print(f"Warning: Could not update {os.path.basename(final_pdf)} because it is open in another program.")
                print(f"Your latest CV is saved as {os.path.basename(gen_pdf)} instead.")
        print(f"Success: Tailored Resume created.")
    else:
        print("Error: Resume LaTeX compilation failed.")

    # Phase 2: Tailored LaTeX Cover Letter (Based on FINAL CV)
    print(f"Phase 2: Generating German Cover Letter based on optimized CV...")
    time.sleep(10) # Breathe
    
    cl_prompt = (
        f"{system_prompt}\n\n"
        f"TARGET JOB DESCRIPTION:\n{jd}\n\n"
        f"FINAL OPTIMIZED RESUME (FOR CONTEXT):\n{latex_code}\n\n"
        f"TASK: Generate a professional German-style Cover Letter (Anschreiben) in LaTeX format. "
        f"Ensure it is perfectly aligned with the achievements and tone of the optimized resume above. "
        f"STRICTLY FOLLOW 'COVER LETTER (ANSCHREIBEN) CONSTRAINTS'. "
        f"The output must be a valid, standalone LaTeX document for a 1-page letter."
    )
    
    cl_raw = run_gemini_cli(cl_prompt)
    if cl_raw:
        cl_latex = ""
        if "```latex" in cl_raw:
            cl_latex = cl_raw.split("```latex")[1].split("```")[0].strip()
        elif "```" in cl_raw:
            parts = cl_raw.split("```")
            for part in parts:
                if "\\documentclass" in part:
                    cl_latex = part.strip()
                    break
        
        if cl_latex:
            cl_tex_path = os.path.join(job_dir, "Cover_Letter.tex")
            with open(cl_tex_path, "w", encoding="utf-8") as f:
                f.write(cl_latex)
            
            if compile_latex(cl_tex_path, job_dir):
                gen_cl_pdf = cl_tex_path.replace(".tex", ".pdf")
                final_cl_pdf = os.path.join(job_dir, "Cover_Letter.pdf")
                if os.path.abspath(gen_cl_pdf).lower() != os.path.abspath(final_cl_pdf).lower():
                    try:
                        if os.path.exists(final_cl_pdf): os.remove(final_cl_pdf)
                        os.rename(gen_cl_pdf, final_cl_pdf)
                    except PermissionError:
                        print(f"Warning: Could not update {os.path.basename(final_cl_pdf)} (File in use).")
                print(f"Success: Cover_Letter.pdf created.")
            else:
                print("Error: Cover Letter LaTeX compilation failed.")
        else:
            print("Notice: Cover Letter LaTeX failed or not found in output.")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tailor_resume_lossless.py <master_cv> <jd> <output_tex_path>")
        sys.exit(1)
    tailor_lossless(sys.argv[1], sys.argv[2], sys.argv[3], "tailor_prompt.txt")
