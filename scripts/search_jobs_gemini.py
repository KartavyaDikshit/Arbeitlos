import os
import json
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_gemini_cli(query, timeout=60):
    """Runs the gemini CLI for a single search query."""
    try:
        process = subprocess.Popen(
            ["gemini", "--prompt", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=True
        )
        stdout, stderr = process.communicate(input=query, timeout=timeout)
        
        if process.returncode != 0:
            print(f"Gemini CLI Error: {stderr}")
            return None
        return stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Gemini CLI Timeout after {timeout}s for this query.")
        process.kill()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def find_werkstudent_jobs():
    """
    Refactored: Searches company-by-company to avoid timeouts and broad-query overhead.
    """
    companies = ["Siemens", "BMW", "Porsche", "Schaeffler", "Bosch", "SAP", "Mercedes-Benz", "Allianz", "Infineon", "Audi"]
    all_found_jobs = []
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "jobs_found.json")

    print(f"Starting granular search for {len(companies)} companies...")

    for company in companies:
        print(f"Searching {company}...")
        
        query = (
            f"Finde 2-3 aktuelle 'Werkstudent' Stellenangebote im Bereich Data Science, AI oder Machine Learning "
            f"speziell bei {company}. "
            f"MANDATORY: 'Werkstudent' muss im Titel oder der Beschreibung sein. "
            f"EXCLUDE: 'Pflichtpraktikum' ist verboten. Freiwillige Praktika sind ok. "
            f"Fokus: Erlangen, Nürnberg, München, Stuttgart. "
            f"Gib das Ergebnis NUR als JSON-Liste zurück: [{{'title': '...', 'company': '{company}', 'url': '...', 'location': '...', 'snippet': '...'}}]. "
            f"Kein Smalltalk, nur das JSON."
        )

        raw_output = run_gemini_cli(query)
        if raw_output:
            try:
                # Clean JSON
                text = raw_output
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                jobs = json.loads(text.strip())
                if isinstance(jobs, list):
                    for job in jobs:
                        job['job_id'] = job.get('url', '').split('/')[-1].split('?')[0] if '/' in job.get('url', '') else "N/A"
                        job['published'] = datetime.now().strftime("%Y-%m-%d")
                        job['company'] = company # Ensure correct company mapping
                    all_found_jobs.extend(jobs)
                    print(f"Found {len(jobs)} roles for {company}.")
            except Exception as e:
                print(f"Failed to parse results for {company}: {e}")
        
        # Save intermediate results so we don't lose progress
        if all_found_jobs:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(all_found_jobs, f, indent=4, ensure_ascii=False)
        
        time.sleep(5) # Rate limit protection

    print(f"Search complete. Total roles found: {len(all_found_jobs)}")
    return all_found_jobs

if __name__ == "__main__":
    find_werkstudent_jobs()
