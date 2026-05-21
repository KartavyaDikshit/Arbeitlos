# Upgrade Plan: Multi-Tier Reinforcement Learning System

## Objective
Implement a sophisticated "Learning Loop" that allows for mass selection of rejected applications, individual analysis, and a synthesized "Master Lesson" that informs all future tailoring missions.

## Key Files & Context
- `app.py`: UI for selecting and triggering analyses.
- `scripts/analyze_rejection.py`: Core logic for individual role analysis.
- `scripts/synthesize_master_lesson.py` (New): Logic for cross-role synthesis.
- `scripts/tailor_resume_lossless.py`: Integration point for applying lessons during tailoring.
- `docs/solutions/master_rejection_lesson.md` (New): Storage for synthesized patterns.

## Implementation Steps

### Phase 1: UI Enhancement (`app.py`)
- [ ] **Multi-Select Interface**: Replace `st.selectbox` with `st.multiselect` in the Post-Mortem Lab.
- [ ] **Batch Processing Button**: Add "EXECUTE BATCH ANALYSIS" to process all selected roles sequentially.
- [ ] **Synthesis Trigger**: Add "GENERATE MASTER LESSON" button to trigger the global synthesis script.
- [ ] **Protocol Tab Update**: Update the "SYSTEM PROTOCOLS" page to show both Master and Individual lessons clearly.

### Phase 2: Batch Analysis Script (`scripts/batch_analyze_rejections.py`)
- [ ] **Sequential Execution**: A simple wrapper script that takes a list of role names and calls `analyze_rejection.py` for each.
- [ ] **Progress Tracking**: Ensure the UI shows which role is currently being analyzed.

### Phase 3: Global Synthesis (`scripts/synthesize_master_lesson.py`)
- [ ] **Lesson Aggregation**: Read all individual lessons from `docs/solutions/rejection_lessons.md`.
- [ ] **Synthesis Prompt**: Use Gemini to identify high-level, recurring failure patterns (e.g., "The candidate consistently over-promises on German fluency" or "Technical bullets are consistently too abstract for Siemens").
- [ ] **Master Storage**: Save the output to `docs/solutions/master_rejection_lesson.md`.

### Phase 4: Two-Tier Contextual Reinforcement (`scripts/tailor_resume_lossless.py`)
- [ ] **Global Injection**: Always include the `master_rejection_lesson.md` in the system prompt.
- [ ] **Semantic Retrieval**: 
    - [ ] Before tailoring, send the new JD and the titles/summaries of all individual lessons to Gemini.
    - [ ] Ask Gemini: "Which 2-3 individual rejection lessons are most relevant to this new role?"
    - [ ] Inject the **Master Lesson** + **Relevant Individual Lessons** into the tailoring prompt.

### Phase 5: Verification & Testing
- [ ] **Reproduction**: Run a batch analysis on 2-3 roles.
- [ ] **Synthesis Check**: Verify the `master_rejection_lesson.md` is generated and contains strategic insights.
- [ ] **Tailoring Check**: Run a new tailoring mission and verify the prompt includes both tiers of lessons.

## Migration & Rollback Strategies
- **Separation**: Keep `rejection_lessons.md` as the raw database and `master_rejection_lesson.md` as the high-level summary.
- **Fallbacks**: If synthesis fails or is empty, the system defaults to using the raw `rejection_lessons.md` as it does currently.
