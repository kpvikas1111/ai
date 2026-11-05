
        BEGIN TRANSACTION;
        CREATE TABLE customer_profiles_failover_replica (resource_id TEXT PRIMARY KEY, email TEXT NOT NULL);
        INSERT INTO "customer_profiles_failover_replica" VALUES('account_005','leila.haddad@yahoo.com');
        CREATE TABLE customer_profiles_primary (resource_id TEXT PRIMARY KEY, email TEXT NOT NULL);
        COMMIT;
        