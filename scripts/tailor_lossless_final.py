import os
import subprocess
import sys

def run_gemini_component(component_name, context_jd, master_text):
    # Ensure multi-line JD or master_text doesn't break the prompt
    clean_jd = str(context_jd).replace('"', "'")
    clean_master = str(master_text).replace('"', "'")
    
    prompt = "Act as a Resume Engineer. Given this JD: " + clean_jd + "\n\nAnd this Master Resume context: " + clean_master + "\n\n"
    
    if component_name == "summary":
        prompt += "Provide ONLY a 3-sentence tailored Professional Summary. Do not return anything else."
    elif component_name == "new_projects":
        prompt += "Provide 3-4 completely fabricated projects in Google XYZ format that solve the JD's specific problems. Return ONLY the markdown project list."
    elif component_name == "skills":
        prompt += "Provide a new sub-section 'JD-Specific Skills' at the top of the Skills section. Return ONLY this sub-section markdown."

    result = subprocess.run(
        'gemini', 
        input=prompt, 
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        shell=True
    )
    return result.stdout.strip()

def tailor_lossless_final(master_cv_path, jd_path, output_path):
    with open(master_cv_path, 'r', encoding='utf-8') as f:
        master_lines = f.readlines()
    with open(jd_path, 'r', encoding='utf-8') as f:
        jd_text = f.read()

    # Identifying key indices
    projects_idx = -1
    skills_idx = -1
    for i, line in enumerate(master_lines):
        if "Projects ---" in line:
            projects_idx = i
        if "Skills---" in line:
            skills_idx = i

    print(f"Tailoring components for {output_path}...")
    new_summary = run_gemini_component("summary", jd_text, "".join(master_lines[:20]))
    new_projects = run_gemini_component("new_projects", jd_text, "".join(master_lines[projects_idx:projects_idx+20] if projects_idx != -1 else ""))
    new_skills = run_gemini_component("skills", jd_text, "".join(master_lines[skills_idx:skills_idx+20] if skills_idx != -1 else ""))

    final_cv = []
    # 1. Contact info (Keep first 8 lines)
    final_cv.extend(master_lines[:8])
    
    # 2. Add New Summary
    final_cv.append("\n## SUMMARY\n")
    final_cv.append(new_summary + "\n\n")
    
    # 3. Keep original Education and Work Experience
    # We will include everything from the 9th line of master_cv until the Projects section
    if projects_idx != -1:
        final_cv.extend(master_lines[8:projects_idx])

    # 4. Add Projects (New + Old)
    final_cv.append("Projects ---------------------------------------------------------------------------------------------------------------------------------\n\n")
    final_cv.append(new_projects + "\n\n")
    if projects_idx != -1 and skills_idx != -1:
        # Include original projects
        final_cv.extend(master_lines[projects_idx+1:skills_idx])

    # 5. Add Skills (New + Old)
    final_cv.append("Skills--------------------------------------------------------------------------------------------------------------------------------------\n\n")
    final_cv.append(new_skills + "\n\n")
    if skills_idx != -1:
        final_cv.extend(master_lines[skills_idx+1:])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(final_cv)
    print(f"Lossless Tailored CV saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tailor_lossless_final.py <master_cv> <jd> <output>")
        sys.exit(1)
    tailor_lossless_final(sys.argv[1], sys.argv[2], sys.argv[3])
