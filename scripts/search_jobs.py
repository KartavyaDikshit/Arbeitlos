import os
from exa_py import Exa
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

api_key = os.getenv("EXA_API_KEY")
exa = Exa(api_key) if api_key else None

def find_student_jobs():
    # Focused list for query
    target_companies = "SAP OR Siemens OR BMW OR Bosch OR Zalando OR Infineon OR Adidas OR Allianz"
    tech = "AI Machine Learning Data Science Software Engineering Computer Science"
    
    # Simple but effective query
    search_query = (
        f"(Werkstudent OR 'Working Student' OR Intern OR Praktikant) "
        f"({tech}) in Germany at ({target_companies})"
    )
    
    print(f"Searching for Werkstudent Roles: {search_query}...")
    
    if not exa: return []

    results = exa.search(
        search_query,
        num_results=40,
        start_published_date=(datetime.now() - timedelta(days=30)).isoformat()
    )
    
    jobs = []
    # Strict filtering for student roles and direct application pages
    required_keywords = ["werkstudent", "working student", "intern", "praktikant"]
    
    for r in results.results:
        title_lower = r.title.lower()
        
        # 1. Skip non-student roles
        if not any(req in title_lower for req in required_keywords):
            continue
            
        # 2. Extract company info
        company = "Job Portal"
        if "linkedin.com" in r.url.lower(): company = "LinkedIn"
        elif "glassdoor" in r.url.lower(): company = "Glassdoor"
        elif "indeed" in r.url.lower(): company = "Indeed"
        elif "stepstone" in r.url.lower(): company = "StepStone"
        else:
            # Try to match from our list
            match = next((c for c in target_companies.split(" OR ") if c.lower() in r.title.lower() or c.lower() in r.url.lower()), "Direct Portal")
            company = match

        job_id = r.url.split('/')[-1].split('?')[0] if '/' in r.url else "N/A"

        jobs.append({
            "url": r.url,
            "title": r.title,
            "job_id": job_id,
            "company": company,
            "published": r.published_date if hasattr(r, 'published_date') else "Recent",
            "snippet": r.text[:200] if hasattr(r, 'text') and r.text else "Direct application link."
        })
        
    # Use absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "data", "jobs_found.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)
    
    print(f"Found {len(jobs)} potential student roles.")
    return jobs

if __name__ == "__main__":
    find_student_jobs()
