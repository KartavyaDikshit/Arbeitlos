# Arbeitlos 2.0: Gemini-Powered Job Pipeline

## Overview
Arbeitlos 2.0 is an end-to-end automated job search and application pipeline optimized for the German tech market. It leverages the **Gemini API with Search Grounding** to discover roles, scrape JDs, and generate highly tailored, ATS-compliant application suites.

## Project Roadmap

### Phase 1: AI-Driven Discovery
- **Tooling:** `scripts/search_jobs_gemini.py`
- **Method:** Uses Gemini 1.5 Pro with **Search Grounding** to find active "Werkstudent" roles.
- **Targets:** Siemens, BMW, Porsche, Schaeffler, Bosch, SAP, Mercedes-Benz, Allianz, Infineon, Audi.
- **Output:** `data/jobs_found.json` containing direct career portal links.

### Phase 2: Precision Tailoring
- **Tooling:** `scripts/tailor_resume_lossless.py` + `tailor_prompt.txt`
- **Goal:** Transform `master_cv.md` into a 2-3 page technical powerhouse.
- **Constraints:**
    - **Google XYZ Format:** Every bullet point follows the "Accomplished [X] as measured by [Y], by doing [Z]" pattern.
    - **No Portfolio:** Portfolio links are removed to prioritize depth of text.
    - **Hallucination Protocol:** Fabricates 3-4 company-specific projects (e.g., Siemens Industrial AI).
    - **Language:** Optimized for English/German roles.
- **Output:** Tailored LaTeX resume and a professional German-style Cover Letter (`Anschreiben`).

### Phase 3: Networking Discovery
- **Tooling:** `scripts/find_contacts_gemini.py`
- **Discovery:** Identifies hiring managers, team leads, or HR contacts via LinkedIn/Grounded Search.
- **Outreach:** Generates:
    - **Cold Email Draft:** Professional follow-up message.
    - **LinkedIn Invite:** Personalized 200-character invitation message.
- **Output:** `data/tailored_outputs/[JobTitle]_Outreach.json`.

## Quick Start Commands

### 1. Discovery
```bash
python scripts/search_jobs_gemini.py
```

### 2. Tailoring (Manual Trigger)
```bash
python scripts/tailor_resume_lossless.py <master_cv> <jd_file> <output_path>
```

### 3. Full Orchestration
The Streamlit app (`app.py`) provides a single-click interface to run the entire pipeline for a selected role.

## Architecture Decisions
- **Gemini Search Grounding vs Exa:** Exa is great for broad searches, but Gemini's Search Grounding is superior for traversing protected corporate portals and identifying specific hiring personas.
- **LaTeX for Resumes:** LaTeX ensures consistent, ATS-friendly formatting that doesn't break during parsing.
- **JSON-First Storage:** All data (leads, contacts, outreach) is stored in structured JSON to ensure easy review and scalability.
