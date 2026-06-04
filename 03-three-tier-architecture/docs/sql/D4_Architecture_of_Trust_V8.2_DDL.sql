-- ═══════════════════════════════════════════════════════════════════════════
-- D⁴ Architecture of Trust — V8.2 Production DDL
-- Mind Over Metadata LLC © 2026
-- Navigator: Peter Heller | Driver: Claude Sonnet 4.6
-- IP Attorney review pending — not for public disclosure
-- ═══════════════════════════════════════════════════════════════════════════
-- V8.2 Corrections from V8.1:
--   1. sdCustomerInfo.* domains replaced with coarser reusable domains:
--      sdLookupInfo.CodeLongDesc  — serves any code/description FQTN
--      sdBusinessInfo.Name        — serves any named entity FQTN
--      sdBusinessInfo.Email       — serves any email FQTN
--      One domain — N FQTNs — 60-80% enterprise reuse
--   2. Self-identifying sentinels — DomainName embedded at domain layer:
--      DEFAULT 'CodeLongDesc UNKNOWN' not 'UNKNOWN'
--      DEFAULT 'Name UNKNOWN' not 'UNKNOWN'
--      Visible in any result set without schema cross-reference
--   3. Three-layer constraint architecture:
--      Layer 1: DOMAIN — constitutional floor — WORM
--      Layer 2: COLUMN — ALTER TABLE SET DEFAULT — ColumnName sentinel
--      Layer 3: TABLE/DATABASE — ALTER TABLE ADD CONSTRAINT — cross-object
--   4. Column overrides via ALTER TABLE SET DEFAULT — ColumnName embedded:
--      'CustomerName UNKNOWN' — self-identifying at FQTN level
--      'CustomerEmail UNKNOWN@UNKNOWN.COM' — self-identifying at FQTN level
--   5. Table constraints via ALTER TABLE ADD CONSTRAINT:
--      chk_customer_name_length — length validation
--      chk_customer_email_format — email format or sentinel
--      chk_customer_code_name_paired — paired sentinel rule
--   6. RecordSource sentinel corrected:
--      DEFAULT 'RecordSource UNKNOWN' not 'SYSTEM'
-- ═══════════════════════════════════════════════════════════════════════════


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 1: Extensions
-- ═══════════════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_blake3";


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 2: Schemas
-- ═══════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS "sdSurrogateKey";  -- key governance
CREATE SCHEMA IF NOT EXISTS "sdSysTime";       -- temporal governance
CREATE SCHEMA IF NOT EXISTS "sdAuditInfo";     -- audit metadata
CREATE SCHEMA IF NOT EXISTS "sdMaskPolicy";    -- DDM governance
CREATE SCHEMA IF NOT EXISTS "sdLookupInfo";    -- V8.2: code/desc columns — any FQTN
CREATE SCHEMA IF NOT EXISTS "sdBusinessInfo";  -- V8.2: named entity columns — any FQTN
CREATE SCHEMA IF NOT EXISTS "PkSequence";      -- sequence generators
CREATE SCHEMA IF NOT EXISTS "Sales";           -- business tables
CREATE SCHEMA IF NOT EXISTS "Audit";           -- biography + burial tables


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 3: FQDN Domains
-- Physical type lives HERE — never in column declarations
-- Zero bare types anywhere — ever
-- Self-identifying sentinels — DomainName embedded in VARCHAR defaults
-- ═══════════════════════════════════════════════════════════════════════════

-- Surrogate key domains
CREATE DOMAIN "sdSurrogateKey"."UUIDv7"              AS UUID     NOT NULL;
CREATE DOMAIN "sdSurrogateKey"."SequenceObjectInt"   AS INTEGER  NOT NULL;
CREATE DOMAIN "sdSurrogateKey"."SequenceObjectBig"   AS BIGINT   NOT NULL;
CREATE DOMAIN "sdSurrogateKey"."BLAKE3Token"         AS BYTEA    NOT NULL;
CREATE DOMAIN "sdSurrogateKey"."BLAKE3_PAIR_HASH"    AS BYTEA    NOT NULL;

