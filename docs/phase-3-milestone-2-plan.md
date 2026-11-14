# R1 / Phase 3 Milestone 2 implementation proposal

Status: **R1 implementation authorized separately after R0**. The [verification report](phase-3-milestone-2-verification.md) records actual results. Created during approved R0 documentation alignment on November 1, 2026. The requirements below preserve the approved proposal; they are not themselves verification evidence. The existing baseline is [Milestone 1](phase-3-milestone-1-verification.md): 86 retained passing tests and seven crash checkpoints.

## Boundaries

Use existing Python/SQL/DuckDB/PyArrow dependencies. Add a fixed sequential controller and read-only execution history. Preserve current transaction contents, analytical definitions, quarantine/deduplication semantics, CLI run/demo commands and returned fields. No scheduling, arbitrary DAGs, parallel execution, API, DataOps integration, detailed lineage, migration, cleanup, new dependency or cloud work.

## Stages and prerequisites

| Stage | Responsibility | Predecessor |
| --- | --- | --- |
| startup | Invocation UUID, trusted outcome evidence, path/budget checks | None |
| lock | Existing OS-owned writer exclusion | startup |
| connect | Existing compatibility gate before schema SQL | lock |
| recover | Resolve compatible committed-but-unpublished work before mutation | connect |
| ingest | Manifest/checksum verification and immutable raw copy | recover |
| prepare | Validation, version classification, quarantine, candidate state and reconciliation | ingest |
| commit | Canonical updates and committed ledger in one transaction | prepare |
| publish | Build/verify full snapshot and atomically replace pointer | commit |
| finalize | Final evidence and published ledger status | publish |

Quarantined input remains a quality outcome under existing semantics; it is not automatically a controller failure. Preserve existing `run`, `_execute`, `recover` and `finish` entry points and test seams.

## States and identities

Stages: pending -> running -> succeeded or failed. A failed prerequisite changes unstarted dependents to blocked. Interrupted is established only by controlled reconciliation, never inferred solely from age. Failed attempts are not rewritten as success; a later recovery attempt has a new identity. Database statuses committed/published remain authoritative for transaction durability.

Keep invocation_id per command and run_id per logical pipeline run. Add stage_id, unique attempt_id, attempt_number, invocation-local sequence and recovery_of_run_id. Recovery retains the original committed run ID but uses the new invocation and attempt. Normal duplicate delivery still creates a new run and uses existing row-level deduplication; no command-level content suppression.

## Retry and failure policy

Retain the existing maximum three attempts for retryable filesystem PermissionError operations with existing delays. Do not add an outer whole-stage retry loop. Lock contention, invalid contracts/checksums, invariants, storage-budget failure and incompatible recovery fail without automatic retries. An uncertain commit is resolved through the durable ledger on restart, never blindly repeated. Publication failure after commit remains pending and is recovered before new ingestion. Evidence failure must not replace an original exception or produce an unsupported success claim.

All seven existing fault checkpoints remain: raw_copy, before_commit, after_commit, parquet_write, before_pointer, after_pointer, evidence.

## History format and storage

Use additive filesystem evidence under the existing approved runtime. Preserve existing invocation outcome files. Add a UUID-keyed controller directory per new invocation with separate atomically published JSON transition records. Do not create a second authoritative database or persistent history cache.

Record schema_version, invocation_id, optional run_id, stage_id, attempt_id, attempt_number, sequence, record_type, occurred_at (UTC), elapsed_seconds (monotonic where applicable), status, sanitized error_type/error_code, recovery_of_run_id and bounded evidence_refs. Do not copy patient payloads, arbitrary exception strings or secret configuration values.

Proposed bounds: 8 KiB per record and 64 records per invocation. Reject unsupported versions, invalid IDs, duplicate sequences and escaping references. Bounds and any truncation must be explicit. The internal controller schema is separate from the existing future DataOps pipeline-event contract; R1 does not implement that contract.

Proposed CLI: `mediflow history --root <approved-root> --limit <n>`. It reads durable evidence only, without opening DuckDB. Historical runs without stage records remain visible as stage-history unavailable. Running records mean completion not recorded, not proof of a live process. Corrupt/missing/partial evidence is reported, not silently repaired, deleted or called successful. Bound/paginate results.

## Exact proposed file scope

Paths below are relative to the MediFlow project. This is the approved inventory; actual implemented files and executed results are listed in the verification report.

