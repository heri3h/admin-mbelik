#!/usr/bin/env python3
import sys
import os
import sqlite3

# Verified OCID mappings for all 25 sub-accounts
VERIFIED_OCIDS = {
    "255-105-1790": "6677093661",  # fun4kids
    "794-665-9174": "1350300855",  # spotgames
    "858-142-9480": "1201608932",  # skuy
    "421-878-4427": "1238372556",  # mbelik
    "808-296-3952": "1295632265",  # glee
    "324-608-5080": "1353856964",  # enew
    "795-987-6337": "1195291415",  # baleq
    "241-049-6062": "6818109511",  # play
    "741-470-4445": "6451875796",  # mko
    "717-875-2215": "1472492541",  # yay
    "997-936-0093": "1465263575",  # vinn
    "437-274-1623": "1264979705",  # nmas
    "830-281-7458": "6462534234",  # joy
    "742-590-8186": "1523436617",  # zse
    "881-243-1778": "6579788316",  # gemol
    "463-389-1978": "1591594469",  # jest
    "500-750-3327": "1385744343",  # xdr
    "698-749-4193": "7686315760",  # polpa
    "990-153-8358": "1584780477",  # kiew
    "951-848-4329": "1384552733",  # wew
    "839-143-9756": "7107757889",  # alt
    "257-312-4470": "6586647543",  # pnt
    "639-202-3042": "1410139644",  # henden
    "556-016-8891": "1145366603",  # nub
    "682-994-0913": "6534459274",  # kedung
}

def migrate_and_populate(db_path="ad_analytics.db"):
    if not os.path.exists(db_path):
        # Try finding in parent or current dir
        if os.path.exists(os.path.join("..", db_path)):
            db_path = os.path.join("..", db_path)
        else:
            print(f"Database file {db_path} not found.")
            return

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Ensure columns exist
    cur.execute("PRAGMA table_info(google_ads_accounts)")
    existing_cols = [c[1] for c in cur.fetchall()]
    print(f"Existing columns in google_ads_accounts: {existing_cols}")

    if "remaining_balance" not in existing_cols:
        print("Adding remaining_balance column...")
        cur.execute("ALTER TABLE google_ads_accounts ADD COLUMN remaining_balance FLOAT DEFAULT 0.0")

    if "ocid" not in existing_cols:
        print("Adding ocid column...")
        cur.execute("ALTER TABLE google_ads_accounts ADD COLUMN ocid VARCHAR(50)")

    conn.commit()

    # 2. Update existing accounts
    cur.execute("SELECT id, customer_id, ocid FROM google_ads_accounts")
    accounts = cur.fetchall()
    print(f"Found {len(accounts)} registered accounts in database.")

    updated_count = 0
    for acc_id, cid, current_ocid in accounts:
        clean_cid = cid.replace("-", "").strip()
        matched_ocid = None

        for target_cid, ocid_val in VERIFIED_OCIDS.items():
            if target_cid == cid or target_cid.replace("-", "") == clean_cid:
                matched_ocid = ocid_val
                break

        if matched_ocid and current_ocid != matched_ocid:
            cur.execute("UPDATE google_ads_accounts SET ocid = ? WHERE id = ?", (matched_ocid, acc_id))
            print(f"  -> Updated account {cid} with OCID {matched_ocid}")
            updated_count += 1

    conn.commit()
    print(f"Successfully updated {updated_count} accounts with verified OCIDs.")
    conn.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "ad_analytics.db"
    migrate_and_populate(db_file)
