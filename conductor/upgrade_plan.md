# Upgrade Plan: Arbeitlos Job Pipeline 2.0

## Objective
Upgrade the current job search and tailoring pipeline to use the Gemini API/CLI for more robust job discovery, 2-3 page ATS-friendly resume generation, and hiring manager identification.

## Key Files & Context
- **Discovery:** `scripts/search_jobs_gemini.py` (New)
- **Tailoring:** `tailor_prompt.txt` (Update)
- **Networking:** `scripts/find_contacts_gemini.py` (New)
- **UI:** `app.py` (Update)
- **Base Resume:** `master_cv.md` (Source)

## Implementation Steps

### Step 1: Architecture & Scraping Strategy
- **Search:** Use Gemini 1.5 Pro with **Search Grounding** to discover roles. This is more effective than the Exa API for finding specific career portal links at major German companies.
- **Scraping:** Integrate `r.jina.ai` as the primary JD scraper to convert portal HTML into high-quality Markdown.
- **Structure:** Update `app.py` to call these new scripts and handle the 2-3 page PDF generation (via LaTeX or a Python-based Markdown-to-PDF converter).

### Step 2: Job Sourcing & Filtering (`scripts/search_jobs_gemini.py`)
Implement a Python script that:
1.  Connects to the Gemini API (`google-generativeai`).
2.  Performs a grounded search for "Werkstudent" roles in Data Science, AI, and ML at **Siemens, BMW, Porsche, Schaeffler, Bosch, SAP, Mercedes-Benz, Allianz, Infineon, and Audi**.
3.  Filters for active roles in the **Erlangen, Nuremberg, Munich, and Stuttgart** regions.
4.  Outputs a JSON file (`data/jobs_found_gemini.json`) for the Streamlit UI.

### Step 3: Material Generation Pipeline (`tailor_prompt.txt`)
Update the system prompt to:
1.  **Expansion:** Instruct the LLM to expand the existing 1.5-page CV into a **2-3 page detailed technical resume**.
2.  **Portfolio Removal:** Explicitly remove the portfolio link to focus on technical depth and impact.
3.  **ATS Optimization:** Use high-density keywords from the JD and strict LaTeX/Markdown formatting that ATS scanners favor.
4.  **Google XYZ Format:** Enforce "Accomplished [X] as measured by [Y], by doing [Z]" for all 15-20+ bullet points.
5.  **German Cover Letter:** Add a dedicated task for a professional German-style cover letter (`Anschreiben`).

### Step 4: Networking & Outreach Pipeline (`scripts/find_contacts_gemini.py`)
Create a new script that:
1.  Takes the Job URL and Company name.
2.  Uses Gemini Search to identify:
    *   The Hiring Manager's name/title.
    *   The specific team name (e.g., "AI Manufacturing Strategy").
    *   A probable contact email or LinkedIn profile.
3.  Drafts a **Cold Email** and a **200-character LinkedIn invite message**.

### Step 5: Output & Documentation
1.  Update `run_pipeline.ps1` to orchestrate the new Gemini-based workflow.
2.  Replace the contents of `GEMINI.md` with the finalized roadmap and technical instructions.

## Verification & Testing
- **Search Test:** Verify `scripts/search_jobs_gemini.py` returns valid URLs from at least 3 target companies.
- **Tailoring Test:** Verify the generated resume is > 2 pages and contains NO portfolio link.
- **Networking Test:** Verify the LinkedIn invite is < 200 characters and contains the hiring manager's name.
