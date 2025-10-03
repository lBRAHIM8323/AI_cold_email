import requests
import json
import os
import sqlite3
import time
import threading
from dotenv import load_dotenv
from loguru import logger
from ..database.summary_handlers import insert_summary

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not set")

DB_PATH = "cold_email.db"
STATUS_FILE = "progress.txt"
MAX_RETRIES = 0

results_lock = threading.Lock()
results = {}

def get_companies():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, website FROM companies")
    companies = cursor.fetchall()
    conn.close()
    return companies

def fetch_website(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=100)
    response.raise_for_status()
    return response.text

def analyze_with_gemini(content, url):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    
    prompt = f"""Analyze this company website content from {url} and extract information in JSON format:

{{
  "department": "Primary industry (healthcare, banking, education, technology, etc.)",
  "products": ["list of products"],
  "services": ["list of services"],
  "customer_segments": ["B2B", "B2C", or both],
  "summary": "Brief summary of company vision/mission",
  "key_technologies": ["technologies they use or mention"],
  "target_market": "Who they serve",
  "unique_value_proposition": "What makes them different",
  "pain_points": ["problems they claim to solve"]
}}

Website content (first 5000 chars):
{content[:5000]}"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{api_url}?key={GEMINI_API_KEY}",
                             headers=headers,
                             json=payload)
    response.raise_for_status()
    
    result = response.json()
    text = result['candidates'][0]['content']['parts'][0]['text']
    
    text = text.strip()
    for prefix in ('```json', '```'):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith('```'):
        text = text[:-3]
    
    return json.loads(text.strip())

def save_progress(idx):
    with open(STATUS_FILE, "w") as f:
        f.write(str(idx))

def load_progress():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE) as f:
            return int(f.read().strip())
    return 0

def process_company(company_id, url, original_idx):
    if not url.startswith('http'):
        url = 'https://' + url
    company_name = url.split('//')[-1].split('/')[0]
    
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            content = fetch_website(url)
            data = analyze_with_gemini(content, url)
            with results_lock:
                results[original_idx] = (company_id, company_name, data, True)
            logger.success(f"[{original_idx}] Success: {url}")
            return True
        except Exception as e:
            logger.debug(f"[{original_idx}] Attempt {attempt} Failed for {url}: {e}")
            if attempt <= MAX_RETRIES:
                time.sleep(5)
            else:
                logger.info(f"[{original_idx}] Skipping...")
                with results_lock:
                    results[original_idx] = (None, None, None, False)
                return False

def main():
    global results
    companies = get_companies()
    start_idx = load_progress()
    
    idx = start_idx
    while idx < len(companies):
        minute_start = time.time()
        batch_end = min(idx + 13, len(companies))
        batch = companies[idx:batch_end]
        
        results = {}
        threads = []
        for i, (company_id, url) in enumerate(batch):
            original_idx = idx + i
            logger.info(f"Starting {url} ({original_idx+1}/{len(companies)})")
            t = threading.Thread(target=process_company, args=(company_id, url, original_idx))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        for i in range(idx, batch_end):
            if i in results and results[i][3]:
                company_id, company_name, data, _ = results[i]
                insert_summary(company_id, company_name, data)
        
        save_progress(batch_end)
        idx = batch_end
        
        if idx < len(companies):
            elapsed = time.time() - minute_start
            wait_time = 60 - elapsed
            if wait_time > 0:
                logger.info(f"\nWaiting {wait_time:.1f}s before next batch...")
                time.sleep(wait_time)

if __name__ == "__main__":
    main()