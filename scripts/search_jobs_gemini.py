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
    Refactored: Searches company-by-company and portal-by-portal.
    """
    # Expanded list of Tier-1 and Tech companies
    companies = [
        "Siemens", "BMW", "Porsche", "Schaeffler", "Bosch", "SAP", "Mercedes-Benz", "Allianz", "Infineon", "Audi",
        "Volkswagen", "Continental", "TRUMPF", "ZF Group", "Munich Re", "Commerzbank", "Deutsche Bank",
        "DHL", "Deutsche Telekom", "Deutsche Bahn", "Zalando", "Delivery Hero", "HelloFresh",
        "Amazon Germany", "Google Germany", "Microsoft Germany", "NVIDIA Germany", "Bayer", "BASF", "Merck", "Henkel"
    ]
    
    # Major job portals to scan
    portals = ["LinkedIn", "Indeed", "StepStone", "Glassdoor"]
    
    all_found_jobs = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "jobs_found.json")

    print(f"Phase 1: Granular search for {len(companies)} targeted companies...")
    sys.stdout.flush()

    for company in companies:
        print(f"Searching {company}...")
        sys.stdout.flush()
        
        query = (
            f"Finde 2-3 aktuelle 'Werkstudent' Stellenangebote im Bereich Data Science, AI oder Machine Learning "
            f"speziell bei {company}. "
            f"MANDATORY: 'Werkstudent' muss im Titel oder der Beschreibung sein. "
            f"EXCLUDE: 'Pflichtpraktikum' ist verboten. "
            f"EXCLUDE: Jobs, die zwingend C1 oder C2 Deutschkenntnisse erfordern, sind verboten. B2 oder fließend Englisch ist ok. "
            f"Fokus: Erlangen, Nürnberg, München, Stuttgart, Berlin, Hamburg. "
            f"Gib das Ergebnis NUR als JSON-Liste zurück: [{{'title': '...', 'company': '{company}', 'url': '...', 'location': '...', 'snippet': '...'}}]. "
            f"Kein Smalltalk, nur das JSON."
        )

        raw_output = run_gemini_cli(query, use_grounding=True)
        if raw_output:
            process_search_results(raw_output, company, all_found_jobs, json_path)
        
        time.sleep(3) # Rate limit protection

    print(f"\nPhase 2: Scanning general portals: {', '.join(portals)}...")
    sys.stdout.flush()

    for portal in portals:
        print(f"Scanning {portal} for new postings...")
        sys.stdout.flush()

        query = (
            f"Finde 5 aktuelle 'Werkstudent' Stellenangebote für Data Science, Machine Learning oder AI in Deutschland auf {portal}. "
            f"MANDATORY: 'Werkstudent' muss im Titel sein. Veröffentlicht in den letzten 7 Tagen. "
            f"EXCLUDE: Jobs, die C1/C2 Deutsch erfordern. "
            f"Gib das Ergebnis NUR als JSON-Liste zurück: [{{'title': '...', 'company': '...', 'url': '...', 'location': '...', 'snippet': '...'}}]. "
            f"Kein Smalltalk, nur das JSON."
        )

        raw_output = run_gemini_cli(query, use_grounding=True)
        if raw_output:
            process_search_results(raw_output, "Various", all_found_jobs, json_path)
        
        time.sleep(5)

    print(f"Search complete. Total unique roles found: {len(all_found_jobs)}")
    sys.stdout.flush()
    return all_found_jobs

def process_search_results(raw_output, default_company, all_found_jobs, json_path):
    try:
        text = raw_output
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        jobs = json.loads(text.strip())
        if isinstance(jobs, list):
            new_count = 0
            for job in jobs:
                # Basic deduplication based on URL
                if any(existing.get('url') == job.get('url') for existing in all_found_jobs):
                    continue
                
                job['job_id'] = job.get('url', '').split('/')[-1].split('?')[0] if '/' in job.get('url', '') else str(int(time.time()))
                job['published'] = datetime.now().strftime("%Y-%m-%d")
                if 'company' not in job or not job['company']:
                    job['company'] = default_company
                
                all_found_jobs.append(job)
                new_count += 1
            
            print(f"Added {new_count} new roles.")
            sys.stdout.flush()

            # Save progress
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(all_found_jobs, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to parse results: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    find_werkstudent_jobs()
