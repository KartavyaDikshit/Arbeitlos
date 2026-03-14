# Project Overview: Resume Tailoring & Job Search Pipeline

This project is an automated job application pipeline designed for a Master's student (Kartavya Niraj Dikshit) specializing in Data Science/AI at FAU Erlangen-Nürnberg. It automates the discovery of job opportunities, scraping of job descriptions (JDs), and the generation of highly tailored resumes and outreach messages using the Gemini CLI and external APIs.

## Tech Stack
- **Language:** Python 3.x, PowerShell
- **APIs:** 
  - [Exa AI](https://exa.ai/) (for semantic job search)
  - [Jina Reader](https://r.jina.ai/) (for scraping JDs into Markdown)
  - [Hunter.io](https://hunter.io/) (for identifying company email patterns)
- **AI Integration:** Gemini CLI (for resume tailoring and message drafting)

## Directory Structure
- `scripts/`: Contains Python scripts for search, scraping, tailoring, and networking.
- `data/`: 
  - `master_cv.md`: The base resume with complete history.
  - `raw_jds/`: Markdown files of scraped job descriptions.
  - `tailored_outputs/`: Tailored resumes, outreach messages, and JSON deltas.
- `requirements.txt`: Python dependencies (`requests`, `exa_py`, `python-dotenv`, `pandas`).
- `run_pipeline.ps1`: The primary orchestrator script.
- `tailor_prompt.txt`: The system prompt defining the AI's "Hallucination Protocol" and tailoring rules.

## Building and Running

### Prerequisites
1. Install dependencies: `pip install -r requirements.txt`
2. Create a `.env` file with the following keys:
   - `EXA_API_KEY`: Required for job search.
   - `HUNTER_API_KEY`: Optional for networking.
3. Ensure the `gemini` CLI tool is installed and authenticated in your environment.

### Execution
The entire pipeline can be run via the PowerShell script:
```powershell
./run_pipeline.ps1
```

Alternatively, scripts can be run individually:
- **Search:** `python scripts/search_jobs.py` (Outputs to `data/jobs_found.json`)
- **Scrape:** `python scripts/scrape_jd.py <url> <filename>` (Outputs to `data/raw_jds/`)
- **Tailor:** `python scripts/tailor_resume_lossless.py <master_cv> <jd> <output_path>`
- **Network:** `python scripts/networker.py <domain> <job_title> <tailored_resume_path>`

## Development Conventions & Logic

### AI Strategy: The "Hallucination Protocol"
As defined in `tailor_prompt.txt`, the AI is instructed to:
1. **Preserve Integrity:** Keep all existing education and experience from the Master CV.
2. **Fabricate Projects:** Generate 3-4 high-impact, company-specific projects (e.g., for BMW or Siemens) to show immediate relevance.
3. **Google XYZ Format:** Rewrite all bullet points (both existing and fabricated) to follow the "Accomplished [X] as measured by [Y], by doing [Z]" pattern.
4. **Keyword Injection:** Seamlessly integrate technical keywords (e.g., "Hugging Face", "PyTorch", "RL") from the JD into the resume.

### Output Flow
- All scraped JDs are stored as `.md` files to ensure formatting is preserved for the AI.
- Tailored outputs are saved with the job title in the filename (e.g., `BMW_CV.md`).
- Networking scripts draft both a cold email and a LinkedIn connection request tailored to the specific company's tech stack.
