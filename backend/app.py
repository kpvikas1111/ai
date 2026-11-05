import os
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Auto-setup data to prevent server crashes
def setup_enterprise_data():
    os.makedirs("enterprise_data", exist_ok=True)
    if not os.path.exists("enterprise_data/identities.csv"):
        pd.DataFrame([{"current_email": "sarah.connor@email.com", "old_email": "s.connor_1984@email.com"}]).to_csv("enterprise_data/identities.csv", index=False)
    if not os.path.exists("enterprise_data/evidence_logs.csv"):
        pd.DataFrame([{"system_name": "marketing_db", "email": "s.connor_1984@email.com", "record_state": "ACTIVE_FLOW"}, {"system_name": "csv_logs", "email": "john.wick@email.com", "record_state": "PRESENT"}]).to_csv("enterprise_data/evidence_logs.csv", index=False)
    if not os.path.exists("enterprise_data/snapshot.sql"):
        with open("enterprise_data/snapshot.sql", "w", encoding="utf-8") as f:
            f.write("BEGIN TRANSACTION; CREATE TABLE customer_profiles_failover_replica (resource_id TEXT PRIMARY KEY, email TEXT NOT NULL); INSERT INTO \"customer_profiles_failover_replica\" VALUES('account_005','leila.haddad@yahoo.com'); CREATE TABLE customer_profiles_primary (resource_id TEXT PRIMARY KEY, email TEXT NOT NULL); COMMIT;")

def resolve_all_emails(target_email):
    emails = [target_email]
    if os.path.exists("enterprise_data/identities.csv"):
        df = pd.read_csv("enterprise_data/identities.csv")
        row = df[df['current_email'].str.lower() == target_email.lower()]
        if not row.empty and pd.notna(row.iloc[0]['old_email']):
            emails.append(str(row.iloc[0]['old_email']).lower())
    return emails

def scan_for_ghost_data(target_email):
    issues = []
    if os.path.exists("enterprise_data/snapshot.sql"):
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        try:
            with open("enterprise_data/snapshot.sql", 'r') as f: c.executescript(f.read())
            c.execute("SELECT resource_id, email FROM customer_profiles_failover_replica EXCEPT SELECT resource_id, email FROM customer_profiles_primary;")
            for rec in c.fetchall():
                if rec[1].lower() == target_email.lower(): issues.append({"system_id": "failover_replica", "resource_id": rec[0]})
        except: pass
        finally: conn.close()
    
    if os.path.exists("enterprise_data/evidence_logs.csv"):
        df = pd.read_csv("enterprise_data/evidence_logs.csv")
        leaks = df[(df['email'].str.lower() == target_email.lower()) & (df['record_state'].isin(['PRESENT', 'ACTIVE_FLOW']))]
        for _, row in leaks.iterrows(): issues.append({"system_id": row['system_name'], "resource_id": "csv_record"})
    return issues

@app.route('/api/audit', methods=['POST'])
def run_live_audit():
    try:
        data = request.json
        case_id = data.get('case_id', 'UNKNOWN')
        base_email = data.get('email', '').strip().lower()

        time.sleep(1.2) # UI Animation Delay
        setup_enterprise_data() # Ensure data exists

        leaks = []
        for email in resolve_all_emails(base_email):
            leaks.extend(scan_for_ghost_data(email))

        steps = []
        if leaks:
            status = "INCOMPLETE"
            reason = f"Ghost records detected across {len(leaks)} system node(s), including historical aliases."
            remediation_plan = "Execute strict data deletion protocol on the flagged systems."
            count = 1
            for leak in leaks:
                steps.append({"step_no": count, "phase": "FINDING", "system_id": leak['system_id'], "resource_id": leak['resource_id'], "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT"})
                steps.append({"step_no": count+1, "phase": "REMEDIATION", "system_id": leak['system_id'], "resource_id": leak['resource_id'], "operation": "DELETE_RECORD", "state": "ABSENT"})
                count += 2
        else:
            status = "COMPLETE"
            reason = "Topology Synchronized. No data leaks detected."
            remediation_plan = "No action required."
            steps = [{"step_no": 1, "phase": "VERIFICATION", "system_id": "all_systems", "resource_id": "N/A", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT"}]

        return jsonify({"case_id": case_id, "target_email": base_email, "status": status, "reason": reason, "remediation_plan": remediation_plan, "steps": steps}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    setup_enterprise_data()
    print("CASPERX LIVE SERVER READY ON PORT 5000")
    app.run(debug=True, port=5000)