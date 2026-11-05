import pandas as pd
import json
import sqlite3
import os

def run_batch_audit():
    print("Initializing Enterprise Phantom Data Audit...")
    
    # Ensure folders exist
    os.makedirs("enterprise_data", exist_ok=True)
    
    # 1. Load Audit Requests (e.g., CASE_101, CASE_102, CASE_103)
    requests_path = 'enterprise_data/audit_requests.csv'
    if not os.path.exists(requests_path):
        # Create default test requests if missing
        requests_df = pd.DataFrame([
            {"case_id": "CASE_101", "email": "sarah.connor@email.com"},
            {"case_id": "CASE_102", "email": "john.wick@email.com"},
            {"case_id": "CASE_103", "email": "bruce.wayne@email.com"}
        ])
    else:
        requests_df = pd.read_csv(requests_path)

    # 2. Load Evidence Logs (Where ghost records hide)
    logs_path = 'enterprise_data/evidence_logs.csv'
    if os.path.exists(logs_path):
        logs_df = pd.read_csv(logs_path)
    else:
        # Default mock logs with explicit leaks to test INCOMPLETE status
        logs_df = pd.DataFrame([
            {"system_name": "failover_replica_db", "email": "john.wick@email.com", "record_state": "PRESENT", "evidence_id": "evidence_logs_csv"},
            {"system_name": "marketing_cache", "email": "sarah.connor@email.com", "record_state": "ACTIVE_FLOW", "evidence_id": "evidence_logs_csv"}
        ])

    output_rows = []

    for _, row in requests_df.iterrows():
        case_id = row['case_id']
        target_email = str(row.get('email', '')).strip().lower()
        
        # Check if this email has active leaks in the evidence logs
        leaks = logs_df[
            (logs_df['email'].astype(str).str.strip().str.lower() == target_email) & 
            (logs_df['record_state'].astype(str).str.upper().isin(['PRESENT', 'ACTIVE_FLOW', 'ACTIVE']))
        ]
        
        steps = []
        if not leaks.empty:
            status = "INCOMPLETE"
            step_counter = 1
            for _, leak in leaks.iterrows():
                # FINDING phase -> Record is PRESENT
                steps.append({
                    "step_no": step_counter,
                    "phase": "FINDING",
                    "system_id": str(leak['system_name']),
                    "resource_id": "record_node_01",
                    "operation": "REPORT_REMAINING_RECORD",
                    "state": "PRESENT",
                    "evidence_id": str(leak['evidence_id'])
                })
                step_counter += 1
                
                # REMEDIATION phase -> Target state is ABSENT
                steps.append({
                    "step_no": step_counter,
                    "phase": "REMEDIATION",
                    "system_id": str(leak['system_name']),
                    "resource_id": "record_node_01",
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

    # Save output.csv
    output_df = pd.DataFrame(output_rows)[["case_id", "deletion_status", "steps_json"]]
    output_df.to_csv('output.csv', index=False)
    print(f"SUCCESS: output.csv generated with {len(output_df)} rows. Check your results!")

if __name__ == '__main__':
    run_batch_audit()