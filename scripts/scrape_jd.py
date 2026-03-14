import requests
import sys
import os

def scrape_to_markdown(url, filename):
    # Use Jina Reader API to get clean markdown from URL
    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/markdown"}
    
    print(f"Scraping {url}...")
    
    response = requests.get(jina_url, headers=headers)
    if response.status_code == 200:
        # Save to data/raw_jds/
        output_dir = "data/raw_jds"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Clean up filename (remove spaces, etc.)
        safe_filename = "".join(x for x in filename if x.isalnum() or x in "._- ")
        path = f"{output_dir}/{safe_filename}.md"
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"Successfully scraped to {path}.")
        return path
    else:
        print(f"Failed to scrape {url}. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scrape_jd.py <url> <filename>")
        sys.exit(1)
    scrape_to_markdown(sys.argv[1], sys.argv[2])
