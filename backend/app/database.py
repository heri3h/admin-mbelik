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
        with engine.connect() as conn:
            if settings.REAL_DATABASE_URL.startswith("sqlite"):
                res = conn.execute(text("PRAGMA table_info(gam_metrics);"))
                cols = [row[1] for row in res.fetchall()]
                if cols and "device_category" not in cols:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'mobile';"))
                if cols and "match_rate" not in cols:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN match_rate FLOAT DEFAULT 0.0;"))
                if cols and "ad_requests" not in cols:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN ad_requests INTEGER DEFAULT 0;"))
                if cols and "matched_requests" not in cols:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN matched_requests INTEGER DEFAULT 0;"))

                res_c = conn.execute(text("PRAGMA table_info(gam_country_metrics);"))
                c_cols = [row[1] for row in res_c.fetchall()]
                if c_cols and "device_category" not in c_cols:
                    conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'mobile';"))
                if c_cols and "pricing_rule_name" not in c_cols:
                    conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN pricing_rule_name VARCHAR(150) DEFAULT 'All Rules';"))

                conn.commit()
    except Exception as e:
        print(f"Auto DB migration notice: {e}")

auto_migrate_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