New source/contracts:
- `mediflow/orchestration.py`: Stage, StageAttempt, ExecutionContext, SequentialController; execute_stage, block_dependents, classify_failure.
- `mediflow/history.py`: write_transition, read_invocation, list_history, validate_record.
- `contracts/controller-record.schema.json`: internal evidence format documentation; standard-library semantic validation.

Existing code to modify:
- `mediflow/incremental.py`: retain entry points; extract prepare_batch, commit_candidate and finalize_evidence; wrap stage boundaries without splitting the canonical/ledger transaction.
- `mediflow/cli.py`: add history command, retain run/demo behavior.
- `mediflow/evidence.py`: only bounded atomic-record support reusing current serialization/fsync/replace behavior.

New tests:
- `tests/unit/test_orchestration.py`
- `tests/unit/test_history.py`
- `tests/integration/test_controller.py`
- `tests/integration/test_controller_recovery.py`

Documentation: update README, architecture, acceptance scenarios, recovery runbook and this plan; create `docs/phase-3-milestone-2-verification.md` only to record actual results after approved execution. Preserve all original 86 tests unchanged. Any required inventory expansion needs review. SQL, source schemas, dependencies, storage.connect and compatibility policy are outside the proposed code changes.

## Implementation sequence

1. Obtain explicit R1 approval after R0 review.
2. Capture pre-change source/evidence hashes and storage; preserve a reviewed source snapshot.
3. Define states and evidence validation; implement history and unit tests.
4. Extract current pipeline helpers without semantic changes.
5. Add controller boundaries, recovery attempts and failure propagation.
6. Add bounded history CLI.
7. Execute targeted tests, complete regression suite and one approved synthetic demonstration in new directories.
8. Report actual tests, faults, hashes, timing definitions, storage and limitations.

## Test and acceptance plan

| Area | Required result |
| --- | --- |
| Sequential success | Each stage once in order; unchanged pipeline results |
| Dependencies/transitions | Failed prerequisites block downstream side effects; illegal transitions rejected |
| Failures | Faults before/after side effects distinguish pre-commit failure from pending publication |
| Retry | Three operation attempts maximum; no multiplied/nested stage retries |
| Duplicate/concurrent execution | Writer exclusion; replay adds no canonical rows or metric changes |
| Recovery | All seven existing checkpoints pass; add interruptions after stage-start evidence and around finalization |
| Identity | Recovery links new invocation/attempt to original committed run |
| Persistence | Fresh process reads consistent history without database access |
| Corruption | Truncated JSON, duplicate sequence, unknown version, invalid ID, oversized payload and escaping path safely reported |
| Compatibility | Existing code/SQL/schema/config/dependency/legacy rejection tests pass |
| Evidence failures | Original exception retained; incomplete evidence never treated as complete success |
| Legacy history | Old manifests readable with stage-history limitation |
| Analytics | Independent complete-group/measure oracle and incremental/full-rebuild equivalence pass |
| Regression | Original 86 case identities retained; zero failures/errors/skips in required tests |
| Resources | Combined project/runtime below 2,000,000,000 bytes |

Final test count is measured, not promised. Use unique evidence filenames and preserve prior failures/results. Test duration is not pipeline throughput.

## Compatibility and rollback

Evidence is additive; existing manifests remain readable. New source/contracts alter compatibility fingerprints: resolve pending older runs with their original implementation before switching. Do not edit fingerprints to force recovery. Initial verification uses new isolated runtime directories.

Retain source snapshot and all R1 evidence on rollback. Old code must use a compatible completed runtime or a preserved matching runtime, never a pending R1 ledger entry. Never restore only current.json against a mismatched database. No automatic schema migration/downgrade or evidence deletion is included. Changes to live source during execution remain unsupported.

## Resources, effort and approval

No new dependencies. Proposed additional test/evidence reserve: up to 300 MB, within the existing 2 GB total, not an increased allowance. Measure before/after; full snapshots and repeated tests can exceed estimates. R0 effort estimate: 4-8 engineering hours. R1 implementation/unit coverage: 12-20 hours; integration/recovery/reporting: 12-20 hours. These are planning ranges, not measured work or delivery promises.

Approval needed for the exact code/test/document inventory, application tests and one synthetic demo, and new runtime evidence. Keep historical evidence, existing packages, no scheduling, no cloud, no Git/publication and no unrelated-project changes. R0 approval granted none of that execution scope; the subsequent explicit R1 instruction authorized implementation, tests and demonstration within these boundaries.