-- Temporal domains
CREATE DOMAIN "sdSysTime"."AuditTriggerTimestamp"
    AS TIMESTAMP WITH TIME ZONE NOT NULL;

-- Audit metadata domains
CREATE DOMAIN "sdAuditInfo"."IsDeleted"
    AS BOOLEAN NOT NULL DEFAULT FALSE;

-- V8.2: self-identifying sentinel — DomainName embedded
CREATE DOMAIN "sdAuditInfo"."RecordSource"
    AS VARCHAR(100) NOT NULL DEFAULT 'RecordSource UNKNOWN';

-- V8.2: IsDeleted domain governs lifecycle flag — two-value predicate compliant
CREATE DOMAIN "sdAuditInfo"."ShippingMode"
    AS VARCHAR(12) NOT NULL DEFAULT 'SYNCHRONOUS'
    CHECK (VALUE IN ('SYNCHRONOUS','ASYNCHRONOUS','DELAYED'));

-- ─────────────────────────────────────────────────────────────────────────
-- sdLookupInfo domains — V8.2
-- Serves any code/description column across any FQTN in any BGD
-- One domain — N FQTNs — WORM after deployment
-- Column override via ALTER TABLE SET DEFAULT embeds ColumnName
-- ─────────────────────────────────────────────────────────────────────────
-- VARCHAR(50): code and short description columns
-- Self-identifying sentinel: 'CodeLongDesc UNKNOWN' visible in any result
CREATE DOMAIN "sdLookupInfo"."CodeLongDesc"
    AS VARCHAR(50) NOT NULL DEFAULT 'CodeLongDesc UNKNOWN';

-- ─────────────────────────────────────────────────────────────────────────
-- sdBusinessInfo domains — V8.2
-- Serves any named entity or email column across any FQTN in any BGD
-- One domain — N FQTNs — WORM after deployment
-- ─────────────────────────────────────────────────────────────────────────
-- VARCHAR(200): any named business entity — Customer, Supplier, Employee
CREATE DOMAIN "sdBusinessInfo"."Name"
    AS VARCHAR(200) NOT NULL DEFAULT 'Name UNKNOWN';

-- VARCHAR(254): RFC 5321 maximum email length
CREATE DOMAIN "sdBusinessInfo"."Email"
    AS VARCHAR(254) NOT NULL DEFAULT 'Email UNKNOWN@UNKNOWN.COM';


-- ─────────────────────────────────────────────────────────────────────────
-- sdMaskPolicy FQDN Domains — DDM governance
-- Seven masking domains — Microsoft DDM function aligned
-- V8.2: self-identifying sentinel pattern applied
-- ─────────────────────────────────────────────────────────────────────────

CREATE DOMAIN "sdMaskPolicy"."MaskedInteger"
    AS INTEGER NOT NULL DEFAULT 0;

CREATE DOMAIN "sdMaskPolicy"."MaskedBigInt"
    AS BIGINT NOT NULL DEFAULT 0;

CREATE DOMAIN "sdMaskPolicy"."MaskedEmail"
    AS VARCHAR(320) NOT NULL DEFAULT 'MaskedEmail UNKNOWN@UNKNOWN.COM';

CREATE DOMAIN "sdMaskPolicy"."MaskedPII"
    AS VARCHAR(200) NOT NULL DEFAULT 'MaskedPII REDACTED';

CREATE DOMAIN "sdMaskPolicy"."MaskedCreditCard"
    AS VARCHAR(19) NOT NULL DEFAULT 'XXXX-XXXX-XXXX-0000';

CREATE DOMAIN "sdMaskPolicy"."MaskedDateTime"
    AS TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT '1900-01-01 00:00:00+00';

CREATE DOMAIN "sdMaskPolicy"."MaskedPhone"
    AS VARCHAR(20) NOT NULL DEFAULT 'MaskedPhone REDACTED';


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 4: Sequences
-- ═══════════════════════════════════════════════════════════════════════════

