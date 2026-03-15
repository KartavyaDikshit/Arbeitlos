import os
import requests
import json
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()

def get_domain_from_url(url):
    try:
        parts = url.split('/')[2].split('.')
        if len(parts) >= 2:
            return f"{parts[-2]}.{parts[-1]}"
        return url.split('/')[2]
    except:
        return ""

def find_contacts(job_url, job_title="", company_name=""):
    exa_key = os.getenv("EXA_API_KEY")
    hunter_key = os.getenv("HUNTER_API_KEY")
    domain = get_domain_from_url(job_url)
    
    contacts = []
    
    if not exa_key:
        return []

    exa = Exa(exa_key)
    
    # STAGE 1: Find the exact person on LinkedIn
    # We search for recruiters or managers for that specific company and role
    person_query = f'LinkedIn profile of "Hiring Manager" OR "Recruiter" OR "Team Lead" for "{job_title}" at {company_name} Germany'
    
    try:
        results = exa.search(person_query, num_results=5)
        for res in results.results:
            if "linkedin.com/in/" in res.url:
                name = res.title.split('-')[0].strip()
                # Clean name (remove titles like MBA, PhD, etc.)
                clean_name = name.split(',')[0].split('|')[0].strip()
                
                contact = {
                    "name": clean_name,
                    "linkedin": res.url,
                    "email": None,
                    "source": "LinkedIn Persona"
                }
                
                # STAGE 2: Try to find their email via Hunter.io if we have a name
                if hunter_key and domain:
                    name_parts = clean_name.split()
                    if len(name_parts) >= 2:
                        first, last = name_parts[0], name_parts[-1]
                        finder_url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first}&last_name={last}&api_key={hunter_key}"
                        try:
                            email_res = requests.get(finder_url).json()
                            if email_res.get('data', {}).get('email'):
                                contact['email'] = email_res['data']['email']
                        except:
                            pass
                
                contacts.append(contact)
                if len(contacts) >= 2: break # We only need the top 2 best matches
    except Exception as e:
        print(f"Contact Search Error: {e}")

    return contacts
