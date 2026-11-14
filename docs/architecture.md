# Implemented architecture through Phase 3 Milestone 2

```mermaid
flowchart LR
  S[Invocation identity and startup evidence] --> C[Path, budget, writer lock and connection]
  C --> K[Pending-recovery compatibility gate]
  K --> G[Seeded JSON Lines] --> I[Checksum-verified immutable raw copy]
  I --> V[Explicit validation]
  V --> Q[Reason-coded quarantine]
  V --> D[Duplicate and source-version classification]
  D --> T[Transactional DuckDB canonical records]
  T --> A[SQL analytics and typed Parquet]
  A --> P[Immutable snapshot and atomic pointer]
  T --> R[Committed-run recovery ledger]
  R --> A
```

`mediflow.generate` creates source batches with hashes and counts. `ingest` validates the manifest and preserves raw bytes. `validation` enforces structure, values, and candidate-state relationships. `deduplicate` classifies each valid version once. `incremental` commits canonical records and the recoverable run ledger in one transaction. `analytics` publishes a complete Parquet generation before replacing `current.json`. Evidence is linked through the UUID run identity.

Single-writer exclusion uses a Windows OS file lock, released even when the child process exits abruptly. Recover pending publication before any newer mutation. Existing raw/snapshot hashes are checked on reuse. No reader should scan staging; resolve `current.json` once and read that immutable snapshot.

Phase 2 rebuilds analytical snapshots after incremental canonical merges. It does not yet implement partition-only recomputation, multi-process readers of DuckDB, a scheduler, dbt, a dashboard, full DataOps event-contract integration, or AI insights. The original AWS mapping (S3, Glue, Athena, Step Functions, CloudWatch) remains design-only and is not tested by this implementation.

## Milestone 1 safeguards and evidence

Each invocation gets a UUID and startup outcome evidence before target validation. Storage, lock, database and recovery initialization failures are recorded when the trusted evidence directory is writable. Pending recovery checks implementation, SQL/schema, configuration, contracts and runtime dependency fingerprints before schema SQL and again before publication. Incompatible or fingerprint-free pending runs block safely. Explicit relationship/accounting errors remain active under optimized Python.

The canonical merge and committed run ledger remain one transaction. Snapshot publication retains its atomic pointer protocol. These safeguards are covered by [hardening tests](../tests/integration/test_hardening.py) and the [86-test retained report](phase-3-milestone-1-verification.md). No application tests were rerun for R0.

## R1 sequential execution and history

The controller enforces startup -> lock -> connect -> recover -> ingest -> prepare -> commit -> publish -> finalize. Failure records block unstarted dependents; no outer whole-stage retries are added. Existing bounded filesystem retries remain unchanged. `prepare_batch` and `commit_candidate` extract existing behavior; canonical records and the committed ledger remain one transaction. `finish` wraps publication and finalization, retaining the existing entry point.

A context-local controller connects the existing entry points without changing their public signatures. Recovery uses a child controller for publish/finalize, sharing the invocation sequence while retaining the original committed run ID. Stage attempts have UUIDs and ordinal numbers. The database ledger remains the authority for commit status.

Immutable transition JSON files live under the approved runtime `invocations/<invocation-id>/controller/`. Existing invocation outcome files remain at `invocations/<invocation-id>.json`. New records include an approved-runtime-relative root reference so the read-only history command can filter a pipeline without querying its writer database. Per-record size is limited to 8 KiB and each invocation to 64 records. Scans are bounded to 10,000 candidates and results to 1,000; limits/truncation are explicit. The reader filters by a validated root reference before loading full stage history and retains only the requested number of result bodies. Unreadable headers that cannot be attributed to a root are reported separately as unattributed errors, not as failures of the requested pipeline.

History validates individual records, sequence/attempt identity and dependency transitions. A successful result needs final-stage evidence and a successful invocation outcome. Historical runs without stage history are labeled accordingly. Hash/fingerprint and database compatibility behavior is unchanged. This is an internal history schema, not full DataOps integration. See the [plan](phase-3-milestone-2-plan.md) and [execution report](phase-3-milestone-2-verification.md).
