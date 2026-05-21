import pandas as pd
import re
import os

def sync_markdown_to_excel():
    md_path = 'data/applications.md'
    excel_path = 'data/tracking.xlsx'
    
    if not os.path.exists(md_path):
        print("No applications.md found to sync.")
        return

    # Read Markdown table
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract rows using regex
    # Pattern matches | Role | Company | Status | ... |
    rows = re.findall(r'\| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|', content)
    
    if len(rows) < 2:
        print("No data found in applications.md")
        return

    # Skip header and separator
    data = rows[2:] 
    
    df = pd.DataFrame(data, columns=['Role', 'Company', 'Status', 'Tailored_Files', 'JD', 'Post_Mortem'])
    
    # Clean up links like [View](path) -> path
    df['Tailored_Files'] = df['Tailored_Files'].str.extract(r'\((.*?)\)')
    df['JD'] = df['JD'].str.extract(r'\((.*?)\)')
    df['Post_Mortem'] = df['Post_Mortem'].str.extract(r'\((.*?)\)')

    # Save to Excel
    df.to_excel(excel_path, index=False)
    print(f"Successfully synced {len(df)} applications to {excel_path}")

if __name__ == "__main__":
    sync_markdown_to_excel()
