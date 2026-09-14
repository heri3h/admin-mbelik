import sys
import os
from datetime import date, timedelta

# Ensure backend folder is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import User
from app.services.auth import get_password_hash
from app.services.sync import sync_service
from app.config import settings

def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            print(f"Creating default admin user: {settings.ADMIN_USERNAME}")
            hashed_pwd = get_password_hash(settings.ADMIN_PASSWORD)
            admin = User(username=settings.ADMIN_USERNAME, hashed_password=hashed_pwd)
            db.add(admin)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")

        # Seed initial 30 days of data
        today = date.today()
        start_date = today - timedelta(days=30)
        print(f"Seeding historical data from {start_date} to {today}...")
        result = sync_service.sync_range(db, start_date, today)
        print(f"Seeding complete! Synced {result['records_synced']} records.")
        print("Done!")
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
