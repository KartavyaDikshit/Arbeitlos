import os
from exa_py import Exa
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

load_dotenv()

api_key = os.getenv("EXA_API_KEY")
exa = Exa(api_key) if api_key else None

def find_student_jobs():
    # Targets: Siemens, BMW, Adidas, Schaeffler, Bosch, Continental in Erlangen/Nuremberg
    companies = ["Siemens", "BMW", "Adidas", "Schaeffler", "Bosch", "Continental"]
    keywords = ["Werkstudent", "Working Student", "Master Thesis", "Internship"]
    tech = "AI Machine Learning Data Science"
    
    # Constructing a broad search for the region
    search_query = f"({ ' OR '.join(keywords) }) {tech} at ({ ' OR '.join(companies) }) in Erlangen OR Nuremberg OR Munich posted in last 7 days"
    
    print(f"Searching for Student Roles: {search_query}...")
    
    if not exa:
        print("EXA_API_KEY not set. This is a dry-run log.")
        return []

    results = exa.search(
        search_query,
        num_results=10,
        category="news" # Exa news/blogs often index career pages better than direct crawl
    )
    
    jobs = [{"url": r.url, "title": r.title} for r in results.results]
    with open("data/jobs_found.json", "w") as f:
        json.dump(jobs, f, indent=4)
    
    print(f"Found {len(jobs)} potential student roles.")
    return jobs

if __name__ == "__main__":
    find_student_jobs()
