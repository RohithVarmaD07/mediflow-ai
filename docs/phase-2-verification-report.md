> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# Phase 2 verification report

Latest quality-improvement verification: **67 tests passed, zero failures/errors/skips**. The original Phase 2 evidence below is retained; the final section records the subsequent quality improvements and proposed Git baseline.

Report finalized: November 1, 2026 (America/New_York). Run evidence retains its original UTC timestamps.

## Outcome

Implemented and verified locally: seeded patients/appointments/encounters, checksum-addressed ingestion, validation/quarantine, duplicates/conflicts/stale versions, transactional incremental merges, late corrections, DuckDB SQL, typed Parquet snapshots, bounded retry, writer exclusion, crash recovery, and run evidence. No AWS execution, production-readiness, AI inference, or remote CI claim.

## Dependency and runtime preflight

Eight approved wheel hashes matched PyPI; bundled licenses and conditional requirements were reviewed. Offline hash-locked installation and pip check passed. Native DuckDB/PyArrow imports and interoperability were exercised by actual tests and demos. See dependency-licenses.md and SECURITY.md for scoped advisory applicability. No other dependency version was changed.

AppData ancestors were ordinary directories without reparse points. Inherited ACLs were inspected; a file fsync plus atomic replacement probe passed. Active state was created only under the approved AppData runtime. No ACL, OneDrive setting, or approval policy was changed.

## Actual automated results

- Final release suite: 41 passed, 0 failed, 0 skipped, 50.23 seconds.
- Composition: 20 unit cases and 21 integration cases.
- Four seeded independent full-history oracle comparisons passed; canonical records and all analytical measures matched.
- Seven forced-subprocess-exit checkpoints passed, plus writer exclusion, retry success, and retry exhaustion.
- Local JUnit evidence: `<approved-runtime>/tests/results-release.xml`.

## Failures retained and corrected

1. Initial suite: 17 failed, 24 passed in 18.31 seconds. Daily SQL aliases needed explicit AS. results-first.xml retains the failures. The next suite passed 41/41.
2. First full-size demo: a row-by-row merge exhausted the configured 512 MB DuckDB memory limit after 49.78 seconds. The transaction failed and its manifest records the exception. Replaced individual inserts with one Arrow-backed batch merge, retaining the same memory limit. Tests and three fresh full-size demos then passed.
3. Baseline source chronology was tightened so completed encounters precede the as-of time; the final suite includes that assertion.

Failed full-size run evidence: `<approved-runtime>/runs/demo-cd009006-c8fa-428b-abb6-286762188ff1/runs/3072a862-d55e-47e8-a449-2f948b66f6f4/manifest.json`.

## Demonstration results

Each of the three independent demo executions ran four batches:

| Batch | Inputs | Accepted | Duplicate | Stale | Invalid | Persisted effect |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Baseline | 10000 | 10000 | 0 | 0 | 0 | 1000 patients, 5000 appointments, 4000 encounters |
| Late correction | 2 | 2 | 0 | 0 | 0 | Two existing records updated |
| Dirty/repeated input | 4 | 0 | 2 | 1 | 1 | No canonical changes; one quarantine record |
| Baseline replay | 10000 | 0 | 9998 | 2 | 0 | No canonical changes |

Every run reconciled exactly (difference 0). The final canonical digest and all Parquet file hashes were identical across the three independent demos. Tests additionally cover new entity insertion, tombstones, conflicting versions, and corrected quarantine resubmission. A failed run can contain planned accepted/change counts; its failed status means those counts must not be interpreted as committed writes.

## Measured performance

Existing Windows x64 laptop, Python 3.13.2, DuckDB 1.4.2, PyArrow 21.0.0; 2 DuckDB threads and 512 MB database memory limit. Each execution uses fresh state, 10,000 baseline records, then corrections/dirty/replay batches. OS caches were not flushed. Times include generation, evidence, snapshot publication, and resource checks; they are not isolated SQL benchmarks.

