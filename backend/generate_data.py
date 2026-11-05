import os
import pandas as pd

os.makedirs("enterprise_data", exist_ok=True)

requests = pd.DataFrame({
    "case_id": ["CASE_101", "CASE_102", "CASE_103"],
    "email": ["sarah.connor@email.com", "john.wick@email.com", "bruce.wayne@email.com"],
    "workflow_claim": ["COMPLETE", "PENDING", "COMPLETE"]
})
requests.to_csv("enterprise_data/audit_requests.csv", index=False)

identities = pd.DataFrame({
    "user_id": ["USR_01", "USR_02", "USR_03"],
    "current_email": ["sarah.connor@email.com", "john.wick@email.com", "bruce.wayne@email.com"],
    "old_email": ["s.connor_1984@email.com", "none", "batman@email.com"]
})
identities.to_csv("enterprise_data/identities.csv", index=False)

evidence = pd.DataFrame({
    "system_name": ["primary_db", "marketing_sync", "primary_db", "backup_server"],
    "email": ["sarah.connor@email.com", "s.connor_1984@email.com", "john.wick@email.com", "bruce.wayne@email.com"],
    "record_state": ["DELETED", "ACTIVE_FLOW", "PRESENT", "DELETED"]
})
evidence.to_csv("enterprise_data/evidence_logs.csv", index=False)

print("Proprietary enterprise datasets successfully generated in /enterprise_data/")