CREATE SEQUENCE "PkSequence"."CustomerPrivateSeq"
    START WITH 1000
    INCREMENT BY 1
    NO MAXVALUE
    CACHE 50
    OWNED BY NONE;

CREATE SEQUENCE "PkSequence"."MaskingPolicySeq"  START WITH 1000;
CREATE SEQUENCE "PkSequence"."RolePermissionSeq" START WITH 1000;
CREATE SEQUENCE "PkSequence"."AccessLogSeq"       START WITH 1000;


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 5: Tables
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────
-- "Sales"."Customer" — CURRENT STATE — V8.2
--
-- Five-Key Architecture:
--   Key 1: CustomerUUIDv7       PRIMARY KEY — non-clustered — 16-byte UUID
--   Key 2: CustomerPrivateSeqId clustered — 4-byte INT — internal only
--   Key 3: CustomerPrivateSeqIdBlake3  GENERATED — external token
--   Key 4: BLAKE3_PAIR_HASH     GENERATED — birth certificate
--   Key 5: IsDeleted            lifecycle flag — always FALSE here
--
-- V8.2 domain changes:
--   CustomerCode  → sdLookupInfo.CodeLongDesc  (was sdCustomerInfo.CustomerCode)
--   CustomerName  → sdBusinessInfo.Name        (was sdCustomerInfo.CustomerName)
--   Email         → sdBusinessInfo.Email       (was sdCustomerInfo.Email)
--   RecordSource  → sdAuditInfo.RecordSource   (sentinel corrected)
--
-- Column overrides applied via ALTER TABLE below — Layer 2
-- Table constraints applied via ALTER TABLE below — Layer 3
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE "Sales"."Customer" (

    -- KEY 1: PUBLIC IDENTITY — PRIMARY KEY — NON-CLUSTERED
    "CustomerUUIDv7"              "sdSurrogateKey"."UUIDv7"
                                   DEFAULT uuid_generate_v7()
                                   PRIMARY KEY,

    -- KEY 2: CLUSTERED INDEX KEY — NOT PRIMARY KEY — INTERNAL ONLY
    -- DDM: sdMaskPolicy.MaskedInteger — unprivileged sees 0
    "CustomerPrivateSeqId"        "sdSurrogateKey"."SequenceObjectInt"
                                   DEFAULT nextval(
                                       '"PkSequence"."CustomerPrivateSeq"'
                                   ) NOT NULL,

    -- KEY 3: EXTERNAL TOKEN — GENERATED ALWAYS AS STORED
    -- BLAKE3(CustomerPrivateSeqId) — bidirectionally dependent on Key 2
    "CustomerPrivateSeqIdBlake3"  "sdSurrogateKey"."BLAKE3Token"
                                   GENERATED ALWAYS AS (
                                       blake3("CustomerPrivateSeqId"::TEXT)
                                   ) STORED NOT NULL,

    -- Allen Interval — temporal governance — V8.2: <= not <
    "ValidFrom"                   "sdSysTime"."AuditTriggerTimestamp"
                                   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ValidTo"                     "sdSysTime"."AuditTriggerTimestamp"
                                   NOT NULL DEFAULT '9999-12-31 23:59:59+00',

    -- KEY 5: LIFECYCLE FLAG — always FALSE in this table
    "IsDeleted"                   "sdAuditInfo"."IsDeleted"
                                   NOT NULL DEFAULT FALSE,

    -- Business columns — V8.2: coarser reusable FQDNs
    -- Column-level overrides via ALTER TABLE SET DEFAULT below
    "CustomerCode"                "sdLookupInfo"."CodeLongDesc"     NOT NULL,
    "CustomerName"                "sdBusinessInfo"."Name"           NOT NULL,
    "Email"                       "sdBusinessInfo"."Email"          NOT NULL,
    "RecordSource"                "sdAuditInfo"."RecordSource"      NOT NULL,

    -- KEY 4: BIRTH CERTIFICATE — V8 CORRECTED INPUTS — immutable
    -- BLAKE3(UUIDv7 || '|' || SeqId) — seals identity + arrival
    "BLAKE3_PAIR_HASH"            "sdSurrogateKey"."BLAKE3_PAIR_HASH"
                                   GENERATED ALWAYS AS (
                                       blake3(
                                           "CustomerUUIDv7"::TEXT
                                           || '|' ||
                                           "CustomerPrivateSeqId"::TEXT
                                       )
                                   ) STORED NOT NULL,

    -- Structural constraints
    CONSTRAINT uq_customer_seq_id
        UNIQUE ("CustomerPrivateSeqId"),
    CONSTRAINT uq_customer_seq_blake3
        UNIQUE ("CustomerPrivateSeqIdBlake3"),
    CONSTRAINT chk_allen_interval
        CHECK ("ValidFrom" <= "ValidTo"),
    CONSTRAINT chk_is_deleted_main
        CHECK ("IsDeleted" = FALSE)
);