| Execution | In-process demo seconds | Including subprocess startup | Evidence directory |
| --- | ---: | ---: | --- |
| 1 | 7.1734 | 8.1493 | `<approved-runtime>\runs\demo-7d0ff7bd-243b-4469-8af4-dc758c6ad239` |
| 2 | 7.1246 | 8.1402 | `<approved-runtime>\runs\demo-86f1be95-0b2a-4979-81c7-f81ee18f7673` |
| 3 | 7.2426 | 8.2499 | `<approved-runtime>\runs\demo-5c4ad465-adc5-4044-a108-9d5eec9e7292` |

Median in-process demo: 7.1734 seconds. Raw combined evidence: `<approved-runtime>/runs/performance.json`.

Final output row counts:
- patients.parquet: 1000 rows; SHA-256 `d377ae4cc04984a18628ed233eeefe68ca3db7beb4bc77cf491472410279be99`
- appointments.parquet: 5000 rows; SHA-256 `839d5d4dd8cf4c8e60f6c40007795b698a9df1315588c86963c982036e05e2a6`
- encounters.parquet: 4000 rows; SHA-256 `48ca31484becf9956e9eee6fa1680c4f1fd60eae5161eb3d4bd805fb99265e07`
- patient_summary.parquet: 1000 rows; SHA-256 `57763f6117e46e951d2b904419de8b2a409845bb4b129d47b0ca13b71f803a7c`
- daily_appointments.parquet: 31 rows; SHA-256 `49cbe050b22bd95ac5b93eaa5876589531ba53db539a98220e9fe1cca89325dd`
- daily_encounters.parquet: 25 rows; SHA-256 `ccff1360d3957157313d682f9afec6b6d45e555f66e494ce01073011c2a8c173`

## Resource usage

Logical file bytes measured immediately before writing this report: 369,182,028 bytes (369.18 MB), including the entire MediFlow folder/environment and external runtime, all retained wheels, failed runs, and tests. Limit: 2,000,000,000 bytes. This is file length, not filesystem allocated size. The report itself adds a small amount; final validation rechecks the limit. Peak process memory was not measured. The database memory limit is not a total-process cap.

## Files modified

```text
README.md
.gitignore
pyproject.toml
SECURITY.md
docs/architecture.md
docs/data-model.md
docs/acceptance-scenarios.md
.github/workflows/ci.yml
```

## Files created

```text
config/demo.toml
docs/data-dictionary.md
docs/dependency-licenses.md
docs/incremental-processing.md
docs/phase-2-execution-plan.md
docs/phase-2-verification-report.md
docs/recovery-runbook.md
mediflow/__init__.py
mediflow/__main__.py
mediflow/analytics.py
mediflow/cli.py
mediflow/config.py
mediflow/deduplicate.py
mediflow/evidence.py
mediflow/generate.py
mediflow/incremental.py
mediflow/ingest.py
mediflow/quarantine.py
mediflow/recovery.py
mediflow/storage.py
mediflow/validation.py
requirements-win-py313.lock
requirements-win-py313.txt
sql/daily_appointments.sql
sql/daily_encounters.sql
sql/patient_summary.sql
sql/reconciliation.sql
sql/schema.sql
tests/conftest.py
tests/integration/test_incremental_equivalence.py
tests/integration/test_late_arrivals.py
tests/integration/test_parquet_publication.py
tests/integration/test_pipeline.py
tests/integration/test_quarantine_reprocessing.py
tests/integration/test_recovery.py
tests/unit/test_deduplication.py
tests/unit/test_evidence.py
tests/unit/test_generation.py
tests/unit/test_path_security.py
tests/unit/test_validation.py
tests/unit/test_version_ordering.py
```

Generated files: approved .venv installation and the external runtime install/wheelhouse/tests/runs/source/raw/state/staging/snapshots trees. Exact runtime contents are linked by manifests. No unrelated project file, root coordination document, Git history, or remote was modified.

## Verification limits and remaining work

