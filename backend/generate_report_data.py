import pandas as pd
import json
import os

def generate_full_report_data():
    print("Extracting full dataset for report.html...")
    
    output_path = '../output.csv' # Reading from repository root
    if not os.path.exists(output_path):
        output_path = 'output.csv' # Fallback path check
        
    if not os.path.exists(output_path):
        print("CRITICAL ERROR: output.csv not found. Run your full batch processor first!")
        return

    output_df = pd.read_csv(output_path)
    report_records = []
    
    for _, row in output_df.iterrows():
        case_id = row['case_id']
        status = row['deletion_status']
        
        try:
            steps = json.loads(row['steps_json'])
        except Exception:
            steps = []
        
        # Build clean descriptive text for the HTML table based on findings/status
        if status == "INCOMPLETE" and len(steps) > 0:
            primary_leak = steps.get('system_id', 'target_system')
            description = f"Data leak detected. Lingering records found in system node: {primary_leak}."
            solution = f"Execute {len(steps)//2} sequential remediation protocol(s) to purge active records."
        elif status == "COMPLETE":
            description = "Deletion request verified. No replication drift or active log residues detected."
            solution = "All system nodes synchronized and validated as ABSENT."
        else:
            description = "Deletion request evaluated as not applicable to active data scopes."
            solution = "No action required."

        report_records.append({
            "case_id": case_id,
            "description": description,
            "status": status,
            "solution_summary": solution,
            "steps_count": len(steps),
            "steps_json": json.dumps(steps, indent=2)
        })

    # Export as a JavaScript data array for the browser interface
    js_content = f"const auditReportData = {json.dumps(report_records, indent=4)};"
    
    os.makedirs("../frontend", exist_ok=True)
    with open("../frontend/audit_data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"SUCCESS: Generated frontend/audit_data.js with all {len(report_records)} individual test case records.")

if __name__ == '__main__':
    generate_full_report_data()