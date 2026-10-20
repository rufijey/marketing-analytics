"""
apply_sql_views.py
Automated runner to execute analytical SQL Views (Marts) in Google BigQuery.
"""

import os
import re
import glob
from google.cloud import bigquery
from google.oauth2 import service_account

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

def apply_views():
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    
    sql_files = sorted(glob.glob("sql/*.sql"))
    print(f"[*] Found {len(sql_files)} SQL files...")
    
    for fpath in sql_files:
        fname = os.path.basename(fpath)
        if fname.startswith("01_"):
            # Skip raw DDL as table is loaded by ETL pipeline
            print(f"[~] Skipping DDL (table initialized by pipeline): {fname}")
            continue
        
        print(f"[*] Executing {fname}...")
        with open(fpath, "r", encoding="utf-8") as f:
            sql_query = f.read()

        # Extract target view identifier to remove any conflicting tables
        match = re.search(r"CREATE\s+OR\s+REPLACE\s+VIEW\s+`?([^`\s]+)`?", sql_query, re.IGNORECASE)
        if match:
            target_view_id = match.group(1).replace("`", "")
            try:
                existing = client.get_table(target_view_id)
                if existing.table_type == "TABLE":
                    print(f"[!] Object {target_view_id} exists as legacy TABLE. Dropping to replace with VIEW...")
                    client.delete_table(target_view_id)
            except Exception:
                pass
            
        job = client.query(sql_query)
        job.result()
        print(f"[+] Successfully deployed View from: {fname}")

    print("\n[*] Deployed entities in dataset martech_dwh:")
    tables = list(client.list_tables("martech_dwh"))
    for t in tables:
        tbl_info = client.get_table(f"martech_dwh.{t.table_id}")
        print(f"  - {t.table_id} ({tbl_info.table_type})")

if __name__ == "__main__":
    apply_views()
