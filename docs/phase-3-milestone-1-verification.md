> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# Phase 3 Milestone 1 verification

Scope: execution hardening only. No orchestration, scheduling, monitoring service, AWS integration, dependency changes, commits, or publication.

## Implementation

Correctness-critical relationship and row-accounting assertions now raise explicit runtime errors before database mutation. They remain active under Python `-O`.

Each invocation receives a UUID and durable startup-stage/outcome JSON under `<approved-runtime>/invocations`. Successful records link to the run ID; run manifests contain the invocation ID. Storage validation, lock, connection, and recovery initialization exceptions are recorded. Exception types and allowlisted safety codes avoid copying arbitrary exception messages. Failure to save a final outcome does not replace an already-active error.

Committed pending runs require matching fingerprints covering implementation files, SQL/schema, configuration, contracts, Python, DuckDB, and PyArrow. The gate runs before schema SQL and again before recovery publication. Incompatible and legacy fingerprint-free pending runs are blocked. Connection initialization closes its connection on failure. Published historical runs remain readable. Canonical updates and ledger insertion retain one transaction; publication and duplicate classification retain their existing protocols.

## Changed files

All paths below are relative to the MediFlow project directory.

Modified:
- `mediflow/incremental.py`
- `mediflow/storage.py`
- `README.md`
- `docs/recovery-runbook.md`

Created:
- `mediflow/compatibility.py`
- `tests/integration/test_hardening.py`
- `docs/phase-3-milestone-1-verification.md`

## Executed verification

Final command from the MediFlow directory:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q --tb=short --basetemp=<approved-runtime>\tests\milestone1-final --junitxml=<approved-runtime>\tests\results-milestone1-final.xml
```

Final result: **86 passed; zero failures, errors, or skips**. Console elapsed time: **264.24 seconds**; JUnit suite time: **264.180 seconds**. The preliminary run passed 82 tests in 206.68 seconds; its evidence is retained as `tests/results-milestone1-a.xml`. There were no failed suite executions during this task. Intentional fault injections raised the expected errors or subprocess exit code and were passing tests.

JUnit case-name comparison against `tests/results-quality.xml` found all original 67 cases present and 19 additional cases. The final suite includes independent full-rebuild comparisons, exact analytical group sets and measures, late corrections, deletion cases, and idempotent replay. No separate full-size demo or performance benchmark was run for this hardening-only milestone; suite time is not a pipeline throughput measurement.

New coverage:
- Five injected startup failures: storage budget, target validation, writer-lock acquisition, database connection, recovery initialization.
- Actual writer contention and actual rejected target path.
- Invocation-to-run success linkage.
- Six incompatible pending-recovery cases: implementation, analytical SQL, schema SQL, configuration, dependency, and legacy missing fingerprint. These simulate mismatched saved fingerprints without changing installed packages or project source. Each verifies rejection, preserved canonical state and committed status, no published pointer, and successful recovery/replay after restoration in the test database.
- Relationship and row-accounting invariant failures before transaction mutation.
- Both invariants in real optimized-Python subprocesses.
- Outcome-write failure preserves the original startup exception.

All seven existing crash checkpoints passed: `raw_copy`, `before_commit`, `after_commit`, `parquet_write`, `before_pointer`, `after_pointer`, and `evidence`. Retry success/exhaustion and writer exclusion also passed. Production-source inspection found no remaining Python assertions.

## Evidence and resources

Evidence root: `<approved-runtime>`.

- Final automated results: `tests/results-milestone1-final.xml`.
- Preliminary automated results: `tests/results-milestone1-a.xml`.
- Prior quality results retained: `tests/results-quality.xml`.
- Per-invocation records: `invocations/<invocation-id>.json`.
- Isolated regression run artifacts: `tests/<UUID>/runs/<run-id>/` and corresponding databases/snapshots.

Final combined logical file storage, including project environment and all approved runtime evidence: **0523477881 bytes**, below the **2,000,000,000-byte** allowance. Dependencies were neither installed nor upgraded. No external systems were contacted. Existing evidence was not deleted.

Git still reports the project and coordination folders as untracked; no staging or commits were performed. `git diff --check` returned no errors, but with untracked files it does not establish a baseline content diff. This report lists edits performed in this task; unrelated projects were not edited.

## Limitations and next milestone

Durable evidence cannot be guaranteed if its trusted directory is inaccessible or storage is exhausted. An abrupt process exit leaves the invocation's last recorded state; automatic reconciliation of invocation outcomes is not implemented. The storage reserve is not a filesystem quota. Exact fingerprint matching can block harmless changes and intentionally blocks older pending runs lacking a fingerprint. Files must remain unchanged during execution; no hot-reload or live schema migration is supported. Fingerprints detect compatibility differences, not malicious tampering or arbitrary database corruption. Existing local single-writer, full-snapshot, memory, and power-loss limitations remain.

Proposed next step, requiring explicit approval: Milestone 2's small sequential execution controller and execution-history design, preserving this recovery gate and transaction model. No Milestones 2–7 work has begun.
