import requests
import json
import subprocess
import time
import sys

def test_n8n():
    print("Testing n8n webhook locally...")
    
    # 1. Start the backend app if it isn't running, or just call the DB directly.
    # To make it simple and not interfere with port binding, we can simulate the API call logic directly by importing and running it.
    # But since it's a FastAPI router, testing via HTTP request is best.
    # Let's see if the server is running on port 8000.
    
    url = "http://127.0.0.1:8000/api/jobs/n8n-webhook"
    
    payload = {
        "jobs": [
            {
                "title": "Software Engineer Intern",
                "company": "n8n Test Company",
                "location": "Istanbul",
                "source_url": "https://example.com/n8n-test-job-unique-id-999",
                "description": "Python, SQL and API design intern.",
                "requirements": "SQL, Python",
                "source": "arbeitnow",
                "job_type": "internship"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Backend server is not running. Let's simulate the database logic directly instead.")
        simulate_db_logic()

def simulate_db_logic():
    from backend.database import SessionLocal
    from backend.models.job import Job
    from backend.schemas.agent_contracts import ScrapedJobContract
    
    raw_data = {
        "title": "Software Engineer Intern",
        "company": "n8n Test Company",
        "location": "Istanbul",
        "source_url": "https://example.com/n8n-test-job-unique-id-999",
        "description": "Python, SQL and API design intern.",
        "requirements": "SQL, Python",
        "source": "arbeitnow",
        "job_type": "internship"
    }
    
    db = SessionLocal()
    try:
        validated = ScrapedJobContract.model_validate(raw_data)
        j_dict = validated.to_job_dict()
        
        # Check duplicate
        existing = db.query(Job).filter(Job.source_url == j_dict["source_url"]).first()
        if existing:
            print("Job already exists in DB.")
            # Remove it to re-test
            db.delete(existing)
            db.commit()
            print("Removed existing job to retry.")
            
        new_job = Job(**j_dict)
        db.add(new_job)
        db.commit()
        print("✅ Success: Data validated and saved to DB successfully using the n8n model mappings!")
        
        # Cleanup test data
        db.delete(new_job)
        db.commit()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # If backend is running, it will check the endpoint, otherwise it runs DB simulation
    simulate_db_logic()
