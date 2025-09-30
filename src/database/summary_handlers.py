import sqlite3
import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__),'..', '..', 'cold_email.db')

def insert_summary(company_id, company_name, data):
    """
    Insert company summary data into the summary table.

    Args:
        company_id (int): ID of the company in the companies table
        company_name (str): Name of the company
        data (dict): JSON data returned by Gemini
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Convert list fields to JSON strings if they exist
    products = json.dumps(data.get("products", [])) if data.get("products") else None
    services = json.dumps(data.get("services", [])) if data.get("services") else None
    customer_segments = json.dumps(data.get("customer_segments", [])) if data.get("customer_segments") else None
    key_technologies = json.dumps(data.get("key_technologies", [])) if data.get("key_technologies") else None
    pain_points = json.dumps(data.get("pain_points", [])) if data.get("pain_points") else None

    summary_text = data.get("summary")
    department = data.get("department")
    target_market = data.get("target_market")
    unique_value_proposition = data.get("unique_value_proposition")

    query = """
    INSERT INTO summary (
        company_id, company_name, summary, department, products, services, 
        customer_segments, key_technologies, target_market, unique_value_proposition, pain_points
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cur.execute(query, (
        company_id, company_name, summary_text, department, products, services,
        customer_segments, key_technologies, target_market, unique_value_proposition, pain_points
    ))
    
    conn.commit()
    conn.close()
    print(f"Inserted summary for company_id={company_id}, company_name={company_name}")
