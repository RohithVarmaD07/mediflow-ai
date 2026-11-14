> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# R1 / Phase 3 Milestone 2 verification

Completed locally November 1, 2026 (America/New_York). Scope: fixed sequential execution controller, durable stage records, read-only history CLI, focused tests and documentation. No subsequent milestone started.

## Implementation and preserved behavior

The controller executes startup, lock, connect, recover, ingest, prepare, commit, publish and finalize in order. Illegal or duplicate transitions are rejected; an operation failure blocks its unstarted dependents. There is no new whole-stage retry loop: existing filesystem retries remain bounded to three operation attempts.

Existing run/recover/finish entry points remain. Preparation and commit logic were extracted without changing canonical/ledger transaction contents. Recovery uses the original committed run ID and a new invocation/stage attempt. SQL, source validation, deduplication, storage/compatibility logic and snapshot publication code were not changed. The original 86 test files/cases remain intact.

Stage records are atomic, sequence-numbered JSON under approved-runtime invocation directories. They are separate from the existing proposed DataOps contract. History validates records and transitions, reports partial/corrupt evidence, and requires final-stage plus invocation success evidence before reporting success. It reads no DuckDB database and does not create missing paths. Legacy manifests remain visible without invented stage history.

## Exact authored file inventory

All entries are relative to `<original-project>`.

Modified (seven):
- `mediflow/incremental.py`
- `mediflow/cli.py`
- `README.md`
- `docs/architecture.md`
- `docs/acceptance-scenarios.md`
- `docs/recovery-runbook.md`
- `docs/phase-3-milestone-2-plan.md`

Created (eight):
- `mediflow/orchestration.py`
- `mediflow/history.py`
- `contracts/controller-record.schema.json`
- `tests/unit/test_orchestration.py`
- `tests/unit/test_history.py`
- `tests/integration/test_controller.py`
- `tests/integration/test_controller_recovery.py`
- `docs/phase-3-milestone-2-verification.md`

The plan allowed evidence.py support changes, but existing atomic_json was sufficient and that file stayed unchanged. No scope expansion or dependency change was needed.

## Automated execution

| Execution | Passed | Failures/errors/skips | Console seconds | JUnit artifact under approved runtime |
| --- | ---: | --- | ---: | --- |
| Initial targeted new tests | 39 | 0/0/0 | 72.42 | tests/results-r1-targeted-a.xml |
| First full regression | 131 | 0/0/0 | 390.80 | tests/results-r1-regression-a.xml |
| Targeted history fix | 34 | 0/0/0 | 50.36 | tests/results-r1-history-fix.xml |
| Final full regression | **133** | **0/0/0** | **540.84** | tests/results-r1-final.xml |

Final JUnit suite time: **540.786 seconds**. Case-identity comparison with `tests/results-milestone1-final.xml` found **86 original cases, zero missing, 47 new**. These are execution measurements, not promised performance targets. All pytest executions in this task passed; the demonstration nevertheless exposed the defect described below.

