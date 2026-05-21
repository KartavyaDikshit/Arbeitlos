import os
import sys
import re
from dotenv import load_dotenv
# Ensure scripts directory is in path for utils import if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import run_gemini_cli

load_dotenv()

def synthesize_master_lesson():
    lessons_file = 'docs/solutions/rejection_lessons.md'
    master_file = 'docs/solutions/master_rejection_lesson.md'
    
    if not os.path.exists(lessons_file):
        print("No rejection lessons found to synthesize.")
        return

    with open(lessons_file, 'r', encoding='utf-8') as f:
        all_lessons = f.read()

    if not all_lessons.strip():
        print("Rejection lessons file is empty.")
        return

    print("Synthesizing Master Lesson from all previous rejections...")

    prompt = f"""
    You are a Lead Career Strategist specializing in the German High-Tech market (AI, ML, Data Science).
    We have a collection of individual rejection analyses from various applications. 
    Your task is to synthesize these into one "MASTER STRATEGY" document.
    
    Individual Lessons Data:
    {all_lessons[:10000]} 
    
    Identify global, systemic patterns of failure across:
    1. TECHNICAL STACK: Are we consistently missing certain 'German Industry Standard' tools (e.g., SAP, specific cloud providers)?
    2. TAILORING FLAWS: Is the AI consistently over-hallucinating or being too aggressive with metrics (XYZ format issues)?
    3. CULTURAL ALIGNMENT: Is the tone consistently off for German engineering culture?
    4. LANGUAGE/LOCATION: Are there repeating themes regarding German fluency or location context?
    
    FORMAT YOUR RESPONSE AS A HIGH-LEVEL STRATEGIC MANIFESTO:
    # MASTER REJECTION STRATEGY & GLOBAL LESSONS
    ## GLOBAL FAILURE PATTERNS
    - [Pattern 1]
    - [Pattern 2]
    
    ## STRATEGIC RECTIFICATIONS (FOR FUTURE TAILORING)
    - [Specific instruction 1]
    - [Specific instruction 2]
    
    ## RED LINES (DO NOT CROSS)
    - [Forbidden action 1]
    
    Keep it concise, actionable, and authoritative.
    """

    output = run_gemini_cli(prompt, model='gemini-3.1-pro-preview', timeout=180)
    
    if output:
        # Strip HTML just in case
        clean_stdout = re.sub(r'<[a-z]+.*?>', '', output, flags=re.IGNORECASE)
        clean_stdout = re.sub(r'</[a-z]+>', '', clean_stdout, flags=re.IGNORECASE)
        
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(clean_stdout)
        print("Master Lesson successfully synthesized.")
    else:
        print("Error: Could not synthesize Master Lesson.")

if __name__ == "__main__":
    synthesize_master_lesson()