- Windows single-writer implementation; the runtime root is deliberately fixed to the approved local location. Portability requires a reviewed configuration change.
- Analytical outputs are rebuilt from incremental canonical state; selective partition recomputation and production scheduling are not implemented.
- Referentially invalid winner batches are quarantined as a group; there is no automatic deferred-parent queue.
- Tests establish process-crash recovery, not power-loss, disk-corruption, or distributed recovery guarantees.
- Synthetic demo distributions are deliberately simple. No real patient data, clinical accuracy, or healthcare compliance certification.
- Native wheel advisories were reviewed for applicability; no comprehensive scanner or penetration test was run. Linux pytest activation needs a new security review.
- Run-state events are local evidence; full integration with the original pipeline-event schema remains future work.
- The CI file remains manual metadata-only and has not run remotely. YAML service validation, GitHub publication, and all external automation remain unverified.
- No dbt, dashboard, AI insights, AWS resource, public website, model, or paid service was introduced.

## Phase 3 recommendations (not started)

Propose partition-aware analytical rebuilding, richer quality summaries and lineage, a reviewed dbt integration, expanded synthetic healthcare scenarios, and the full DataOps event contract. Retain independent reconciliation and recovery checks. Obtain owner approval for exact files, dependencies, and scope before any Phase 3 execution.

## Phase 2 quality improvements — November 1, 2026

The independent Python oracle now compares complete analytical key sets before checking metrics. Duplicate keys fail before dictionary indexing can hide them. Comparisons run after every seeded incremental stage, including late corrections and replay, and compare complete active entity identifiers as well.

Added 26 cases: 12 deliberate group-set corruptions (missing, unexpected, duplicate, and empty outputs across all three analytical tables), 10 incorrect-metric cases, three empty-history output cases, and one integrated edge-history scenario. That scenario covers completed/cancelled/no-show appointments, a cancelled-only group with NULL rate, a walk-in, a patient with no activity, duplicate inputs, late date/facility corrections, removal of entire groups through tombstones, and replay. No application code or dependencies changed.

### Actual regression results

- Full suite: **67 passed, zero failures, errors, or skips**. Console duration: **113.39 seconds**; JUnit suite duration: **113.322 seconds**.
- All four seeded full-history comparisons passed at each stage.
- All seven forced-exit checkpoints passed: raw_copy, before_commit, after_commit, parquet_write, before_pointer, after_pointer, evidence.
- Existing writer exclusion, bounded retry, quarantine, and duplicate-idempotency tests passed.
- No new application defect was found. Deliberately damaged output cases were rejected as intended; they are passing verifier tests, not observed application failures. Earlier Phase 2 failures remain retained.
- JUnit evidence: `<approved-runtime>/tests/results-quality.xml`.

### Synthetic demonstration

Four successful pipeline runs: 10,000 baseline inserts; two late updates; a dirty batch with one quarantine, two duplicates and one stale row; replay with 9,998 duplicates and two stale rows. Replay inserted/updated/deleted nothing and preserved the canonical digest and output hashes. All reconciliation differences were zero. Verified 24 Parquet hashes against the saved manifests.

Measured demo time: **13.0495 seconds**; **15.0107 seconds** including process startup. This is one additional measurement, not a statistically controlled comparison with earlier runs. Evidence: `<approved-runtime>/runs/quality-demo.json`; demo directory: `<approved-runtime>\runs\demo-47308ad7-49c3-4fcf-90e6-a255f304fc00`. The evidence also records the exact updated test-file SHA-256.

Logical working storage measured before this report update: **414,757,474 bytes (414.76 MB)** across the project/environment and runtime, below the approved 2,000,000,000-byte allowance. Evidence and test artifacts were retained. Peak RAM and allocated disk blocks were not measured.

### Exact files modified by this task

```text
.gitignore
README.md
docs/acceptance-scenarios.md
docs/incremental-processing.md
docs/phase-2-verification-report.md
tests/integration/test_incremental_equivalence.py
```

No new authored file was needed. Generated JUnit and demo evidence remain under the approved AppData runtime.

### Proposed initial Git baseline

Git remains on unborn `master`, with no tracked/staged files, commits, or remotes. The following **51 authored MediFlow files** are the complete proposed baseline. They include the two existing foundation files unchanged by Phase 2. Do not use a repository-wide `git add .`: root coordination documents, Agentic DataOps, and portfolio files are outside this baseline scope. The previously approved independent-repository separation remains a later action; it was not performed here.

