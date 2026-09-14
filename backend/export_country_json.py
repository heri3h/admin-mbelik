import sys
import json
from datetime import date
from app.database import SessionLocal
from app.models import User
from app.api.dashboard import get_site_countries_breakdown

def export_domain_countries_to_json(domain: str, start_date: str = None, end_date: str = None, output_file: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).first()
        items = get_site_countries_breakdown(domain, start_date, end_date, db, user)

        # Convert Pydantic items to dict list
        data = [item.model_dump() if hasattr(item, 'model_dump') else item.dict() for item in items]
        json_output = json.dumps(data, indent=2, ensure_ascii=False)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"✅ Data JSON berhasil disimpan ke file: {output_file}")
        
        return json_output
    finally:
        db.close()

if __name__ == "__main__":
    # Allow running with command line arguments:
    # python3 export_country_json.py <domain> [start_date] [end_date] [output_file]
    domain = sys.argv[1] if len(sys.argv) > 1 else "zse.ugames.top"
    start_date = sys.argv[2] if len(sys.argv) > 2 else "2026-09-01"
    end_date = sys.argv[3] if len(sys.argv) > 3 else "2026-09-13"
    output_file = sys.argv[4] if len(sys.argv) > 4 else f"{domain}_countries.json"

    result_json = export_domain_countries_to_json(domain, start_date, end_date, output_file)
    print(f"=== SAMPLE OUTPUT JSON UNTUK {domain} ===")
    print(result_json[:600] + "\n...")
