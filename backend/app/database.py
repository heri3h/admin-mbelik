from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# For SQLite, check if connect_args needs check_same_thread=False
connect_args = {}
if settings.REAL_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    connect_args["timeout"] = 30

engine = create_engine(
    settings.REAL_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

if settings.REAL_DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from sqlalchemy import text

def auto_migrate_db():
    try:
        from app.models import Base
        with engine.connect() as conn:
            if settings.REAL_DATABASE_URL.startswith("sqlite"):
                # Recreate gam_metrics if sqlite_master schema lacks device_category in UNIQUE constraint
                res_m = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='gam_metrics';")).fetchone()
                if res_m and res_m[0] and ("_date_domain_adunit_pricing_dev_uc" not in res_m[0] or "device_category" not in res_m[0]):
                    print("Migrating gam_metrics table to add device_category unique constraint...")
                    conn.execute(text("DROP TABLE IF EXISTS gam_metrics;"))
                    conn.commit()

                # Recreate gam_country_metrics if sqlite_master schema lacks device_category in UNIQUE constraint
                res_c = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='gam_country_metrics';")).fetchone()
                if res_c and res_c[0] and ("_date_domain_country_adunit_pricing_dev_uc" not in res_c[0] or "device_category" not in res_c[0]):
                    print("Migrating gam_country_metrics table to add device_category unique constraint...")
                    conn.execute(text("DROP TABLE IF EXISTS gam_country_metrics;"))
                    conn.commit()

        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Auto DB migration notice: {e}")

auto_migrate_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