```text
mediflow-ai/.github/dependabot.yml
mediflow-ai/.github/workflows/ci.yml
mediflow-ai/.gitignore
mediflow-ai/README.md
mediflow-ai/SECURITY.md
mediflow-ai/config/demo.toml
mediflow-ai/contracts/pipeline-event.schema.json
mediflow-ai/docs/acceptance-scenarios.md
mediflow-ai/docs/architecture.md
mediflow-ai/docs/data-dictionary.md
mediflow-ai/docs/data-model.md
mediflow-ai/docs/dependency-licenses.md
mediflow-ai/docs/incremental-processing.md
mediflow-ai/docs/phase-2-execution-plan.md
mediflow-ai/docs/phase-2-verification-report.md
mediflow-ai/docs/recovery-runbook.md
mediflow-ai/mediflow/__init__.py
mediflow-ai/mediflow/__main__.py
mediflow-ai/mediflow/analytics.py
mediflow-ai/mediflow/cli.py
mediflow-ai/mediflow/config.py
mediflow-ai/mediflow/deduplicate.py
mediflow-ai/mediflow/evidence.py
mediflow-ai/mediflow/generate.py
mediflow-ai/mediflow/incremental.py
mediflow-ai/mediflow/ingest.py
mediflow-ai/mediflow/quarantine.py
mediflow-ai/mediflow/recovery.py
mediflow-ai/mediflow/storage.py
mediflow-ai/mediflow/validation.py
mediflow-ai/pyproject.toml
mediflow-ai/requirements-win-py313.lock
mediflow-ai/requirements-win-py313.txt
mediflow-ai/sql/daily_appointments.sql
mediflow-ai/sql/daily_encounters.sql
mediflow-ai/sql/patient_summary.sql
mediflow-ai/sql/reconciliation.sql
mediflow-ai/sql/schema.sql
mediflow-ai/tests/conftest.py
mediflow-ai/tests/integration/test_incremental_equivalence.py
mediflow-ai/tests/integration/test_late_arrivals.py
mediflow-ai/tests/integration/test_parquet_publication.py
mediflow-ai/tests/integration/test_pipeline.py
mediflow-ai/tests/integration/test_quarantine_reprocessing.py
mediflow-ai/tests/integration/test_recovery.py
mediflow-ai/tests/unit/test_deduplication.py
mediflow-ai/tests/unit/test_evidence.py
mediflow-ai/tests/unit/test_generation.py
mediflow-ai/tests/unit/test_path_security.py
mediflow-ai/tests/unit/test_validation.py
mediflow-ai/tests/unit/test_version_ordering.py
```

The existing environment, runtime data, generated datasets, database files, caches, credentials, keys, and temporary output are excluded by ignore rules or remain outside the checkout. MediFlow's own ignore file now additionally excludes `.credentials/`, coverage fragments/output, test-results, and `*.tmp`, so these exclusions do not depend on the parent coordination repository. No proposed authored path is accidentally ignored.

A targeted scan of authored text found no private-key blocks, AWS access-key patterns, GitHub/OpenAI token patterns, credential-bearing URLs, or literal assigned secrets. No generated dataset/database/temp file appeared in the authored baseline. This is a bounded pattern review, not proof that all sensitive information is absent. Five authored files contain local absolute paths, including the approved username/runtime location; review these before any future public publication. No real patient data or production credentials are part of the dataset design.

**Commit gate:** Git user.name and user.email are not configured. Obtain owner-approved author identity and explicit commit approval before configuring identity, staging, or committing. No Git settings were modified.

Proposed initial commit message:

```text
feat(mediflow): add verified local healthcare data pipeline

Implement synthetic ingestion, validation, incremental DuckDB state,
Parquet analytics, recoverable publication, and run evidence.
Verify complete analytical groups and metrics with independent rebuilds,
edge cases, replay checks, and seven crash-recovery checkpoints.
Pin reviewed dependencies and document local operating limits.
```

### Remaining limits

The broader Windows/single-writer, snapshot-rebuild, local-runtime, synthetic-data, security-review, and crash-versus-power-loss limitations above still apply. The expanded oracle checks complete outputs for the tested histories; it does not prove correctness for every possible source sequence. No remote CI, comprehensive secret scanner, fresh platform install, public release, or Phase 3 work occurred. Committing and any later publication require separate approval.
