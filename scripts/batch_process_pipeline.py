import os
import sys
import glob
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

def extract_job_title(jd_content):
    """Uses Gemini to extract a clean, descriptive job title from JD content."""
    try:
        # Re-using the logic from tailor_resume_lossless.py to call gemini cli
        prompt = (
            f"Extract exactly ONE professional and descriptive Job Title from the following Job Description content. "
            f"It should be in CamelCase or snake_case for use as a folder name. "
            f"Example: 'WorkingStudentGenAI' or 'DataEngineerIntern'. "
            f"DO NOT include any extra text or emojis. "
            f"JD Content:\n{jd_content[:2000]}" # Use first 2000 chars to save tokens
        )
        
        # We need a small helper to run the CLI here
        process = subprocess.Popen(
            ["gemini", "-e", "", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout, stderr = process.communicate(input=prompt, timeout=30)
        
        if process.returncode == 0 and stdout.strip():
            # Clean the output to be a valid folder name
            title = "".join(x for x in stdout.strip() if x.isalnum())
            return title if title else "UnknownJob"
        return "UnknownJob"
    except Exception:
        return "UnknownJob"

def run_tailor_pipeline(jd_path):
    """Executes the tailor_resume_lossless script for a single JD."""
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_content = f.read()
    
    # Extract the descriptive job title instead of using filename
    print(f"[{os.path.basename(jd_path)}] Extracting job title...")
    job_role = extract_job_title(jd_content)
    
    output_dir = os.path.join("data", "tailored_outputs", job_role)
    os.makedirs(output_dir, exist_ok=True)
    
    output_tex = os.path.join(output_dir, "CV.tex")
    master_cv = os.path.join("data", "master_cv.md")
    
    # Fallback to root master_cv.md if not in data folder
    if not os.path.exists(master_cv):
        master_cv = "master_cv.md"

    print(f"[{job_role}] Starting tailoring pipeline...")
    
    cmd = [
        sys.executable,
        os.path.join("scripts", "tailor_resume_lossless.py"),
        master_cv,
        jd_path,
        output_tex
    ]
    
    try:
        # Run the script and capture output
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode == 0:
            print(f"[{job_role}] SUCCESS.")
            clean_latex_artifacts(output_dir)
            return True, job_role
        else:
            print(f"[{job_role}] FAILED. Error:\n{process.stderr}")
            return False, job_role
    except Exception as e:
        print(f"[{job_role}] EXCEPTION: {e}")
        return False, job_role

def clean_latex_artifacts(directory):
    """Removes auxiliary LaTeX files (.aux, .log, .out) from the output directory."""
    artifacts = ["*.aux", "*.log", "*.out"]
    for artifact in artifacts:
        for file in glob.glob(os.path.join(directory, artifact)):
            try:
                os.remove(file)
            except OSError:
                pass

def main():
    batch_dir = os.path.join("data", "batch_jds")
    
    # Find all .txt and .md files in the batch directory
    jds = glob.glob(os.path.join(batch_dir, "*.txt")) + glob.glob(os.path.join(batch_dir, "*.md"))
    
    if not jds:
        print(f"No Job Descriptions found in {batch_dir}. Please add some .txt or .md files.")
        return

    print(f"Found {len(jds)} Job Descriptions. Initializing batch processing...")
    
    # Run a maximum of 3 concurrent processes to respect general API rate limits
    max_workers = 3 
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks with a slight stagger to prevent immediate API congestion
        future_to_jd = {}
        for jd in jds:
            future = executor.submit(run_tailor_pipeline, jd)
            future_to_jd[future] = jd
            time.sleep(2) # 2-second stagger
            
        for future in as_completed(future_to_jd):
            jd = future_to_jd[future]
            try:
                success, name = future.result()
                results.append((name, success))
            except Exception as exc:
                print(f"Job {jd} generated an exception: {exc}")
                results.append((os.path.basename(jd), False))
                
    # Print Final Summary
    print("\n" + "="*40)
    print("BATCH PROCESSING SUMMARY")
    print("="*40)
    successful = sum(1 for _, success in results if success)
    print(f"Total Jobs Processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print("-" * 40)
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} - {name}")

if __name__ == "__main__":
    main()