Final command, from the MediFlow project:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q --tb=short --basetemp=<approved-runtime>\tests\r1-final --junitxml=<approved-runtime>\tests\results-r1-final.xml
```

Coverage includes ordering, illegal/duplicate transitions, blocked dependents, bounded operation retries, secondary evidence failures, record bounds, schema/sequence/transition corruption, incomplete outcomes, legacy reads, root filtering, read-only CLI, no database access and recovered run/attempt identities. Existing independent full-rebuild, exact analytical group/measure, late correction, tombstone, compatibility rejection and idempotent replay tests passed.

All seven original crash checkpoints passed: raw_copy, before_commit, after_commit, parquet_write, before_pointer, after_pointer, evidence. Added tests verify recovery attempt identity at five post-commit points and subprocess exits after an ingest-start record and after final-stage completion. These establish tested process-crash behavior, not hardware power-loss durability.

## Discovered defect and retained evidence

The first demo produced correct data and replay results, but its history response included an unattributed corruption error from a deliberately damaged, unrelated test fixture. The reader loaded full histories before applying root filtering. Evidence is preserved in `runs/r1-demo.json` (demo-ca6783bc-6625-4d82-9a26-e27af9083a0c): 22.109564 seconds internal, 24.497668 seconds including subprocess startup, four successful invocations and 24 matching output hashes, plus the erroneous history attribution.

The fix validates the first record/root reference before loading a full history. Corruption belonging to the requested pipeline remains visible; unreadable headers that cannot be assigned to a root are reported in a separate unattributed_errors field. The reader also retains only the requested number of result bodies. New regression tests cover foreign versus local corruption. The targeted fix and final full suite passed. No evidence was deleted or rewritten to hide the defect.

## Final synthetic demonstration

Evidence: `runs/r1-demo-final.json`; structured execution verification: `r1-execution-verification.json` under the approved runtime.

Demo directory: `runs/demo-f6b90f55-ebf1-47ec-9cb0-b59cd7da48a4`.

| Invocation | Actual result |
| --- | --- |
| Baseline | 10,000 accepted inserts: 1,000 patients, 5,000 appointments, 4,000 encounters |
| Late corrections | Two accepted updates; no inserts |
| Dirty batch | One invalid record, two duplicates, one stale record; no canonical changes |
| Baseline replay | 9,998 duplicates and two stale records; zero inserts/updates/tombstones |

All four reconciliation differences were zero. Replay canonical digest and all analytical/entity output hashes were identical to the preceding state. All **24 output hashes** were independently checked. Each run's compatibility fingerprint matched the tested current source/configuration. History returned **four succeeded items, no errors, no unattributed errors and no truncation**.

Final internal demo duration: **28.076159 seconds**; subprocess duration: **31.394248 seconds**. This is one synthetic workload measurement. It is not a controlled comparison with older demos, a throughput SLA, or an enterprise-scale result. Stage timings exclude their start-record write; wrapper/run measurements include additional evidence overhead. Peak process RAM was not measured.

## Preservation and resources

`r1-preservation.json` retains pre-change file hashes and a source snapshot. Comparing all 9,796 original files found exactly the seven authorized existing-file changes above, **9,789 unchanged files**, and **zero missing files**. No pre-existing runtime artifact, original test, dependency file, Agentic DataOps file or portfolio file changed. The eight new authored files above are the complete project additions.

Combined final logical storage, including the MediFlow environment, preserved history, new tests/demos and report: **741106313 bytes**, below the **2,000,000,000-byte** cap and within the proposed 300 MB additional reserve. No installation, cloud access, scheduling activation, commit or publication occurred. All runtime writes stayed under `<approved-runtime>`.

## Limitations and next gate

- Filesystem failure can prevent durable outcome/history evidence; original exceptions are preserved where a secondary write fails.
- Interrupted invocation records are not rewritten or automatically declared recovered. The database ledger, not history alone, determines commit status.
- Corrupt or unattributable historical headers cannot reliably establish prior stage-attempt ordinals. Unknown-root corruption is reported separately; no automatic repair exists.
- History is bounded to 64 records per invocation, 8 KiB per record, 10,000 scanned candidates and at most 1,000 returned items. Results use UUID order, not chronological pagination. Recovery attempt discovery stops at the scan limit.
- History is local evidence, not tamper-proof authentication. Single-writer Windows assumptions, full snapshot regeneration, Python memory limits and preflight-only disk budgeting remain.
- Preserved evidence increases scan cost; performance figures are measured locally without a controlled before/after benchmark.
- Root coordination documents remain the dated R0 snapshot because they were outside R1's edit inventory. No unrelated documentation was silently updated.

Recommended next milestone: separately review R2 operational-event, quality-report and lineage contracts. R2, scheduling, DataOps integration and cloud work have not begun. Explicit approval is required before further implementation.