-- ═══════════════════════════════════════════════════════════════════════════
-- LAYER 2 — COLUMN OVERRIDES — ALTER TABLE SET DEFAULT
-- Self-identifying sentinel: ColumnName embedded — visible in any result
-- Narrows the WORM domain default to the FQTN-specific business context
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE "Sales"."Customer"
    ALTER COLUMN "CustomerCode"  SET DEFAULT 'CustomerCode UNKNOWN';
ALTER TABLE "Sales"."Customer"
    ALTER COLUMN "CustomerName"  SET DEFAULT 'CustomerName UNKNOWN';
ALTER TABLE "Sales"."Customer"
    ALTER COLUMN "Email"         SET DEFAULT 'CustomerEmail UNKNOWN@UNKNOWN.COM';
ALTER TABLE "Sales"."Customer"
    ALTER COLUMN "RecordSource"  SET DEFAULT 'RecordSource UNKNOWN';


-- ═══════════════════════════════════════════════════════════════════════════
-- LAYER 3 — TABLE CONSTRAINTS — ALTER TABLE ADD CONSTRAINT
-- Column-level, table-level, and cross-column business rules
-- Applied after CREATE TABLE — modular — governed independently
-- ═══════════════════════════════════════════════════════════════════════════

-- Column-level: CustomerName must have content when not sentinel
ALTER TABLE "Sales"."Customer"
    ADD CONSTRAINT chk_customer_name_length
        CHECK (LENGTH(TRIM("CustomerName")) >= 1);

-- Column-level: Email must be valid format or sentinel
ALTER TABLE "Sales"."Customer"
    ADD CONSTRAINT chk_customer_email_format
        CHECK ("Email" = 'CustomerEmail UNKNOWN@UNKNOWN.COM'
            OR "Email" LIKE '%_@_%._%');

-- Table-level: paired sentinel rule — if Code unknown, Name must be unknown
ALTER TABLE "Sales"."Customer"
    ADD CONSTRAINT chk_customer_code_name_paired
        CHECK (
            ("CustomerCode" = 'CustomerCode UNKNOWN')
            = ("CustomerName" = 'CustomerName UNKNOWN')
        );

-- Column-level: Allen Interval — ValidFrom <= ValidTo
-- (also enforced in CREATE TABLE — defense in depth)
ALTER TABLE "Sales"."Customer"
    ADD CONSTRAINT chk_customer_temporal_valid
        CHECK ("ValidFrom" <= "ValidTo");


