# Implementation Plan: Arbeitlos 2.0 Feature Upgrades

## Objective
Update the `Arbeitlos 2.0` pipeline to:
1. Filter out jobs requiring C1/C2 German language proficiency.
2. Introduce a real-time progress sidebar in the Streamlit app for the CV tailoring process.
3. Allow users to mark a tailored job as "Applied" directly from the sidebar.
4. Log "Applied" jobs to an Excel tracking sheet (`data/tracking.xlsx`).

## Scope & Impact
- `scripts/search_jobs_gemini.py`: Modify the Gemini API prompt to strictly exclude roles requiring C1/C2 German.
- `app.py`:
    - Add state management for active tailoring tasks (`st.session_state.active_tailor` and `st.session_state.tailor_ready`).
    - Redirect the "Tailor Suite" button in `page_find_jobs` to set the active task and trigger a re-run instead of navigating to a manual page.
    - Implement the sidebar UI to display real-time CLI output using `run_script_realtime`.
    - Create the `log_application_to_excel` utility to append applied jobs to `data/tracking.xlsx`.
    - Provide a "Mark as Applied" button once the suite is finalized.

## Implementation Steps

### Step 1: Update Job Discovery Query
Modify the `query` string in `scripts/search_jobs_gemini.py`:
- Add: `f"EXCLUDE: Jobs, die zwingend C1 oder C2 Deutschkenntnisse erfordern, sind verboten. B2 oder fließend Englisch ist ok. "`

### Step 2: Implement Excel Tracking Utility
Add a new function `log_application_to_excel(company, title, url)` in `app.py` to append data to `data/tracking.xlsx` using `pandas`.

### Step 3: Enhance Streamlit UI
Modify `app.py`:
1. **Trigger Change:** Update `page_find_jobs()` so clicking "Tailor Suite" sets `st.session_state.active_tailor = job` and calls `st.rerun()`.
2. **Sidebar Logic:** In `main()`, under the `st.sidebar` context:
    - Check for `active_tailor`. If present, execute `tailor_resume_lossless.py` and `harvest_apps.py` synchronously while piping `log_container` to the sidebar.
    - Upon completion, set `st.session_state.tailor_ready = job` and clear `active_tailor`.
    - Check for `tailor_ready`. If present, display the "Mark as Applied" button. When clicked, call `log_application_to_excel` and clear the state.

## Verification
- Run `python scripts/search_jobs_gemini.py` to ensure returned jobs do not require C1/C2 German.
- Run `streamlit run app.py`, search for jobs, click "Tailor Suite", and verify the sidebar populates with real-time logs.
- Wait for completion and click "Mark as Applied".
- Verify that `data/tracking.xlsx` is created/updated with the correct details.