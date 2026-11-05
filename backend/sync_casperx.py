import pandas as pd
import json
import os
import re

print("--- Starting CASPERX Compliance Sync ---")

req_df = pd.read_csv("deletion_requests.csv")
id_df = pd.read_csv("user_identities.csv")

files_to_search = {}
for f in os.listdir("."):
    if f.endswith(".json") or f.endswith(".txt") or f.endswith(".sql"):
        with open(f, "r", encoding="utf-8", errors="ignore") as file:
            files_to_search[f] = file.read()

leak_summary = []
for _, row in req_df.iterrows():
    case_id = str(row.get("case_id", "")).strip()
    base_email = str(row.get("email", "")).strip().lower()
    if not base_email or base_email == "nan": continue
    
    identifiers = set([base_email])
    match = id_df[id_df["email"].astype(str).str.lower() == base_email]
    if not match.empty:
        m = match.iloc[0]
        for key in ["user_id", "phone", "email_hash"]:
            val = str(m.get(key, "")).strip()
            if val and val != "nan": identifiers.add(val)
            
    user_found_files = []
    for fname, content in files_to_search.items():
        content_lower = content.lower()
        found = False
        for ident in identifiers:
            ident_lower = ident.lower()
            if ident_lower.startswith("user_"):
                if re.search(r"\b" + re.escape(ident_lower) + r"\b", content_lower): found = True
            else:
                if ident_lower in content_lower: found = True
            if found: break
        if found:
            user_found_files.append(fname)
            
    if user_found_files:
        leak_summary.append({"case_id": case_id, "files": user_found_files, "status": "INCOMPLETE"})
    else:
        leak_summary.append({"case_id": case_id, "files": [], "status": "COMPLETE"})

total_requests = len(req_df)
incomplete_cases = sum(1 for x in leak_summary if x["status"] == "INCOMPLETE")
complete_cases = total_requests - incomplete_cases

failover_count = sum(1 for x in leak_summary if any("failover" in f for f in x["files"]))
marketing_count = sum(1 for x in leak_summary if any("analytics" in f for f in x["files"]))
cache_count = sum(1 for x in leak_summary if any("connector" in f or "cache" in f for f in x["files"]))
legacy_count = sum(1 for x in leak_summary if any("snapshot" in f or "inventory" in f for f in x["files"]))

print("\n[METRICS CALCULATED]")
print(f"Total Requests: {total_requests}")
print(f"Compliant (Complete): {complete_cases}")
print(f"Violations (Incomplete): {incomplete_cases}")
print(f"Vectors -> Failover: {failover_count}, Marketing: {marketing_count}, Cache: {cache_count}, Legacy: {legacy_count}")

dashboard_metrics = {
    "total_requests": total_requests,
    "compliant_complete": complete_cases,
    "violations_incomplete": incomplete_cases,
    "vectors": {
        "failover_replica": failover_count,
        "marketing_logs": marketing_count,
        "cache_server": cache_count,
        "legacy_backup": legacy_count
    },
    "cases": leak_summary
}

with open("casperx_metrics.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_metrics, f, indent=4)

print("\nSuccessfully generated 'casperx_metrics.json'!")

