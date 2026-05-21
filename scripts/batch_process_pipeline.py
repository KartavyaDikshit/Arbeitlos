import os
import sys
import glob
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

def extract_job_title(jd_content, fallback_name):
    """Uses Gemini to extract a clean, descriptive job title from JD content."""
    try:
        # Extract filename without extension as the base fallback
        clean_fallback = "".join(x for x in os.path.splitext(fallback_name)[0] if x.isalnum())
        
        prompt = (
            f"Extract exactly ONE professional and descriptive Job Title from the following Job Description content. "
            f"It should be in CamelCase (e.g., 'WorkingStudentGenAI' or 'DataEngineerIntern'). "
            f"RETURN ONLY THE TITLE. No extra text, no markdown, no quotes.\n\n"
            f"JD Content:\n{jd_content[:3000]}"
        )
        
        process = subprocess.Popen(
            ["gemini", "-e", "", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout, stderr = process.communicate(input=prompt, timeout=45)
        
        if process.returncode == 0 and stdout.strip():
            # Clean the output to be a valid folder name (CamelCase)
            title = "".join(x for x in stdout.strip() if x.isalnum())
            if title and len(title) > 3:
                return title
        
        if stderr.strip():
            print(f"Extraction API Warning for {fallback_name}: {stderr.strip()}")
            
    except Exception as e:
        print(f"Exception during title extraction for {fallback_name}: {e}")
    
    # Fallback to the filename if AI extraction fails or returns empty
    return clean_fallback if clean_fallback else "JobApplication"

def get_unique_dir(base_path):
    """Ensures a directory is unique by appending a counter if it already exists."""
    if not os.path.exists(base_path):
        return base_path
    
    counter = 1
    unique_path = f"{base_path}_{counter}"
    while os.path.exists(unique_path):
        counter += 1
        unique_path = f"{base_path}_{counter}"
    return unique_path

def run_tailor_pipeline(jd_path):
    """Executes the tailor_resume_lossless script for a single JD."""
    filename = os.path.basename(jd_path)
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_content = f.read()
    except Exception as e:
        print(f"[{filename}] Error reading file: {e}")
        return False, filename
    
    # Extract the descriptive job title with fallback to filename
    print(f"[{filename}] Extracting job title...")
    job_role = extract_job_title(jd_content, filename)
    
    # Ensure folder uniqueness to prevent overwriting
    target_path = os.path.join("data", "tailored_outputs", job_role)
    output_dir = get_unique_dir(target_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Update job_role to reflect the actual folder name used
    job_role = os.path.basename(output_dir)
    
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