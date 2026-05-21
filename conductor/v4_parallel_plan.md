# Implementation Plan: Parallel Tailoring & Active Operations Page

## Objective
Enable parallel job tailoring tasks and provide a dedicated monitoring page.

## Scope & Impact
- `app.py`:
    - Move tailoring logic from a blocking sidebar process to a background execution model.
    - Implement `st.session_state.tasks` to store metadata (ID, Company, Role, LogPath, Status).
    - Create a new "Active Operations" navigation tab.
    - Update "Tailor CV" to allow manual JD input while other tasks run.
    - Sidebar will now show a "Tasks Summary" (e.g., "3 Tasks Running").

## Implementation Steps

### Step 1: Background Process Utility
Modify `run_script` or add a new `launch_task(cmd_list, task_id)`:
- Generate a unique `task_id` (e.g., timestamp + title).
- Launch `subprocess.Popen` with output redirected to `data/logs/[task_id].log`.
- Return the process handle (though we'll rely on the log file and process existence check).

### Step 2: State Management
Initialize `st.session_state.tasks = {}` in `main()`.
Each task entry:
```json
{
  "task_id": "...",
  "company": "...",
  "role": "...",
  "status": "Running/Complete/Failed",
  "log_path": "...",
  "url": "..."
}
```

### Step 3: Update "Find Jobs" and "Tailor CV" Pages
- "Tailor Suite" button will now call `launch_task` and add to `st.session_state.tasks`.
- "Tailor CV" page will remain for manual pasting, but clicking "Execute" will also use the background launcher.

### Step 4: Create "Active Operations" Page
- Iterate through `st.session_state.tasks`.
- For each task:
    - Check if process is still running (using PID or a sentinel file).
    - Display log tail in an expander.
    - If "Complete", show the "Mark as Applied" button.
    - Add a "Clear" button for finished tasks.

### Step 5: Sidebar Summary
- Replace the blocking log container with a task list summary in the sidebar.

## Verification
- Trigger multiple "Tailor Suite" operations.
- Navigate to "Active Operations" and verify logs are updating for all tasks.
- Paste a JD manually and verify it runs alongside existing ones.
- Mark multiple as "Applied" and check Excel.