-- ═══════════════════════════════════════════════════════════════════════════
-- "Audit"."Sales.Customer" — BIOGRAPHY + BURIAL — WORM
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE "Audit"."Sales.Customer" (

    "AuditUUIDv7"             "sdSurrogateKey"."UUIDv7"
                               DEFAULT uuid_generate_v7() PRIMARY KEY,
    "AuditSeqId"              "sdSurrogateKey"."SequenceObjectInt"
                               DEFAULT nextval(
                                   '"PkSequence"."CustomerPrivateSeq"'
                               ) NOT NULL,

    -- Source row linkage
    "CustomerUUIDv7"          "sdSurrogateKey"."UUIDv7"       NOT NULL,
    "CustomerPrivateSeqId"    "sdSurrogateKey"."SequenceObjectInt" NOT NULL,

    -- Previous state payload — V8.2 coarser domains
    "CustomerCode"            "sdLookupInfo"."CodeLongDesc"    NOT NULL,
    "CustomerName"            "sdBusinessInfo"."Name"          NOT NULL,
    "Email"                   "sdBusinessInfo"."Email"         NOT NULL,
    "RecordSource"            "sdAuditInfo"."RecordSource"     NOT NULL,

    -- Allen Interval — closed state
    "ValidFrom"               "sdSysTime"."AuditTriggerTimestamp" NOT NULL,
    "ValidTo"                 "sdSysTime"."AuditTriggerTimestamp" NOT NULL,

    -- IsDeleted: FALSE = superseded / TRUE = burial
    "IsDeleted"               "sdAuditInfo"."IsDeleted"        NOT NULL DEFAULT FALSE,

    -- Audit row birth certificate
    "BLAKE3_PAIR_HASH"        "sdSurrogateKey"."BLAKE3_PAIR_HASH"
                               GENERATED ALWAYS AS (
                                   blake3(
                                       "AuditUUIDv7"::TEXT
                                       || '|' ||
                                       "AuditSeqId"::TEXT
                                   )
                               ) STORED NOT NULL,

    -- Source row birth certificate — immutable witness
    "SourceBLAKE3_PAIR_HASH"  "sdSurrogateKey"."BLAKE3_PAIR_HASH" NOT NULL,

    CONSTRAINT uq_audit_seq     UNIQUE ("AuditSeqId"),
    CONSTRAINT chk_audit_allen  CHECK  ("ValidFrom" <= "ValidTo"),

    CONSTRAINT fk_audit_customer_uuid
        FOREIGN KEY ("CustomerUUIDv7")
        REFERENCES "Sales"."Customer" ("CustomerUUIDv7")
        -- NO CASCADE — covenant prohibition — CASCADE destroys audit chain
);


-- ═══════════════════════════════════════════════════════════════════════════
-- "Sales"."CustomerTokenLookup" — Reverse resolution
-- CustomerPrivateSeqIdBlake3 → CustomerPrivateSeqId — O(1)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE "Sales"."CustomerTokenLookup" (
    "CustomerPrivateSeqIdBlake3"  "sdSurrogateKey"."BLAKE3Token" PRIMARY KEY,
    "CustomerPrivateSeqId"        "sdSurrogateKey"."SequenceObjectInt" NOT NULL,
    "CreatedAt"                   "sdSysTime"."AuditTriggerTimestamp"
                                   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_token_to_customer
        FOREIGN KEY ("CustomerPrivateSeqId")
        REFERENCES "Sales"."Customer" ("CustomerPrivateSeqId")
        ON DELETE RESTRICT
);


-- ═══════════════════════════════════════════════════════════════════════════
-- sdMaskPolicy tables — MaskingPolicies, RolePermissions, AccessLog
-- (unchanged from V8.1 — see prior version for full content)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE "sdMaskPolicy"."MaskingPolicies" (
    "PolicyUUIDv7"  "sdSurrogateKey"."UUIDv7"
                     DEFAULT uuid_generate_v7() PRIMARY KEY,
    "PolicySeqId"   "sdSurrogateKey"."SequenceObjectInt"
                     DEFAULT nextval('"PkSequence"."MaskingPolicySeq"') NOT NULL,
    "SchemaName"    "sdAuditInfo"."RecordSource"  NOT NULL,
    "TableName"     "sdAuditInfo"."RecordSource"  NOT NULL,
    "ColumnName"    "sdAuditInfo"."RecordSource"  NOT NULL,
    "MaskDomain"    "sdAuditInfo"."RecordSource"  NOT NULL,
    "UnmaskLevel"   VARCHAR(10) NOT NULL DEFAULT 'COLUMN'
                     CHECK ("UnmaskLevel" IN ('COLUMN','TABLE','SCHEMA','DATABASE')),
    "ValidFrom"     "sdSysTime"."AuditTriggerTimestamp"
                     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ValidTo"       "sdSysTime"."AuditTriggerTimestamp"
                     NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    "IsDeleted"     "sdAuditInfo"."IsDeleted"     NOT NULL DEFAULT FALSE,
    "BLAKE3_PAIR_HASH" "sdSurrogateKey"."BLAKE3_PAIR_HASH"
                     GENERATED ALWAYS AS (
                         blake3("PolicyUUIDv7"::TEXT || '|' || "PolicySeqId"::TEXT)
                     ) STORED NOT NULL,
    CONSTRAINT uq_policy_seq  UNIQUE ("PolicySeqId"),
    CONSTRAINT uq_policy_col  UNIQUE ("SchemaName","TableName","ColumnName"),
    CONSTRAINT chk_policy_allen CHECK ("ValidFrom" <= "ValidTo")
);

