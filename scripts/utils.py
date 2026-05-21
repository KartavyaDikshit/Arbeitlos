import os
import subprocess
import shutil
import re
import sys
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_gemini_client():
    """Lazily initializes and returns the Gemini API client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                # Use v1beta for newest features
                _client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            except Exception as e:
                print(f"Error initializing Gemini client: {e}")
    return _client

def check_dependency(name):
    """Checks if a command-line tool is available."""
    return shutil.which(name) is not None

def clean_diagnostic_output(text):
    """Removes 'MCP issues detected' and other diagnostic noise from Gemini CLI output."""
    if not text: return ""
    lines = text.splitlines()
    cleaned = "\n".join([l for l in lines if "MCP issues detected" not in l]).strip()
    return cleaned

def run_gemini_cli(prompt, timeout=300, model='gemini-flash-latest', use_grounding=False):
    """
    Primary interface for LLM calls. 
    Prioritizes Gemini API (SDK) if available, falls back to CLI.
    """
    client = get_gemini_client()
    if client:
        # Try requested model
        result = _call_gemini_api(client, prompt, model, use_grounding)
        if result:
            return result
            
        # If requested model failed (likely Pro quota), try Flash without grounding
        if model != 'gemini-flash-latest' or use_grounding:
            print(f"Falling back to basic gemini-flash-latest (No grounding) for stability...")
            result = _call_gemini_api(client, prompt, 'gemini-flash-latest', use_grounding=False)
            if result:
                return result

    # Final fallback to legacy CLI logic
    print("API failed or exhausted. Falling back to CLI wrapper...")
    return run_legacy_gemini_cli(prompt, timeout)

def _call_gemini_api(client, prompt, model, use_grounding):
    """Internal helper to call the API with retries and tool handling."""
    try:
        config_params = {}
        if use_grounding:
            # Note: Grounding often requires a billable project or specific model
            config_params['tools'] = [types.Tool(google_search=types.GoogleSearch())]
        
        config = types.GenerateContentConfig(**config_params) if config_params else None
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        if response and response.text:
            return response.text
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "resource_exhausted" in err_msg:
            if "limit: 0" in err_msg:
                # Quota is strictly 0 for this model/tool
                return None
            # Temporary rate limit, wait a bit
            print("Rate limit hit. Waiting 5s...")
            time.sleep(5)
        elif "404" in err_msg:
            # Model doesn't exist for this API version
            return None
        print(f"API Call Error ({model}): {e}")
    return None

def run_legacy_gemini_cli(prompt, timeout=300):
    """Runs the gemini CLI with the given prompt safely."""
    try:
        cmd = ["gemini", "--prompt", "-"]
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            shell=(sys.platform == "win32")
        )
        stdout, stderr = process.communicate(input=prompt, timeout=timeout)
        
        if process.returncode != 0:
            cleaned = clean_diagnostic_output(stdout)
            if cleaned and not stderr.strip():
                return cleaned
            return None
            
        return clean_diagnostic_output(stdout)
    except subprocess.TimeoutExpired:
        if 'process' in locals():
            process.kill()
        return None
    except Exception:
        return None
