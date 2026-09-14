import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app.models import DailyProfitSummary, GAMMetric
from sqlalchemy import func

def inspect_db():
    print("=" * 65)
    print("=== INSPEKSI SELURUH TANGGAL & EARNING DI DATABASE DASHBOARD ===")
    print("=" * 65)

    db = SessionLocal()
    try:
        summaries = db.query(DailyProfitSummary).order_by(DailyProfitSummary.date.desc()).all()
        print(f"Total Baris DailyProfitSummary: {len(summaries)}\n")
        print(f"{'Tanggal DB':<15} | {'Total Revenue':<20} | {'Total Spend':<20} | {'Net Profit':<20}")
        print("-" * 80)
        for s in summaries:
            print(f"{str(s.date):<15} | Rp {s.total_revenue:<17,.2f} | Rp {s.total_spend:<17,.2f} | Rp {s.net_profit:<17,.2f}")

        print("\n" + "=" * 65)
        print("=== AGREGASI PER TANGGAL DARI GAMMETRIC ===")
        print("=" * 65)
        gam_rows = db.query(
            GAMMetric.date,
            func.sum(GAMMetric.revenue).label("rev"),
            func.sum(GAMMetric.impressions).label("imps")
        ).group_by(GAMMetric.date).order_by(GAMMetric.date.desc()).all()

        for g in gam_rows:
            print(f"Tanggal GAMMetric: {g.date} | Total Revenue (-8%): Rp {g.rev:,.2f} | Total Imps: {g.imps:,}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