CREATE TABLE "sdMaskPolicy"."RolePermissions" (
    "RoleUUIDv7"   "sdSurrogateKey"."UUIDv7"
                    DEFAULT uuid_generate_v7() PRIMARY KEY,
    "RoleSeqId"    "sdSurrogateKey"."SequenceObjectInt"
                    DEFAULT nextval('"PkSequence"."RolePermissionSeq"') NOT NULL,
    "RoleName"     "sdAuditInfo"."RecordSource"  NOT NULL,
    "RoleType"     VARCHAR(10) NOT NULL DEFAULT 'USER'
                    CHECK ("RoleType" IN ('GUEST','USER','ATTENDANT','LEAD','MANAGER','NAVIGATOR')),
    "UnmaskLevel"  VARCHAR(10) NOT NULL DEFAULT 'NONE'
                    CHECK ("UnmaskLevel" IN ('NONE','COLUMN','TABLE','SCHEMA','DATABASE')),
    "ValidFrom"    "sdSysTime"."AuditTriggerTimestamp"
                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ValidTo"      "sdSysTime"."AuditTriggerTimestamp"
                    NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    "IsDeleted"    "sdAuditInfo"."IsDeleted"     NOT NULL DEFAULT FALSE,
    "BLAKE3_PAIR_HASH" "sdSurrogateKey"."BLAKE3_PAIR_HASH"
                    GENERATED ALWAYS AS (
                        blake3("RoleUUIDv7"::TEXT || '|' || "RoleSeqId"::TEXT)
                    ) STORED NOT NULL,
    CONSTRAINT uq_role_seq   UNIQUE ("RoleSeqId"),
    CONSTRAINT uq_role_name  UNIQUE ("RoleName"),
    CONSTRAINT chk_role_allen CHECK ("ValidFrom" <= "ValidTo")
);

CREATE TABLE "sdMaskPolicy"."AccessLog" (
    "LogUUIDv7"    "sdSurrogateKey"."UUIDv7"
                    DEFAULT uuid_generate_v7() PRIMARY KEY,
    "LogSeqId"     "sdSurrogateKey"."SequenceObjectInt"
                    DEFAULT nextval('"PkSequence"."AccessLogSeq"') NOT NULL,
    "RoleName"     "sdAuditInfo"."RecordSource"  NOT NULL,
    "SchemaName"   "sdAuditInfo"."RecordSource"  NOT NULL,
    "TableName"    "sdAuditInfo"."RecordSource"  NOT NULL,
    "ColumnName"   "sdAuditInfo"."RecordSource"  NOT NULL,
    "MaskDomain"   "sdAuditInfo"."RecordSource"  NOT NULL,
    "WasMasked"    "sdAuditInfo"."IsDeleted"     NOT NULL,
    "ValidFrom"    "sdSysTime"."AuditTriggerTimestamp"
                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ValidTo"      "sdSysTime"."AuditTriggerTimestamp"
                    NOT NULL DEFAULT '9999-12-31 23:59:59+00',
    "BLAKE3_PAIR_HASH" "sdSurrogateKey"."BLAKE3_PAIR_HASH"
                    GENERATED ALWAYS AS (
                        blake3("LogUUIDv7"::TEXT || '|' || "LogSeqId"::TEXT)
                    ) STORED NOT NULL,
    CONSTRAINT uq_log_seq   UNIQUE ("LogSeqId"),
    CONSTRAINT chk_log_allen CHECK ("ValidFrom" <= "ValidTo")
);


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 6: Indexes
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_customer_clustered_seq
    ON "Sales"."Customer" USING btree ("CustomerPrivateSeqId");
