import requests
import json
import os
from dotenv import load_dotenv
from src.database.summary_handlers import insert_summary

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not set")

def fetch_website(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def analyze_with_gemini(content, url):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
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
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    
    return json.loads(text.strip())

def main():
    company_urls = [
        'www.seez.co', 'www.presight.ai/', 'pathfinder.global/',
        'www.synapse-analytics.io/', 'fifreedomtoday.com/', 'www.thegamecompany.ai/', 'www.tenderd.com/',
        'realiste.ai', 'www.aitech.io/', 'zoftwarehub.com/', 'www.cleargrid.ai', 'haloai.app/en',
        'healsgood.com', 'www.instacodigo.com', 'www.maximuz.tech', 'www.predictivdata.com',
        'fantv.world', 'qanooni.ai/', 'jobescape.me/', 'liberaglobal.ai', 'gothelist.com',
        'www.micropolis.ai', 'cybirb.com', 'www.ragworks.ai', 'www.wellxai.com/', 'www.jadasquad.com',
        'www.neurobotx.ai', 'augmento.com', 'revsetter.ai', 'www.distichain.com', 'skillfulai.io/',
        'texel.graphics', 'www.zeroe.io', 'lokalee.app/', 'exv.io'
    ]

    for idx, url in enumerate(company_urls, start=1):
        company_id = idx  # or get actual ID from DB if needed
        company_name = url.split('//')[-1].split('/')[0]  # crude name extraction from URL

        if not url.startswith('http'):
            url = 'https://' + url

        print(f"\nFetching {url}...")
        content = fetch_website(url)

        print("Analyzing with Gemini...")
        data = analyze_with_gemini(content, url)

        print("Inserting data into summary table...")
        insert_summary(company_id, company_name, data)

if __name__ == "__main__":
    main()
