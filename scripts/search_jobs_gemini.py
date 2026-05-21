import os
import json
import subprocess
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
from utils import run_gemini_cli

load_dotenv()

def find_werkstudent_jobs():
    """
    Refactored: Searches company-by-company to avoid timeouts and broad-query overhead.
    """
    companies = ["Siemens", "BMW", "Porsche", "Schaeffler", "Bosch", "SAP", "Mercedes-Benz", "Allianz", "Infineon", "Audi"]
    all_found_jobs = []
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "jobs_found.json")

    print(f"Starting granular search for {len(companies)} companies...")
    sys.stdout.flush()

    for company in companies:
        print(f"Searching {company}...")
        sys.stdout.flush()
        
        query = (
            f"Finde 2-3 aktuelle 'Werkstudent' Stellenangebote im Bereich Data Science, AI oder Machine Learning "
            f"speziell bei {company}. "
            f"MANDATORY: 'Werkstudent' muss im Titel oder der Beschreibung sein. "
            f"EXCLUDE: 'Pflichtpraktikum' ist verboten. Freiwillige Praktika sind ok. "
            f"EXCLUDE: Jobs, die zwingend C1 oder C2 Deutschkenntnisse erfordern, sind verboten. B2 oder fließend Englisch ist ok. "
            f"Fokus: Erlangen, Nürnberg, München, Stuttgart. "
            f"Gib das Ergebnis NUR als JSON-Liste zurück: [{{'title': '...', 'company': '{company}', 'url': '...', 'location': '...', 'snippet': '...'}}]. "
            f"Kein Smalltalk, nur das JSON."
        )

        raw_output = run_gemini_cli(query, use_grounding=True)
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
                    sys.stdout.flush()
            except Exception as e:
                print(f"Failed to parse results for {company}: {e}")
                sys.stdout.flush()
        
        # Save intermediate results so we don't lose progress
        if all_found_jobs:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(all_found_jobs, f, indent=4, ensure_ascii=False)
        
        time.sleep(5) # Rate limit protection

    print(f"Search complete. Total roles found: {len(all_found_jobs)}")
    sys.stdout.flush()
    return all_found_jobs

if __name__ == "__main__":
    find_werkstudent_jobs()
