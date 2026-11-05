import pandas as pd
import json
import sqlite3
import os

# --- 1. IDENTITY RESOLUTION ---
def resolve_all_emails(target_email):
    """Checks the dataset for current and old emails."""
    emails_to_search = [target_email]
    identities_path = "enterprise_data/identities.csv"
    
    if os.path.exists(identities_path):
        try:
            df = pd.read_csv(identities_path)
            user_row = df[df['current_email'].astype(str).str.lower() == target_email.lower()]
            if not user_row.empty:
                old_email = str(user_row.iloc[0].get('old_email', '')).lower()
                if old_email != 'none' and pd.notna(old_email) and old_email != 'nan' and old_email != '':
                    emails_to_search.append(old_email)
        except Exception as e:
            print(f"Identity resolution skipped/error: {e}")
    return emails_to_search

# --- 2. MULTI-SOURCE EVIDENCE SCANNER ---
def scan_for_ghost_data(target_email):
    """Scans enterprise evidence logs and snapshots for data leaks."""
    issues = []
    
    # A. Scan CSV Activity Logs
    activity_path = "enterprise_data/evidence_logs.csv"
    if os.path.exists(activity_path):
        try:
            df = pd.read_csv(activity_path)
            if 'email' in df.columns and 'record_state' in df.columns:
                leaks = df[(df['email'].astype(str).str.lower() == target_email.lower()) & 
                           (df['record_state'].isin(['PRESENT', 'ACTIVE_FLOW', 'ACTIVE', 'RESTORED']))]
                for _, row in leaks.iterrows():
                    issues.append({
                        "system_id": row.get('system_name', 'unknown_system'),
                        "resource_id": row.get('resource_id', 'csv_record'),
                        "evidence_id": row.get('evidence_id', 'evidence_logs_csv')
                    })
        except Exception:
            pass

    # B. Scan SQL Evidence Snapshot
    sql_path = "enterprise_data/snapshot.sql"
    if os.path.exists(sql_path):
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
            cursor.execute("""
                SELECT resource_id, email 
                FROM customer_profiles_failover_replica
                EXCEPT
                SELECT resource_id, email 
                FROM customer_profiles_primary;
            """)
            for record in cursor.fetchall():
                if record[1].lower() == target_email.lower():
                    issues.append({
                        "system_id": "failover_replica",
                        "resource_id": record[0],
                        "evidence_id": "sql_snapshot_01"
                    })
        except Exception:
            pass
        finally:
            conn.close()
                    
    return issues

# --- 3. PROCESS THE BATCH DATASET ---
def generate_final_output():
    print("1/3 Loading Enterprise Audit Requests...")
    requests_path = 'enterprise_data/audit_requests.csv'
    
    if not os.path.exists(requests_path):
        print(f"CRITICAL ERROR: Could not find {requests_path}.")
        print("Ensure your dataset files are inside the enterprise_data/ directory.")
        return

    requests_df = pd.read_csv(requests_path)
    output_rows = []
    
    print(f"2/3 Processing {len(requests_df)} cases... Evaluating evidence paths.")
    
    for _, row in requests_df.iterrows():
        case_id = row['case_id']
        base_email = str(row.get('email', '')).lower()
        
        # Resolve Identity (Current + Aliases)
        all_emails = resolve_all_emails(base_email)
        
        # Scan all evidence sources for leaks
        leaks = []
        for email in all_emails:
            if email:
                leaks.extend(scan_for_ghost_data(email))
            
        # Format the strict steps_json output structure
        steps = []
        if leaks:
            status = "INCOMPLETE"
            step_counter = 1
            for leak in leaks:
                steps.append({
                    "step_no": step_counter, 
                    "phase": "FINDING", 
                    "system_id": leak['system_id'], 
                    "resource_id": leak['resource_id'], 
                    "operation": "REPORT_REMAINING_RECORD", 
                    "state": "PRESENT", 
                    "evidence_id": leak['evidence_id']
                })
                step_counter += 1
                steps.append({
                    "step_no": step_counter, 
                    "phase": "REMEDIATION", 
                    "system_id": leak['system_id'], 
                    "resource_id": leak['resource_id'], 
                    "operation": "DELETE_RECORD", 
                    "state": "ABSENT", 
                    "evidence_id": ""
                })
                step_counter += 1
        else:
            status = "COMPLETE"
            steps = [{
                "step_no": 1, 
                "phase": "VERIFICATION", 
                "system_id": "all_enterprise_systems", 
                "resource_id": "N/A", 
                "operation": "VERIFY_RECORD_ABSENT", 
                "state": "ABSENT", 
                "evidence_id": "multi_source_scan"
            }]
            
        output_rows.append({
            "case_id": case_id, 
            "deletion_status": status, 
            "steps_json": json.dumps(steps)
        })
        
    print("3/3 Formatting and Sorting Output...")
    output_df = pd.DataFrame(output_rows)[["case_id", "deletion_status", "steps_json"]]
    
    # Sort strictly by case_id
    output_df = output_df.sort_values(by="case_id")
    
    output_df.to_csv('output.csv', index=False)
    print(f"SUCCESS: output.csv generated with {len(output_df)} data rows.")

if __name__ == '__main__':
    generate_final_output()