CLUSTER "Sales"."Customer" USING idx_customer_clustered_seq;

CREATE INDEX idx_customer_temporal
    ON "Sales"."Customer"
    USING btree ("CustomerPrivateSeqId", "ValidFrom", "ValidTo");

CREATE INDEX idx_customer_email
    ON "Sales"."Customer" USING btree ("Email");

CREATE INDEX idx_audit_customer_seq
    ON "Audit"."Sales.Customer" USING btree ("AuditSeqId");
CLUSTER "Audit"."Sales.Customer" USING idx_audit_customer_seq;

CREATE INDEX idx_audit_customer_uuid
    ON "Audit"."Sales.Customer" USING btree ("CustomerUUIDv7");

CREATE INDEX idx_policy_seq
    ON "sdMaskPolicy"."MaskingPolicies" USING btree ("PolicySeqId");
CLUSTER "sdMaskPolicy"."MaskingPolicies" USING idx_policy_seq;

CREATE INDEX idx_role_seq
    ON "sdMaskPolicy"."RolePermissions" USING btree ("RoleSeqId");
CLUSTER "sdMaskPolicy"."RolePermissions" USING idx_role_seq;

CREATE INDEX idx_log_seq
    ON "sdMaskPolicy"."AccessLog" USING btree ("LogSeqId");
CLUSTER "sdMaskPolicy"."AccessLog" USING idx_log_seq;


-- ═══════════════════════════════════════════════════════════════════════════
-- BOOTSTRAP BLOCK — Step 7: Triggers
-- ═══════════════════════════════════════════════════════════════════════════

-- WORM: Audit biography — append only
CREATE OR REPLACE FUNCTION "Audit".enforce_worm_sales_customer()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'WORM violation: % is prohibited on "Audit"."Sales.Customer". '
        'The biography table is append-only by covenant.',
        TG_OP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_worm_audit_sales_customer
    BEFORE UPDATE OR DELETE ON "Audit"."Sales.Customer"
    FOR EACH ROW EXECUTE FUNCTION "Audit".enforce_worm_sales_customer();

-- WORM: AccessLog — append only
CREATE OR REPLACE FUNCTION "sdMaskPolicy".enforce_worm_access_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'WORM violation: % is prohibited on "sdMaskPolicy"."AccessLog". '
        'The DDM access audit log is append-only by covenant.',
        TG_OP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_worm_access_log
    BEFORE UPDATE OR DELETE ON "sdMaskPolicy"."AccessLog"
    FOR EACH ROW EXECUTE FUNCTION "sdMaskPolicy".enforce_worm_access_log();

