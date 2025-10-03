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

    def to_json(value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value)

    products = to_json(data.get("products"))
    services = to_json(data.get("services"))
    customer_segments = to_json(data.get("customer_segments"))
    key_technologies = to_json(data.get("key_technologies"))
    pain_points = to_json(data.get("pain_points"))
    target_market = to_json(data.get("target_market"))
    unique_value_proposition = to_json(data.get("unique_value_proposition"))

    summary_text = data.get("summary")
    department = data.get("department")

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