-- Token lookup auto-populate
CREATE OR REPLACE FUNCTION "Sales"."fn_CustomerTokenLookup_Insert"()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Sales"."CustomerTokenLookup" (
        "CustomerPrivateSeqIdBlake3", "CustomerPrivateSeqId"
    ) VALUES (
        NEW."CustomerPrivateSeqIdBlake3", NEW."CustomerPrivateSeqId"
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_customer_token_lookup
    AFTER INSERT ON "Sales"."Customer"
    FOR EACH ROW
    EXECUTE FUNCTION "Sales"."fn_CustomerTokenLookup_Insert"();


-- ═══════════════════════════════════════════════════════════════════════════
-- DEVELOPER EXPERIENCE — Golden Record Lifecycle
-- ═══════════════════════════════════════════════════════════════════════════

-- INSERT — all governance automatic — sentinels visible if data missing
INSERT INTO "Sales"."Customer"
    ("CustomerCode","CustomerName","Email","RecordSource")
VALUES ('CUST-00042','Acme Corporation','acme@acme.com','CRM');
-- CustomerCode sentinel: 'CustomerCode UNKNOWN' if omitted
-- CustomerName sentinel: 'CustomerName UNKNOWN' if omitted
-- Email sentinel:        'CustomerEmail UNKNOWN@UNKNOWN.COM' if omitted
-- RecordSource sentinel: 'RecordSource UNKNOWN' if omitted

-- UPDATE — audit row FIRST — atomic transaction
BEGIN;
    INSERT INTO "Audit"."Sales.Customer"
        ("CustomerUUIDv7","CustomerPrivateSeqId",
         "CustomerCode","CustomerName","Email","RecordSource",
         "ValidFrom","ValidTo","IsDeleted","SourceBLAKE3_PAIR_HASH")
    SELECT "CustomerUUIDv7","CustomerPrivateSeqId",
           "CustomerCode","CustomerName","Email","RecordSource",
           "ValidFrom", CURRENT_TIMESTAMP, FALSE, "BLAKE3_PAIR_HASH"
    FROM   "Sales"."Customer"
    WHERE  "CustomerUUIDv7" = '[target-uuid]';

    UPDATE "Sales"."Customer"
    SET    "CustomerName" = 'Acme Corporation Ltd',
           "ValidFrom"    = CURRENT_TIMESTAMP
    WHERE  "CustomerUUIDv7" = '[target-uuid]'
    AND    "ValidTo"         = '9999-12-31 23:59:59+00';
COMMIT;

-- DELETE — burial record FIRST — atomic transaction
BEGIN;
    INSERT INTO "Audit"."Sales.Customer"
        ("CustomerUUIDv7","CustomerPrivateSeqId",
         "CustomerCode","CustomerName","Email","RecordSource",
         "ValidFrom","ValidTo","IsDeleted","SourceBLAKE3_PAIR_HASH")
    SELECT "CustomerUUIDv7","CustomerPrivateSeqId",
           "CustomerCode","CustomerName","Email","RecordSource",
           "ValidFrom", CURRENT_TIMESTAMP, TRUE, "BLAKE3_PAIR_HASH"
    FROM   "Sales"."Customer"
    WHERE  "CustomerUUIDv7" = '[target-uuid]';

    DELETE FROM "Sales"."Customer"
    WHERE  "CustomerUUIDv7" = '[target-uuid]';
COMMIT;


-- ═══════════════════════════════════════════════════════════════════════════
-- VERSION HISTORY
-- ═══════════════════════════════════════════════════════════════════════════
-- V7   Pre-2026-05-13  Three-key. BLAKE3 inputs: SeqId+ValidFrom (wrong)
-- V8   2026-05-13      Four-key. BLAKE3 inputs corrected: UUIDv7|SeqId
--                      IsDeleted added. sdMaskPolicy added. Allen <= fixed
-- V8.1 2026-05-15      Five-key. CustomerPrivateSeqIdBlake3 added.
--                      CustomerTokenLookup + trigger. Two UNIQUE constraints
-- V8.2 2026-05-15      Coarser domains: sdLookupInfo.CodeLongDesc,
--                      sdBusinessInfo.Name, sdBusinessInfo.Email.
--                      Self-identifying sentinels: '{DomainName} UNKNOWN'.
--                      Three-layer constraint architecture.
--                      Column overrides: ALTER TABLE SET DEFAULT.
--                      Table constraints: ALTER TABLE ADD CONSTRAINT.
--                      Claim 4: MDM reduction. ADR-068.
-- ═══════════════════════════════════════════════════════════════════════════

-- © 2026 Peter Heller / Mind Over Metadata LLC
-- D⁴ Architecture of Trust V8.2 DDL
-- FreedomTower — Session C — 2026-05-15
-- Navigator: Peter Heller | Driver: Claude Sonnet 4.6
-- IP Attorney review pending — not for public disclosure
