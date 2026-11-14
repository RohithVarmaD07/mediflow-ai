# MediFlow AI

A local, synthetic healthcare pipeline for patients, appointments, and encounters. Phase 2 implements immutable ingestion, explicit validation and quarantine, versioned incremental updates, DuckDB analytics, typed Parquet snapshots, recovery, and execution evidence. See the verification report for actual results and limitations.

## Current status

| Milestone | Status |
| --- | --- |
| Phase 2 vertical slice and quality improvements | Completed locally; historical 41/67-test evidence retained |
| Phase 3 Milestone 1 hardening | Completed locally; retained result: 86 passed, zero failures/errors/skips |
| R0 documentation alignment | Completed; historical evidence preserved |
| R1 / Phase 3 Milestone 2 | Completed locally; 133 passed, zero failures/errors/skips; original 86 cases retained |

See the [Milestone 1 report](docs/phase-3-milestone-1-verification.md) and [R1 plan](docs/phase-3-milestone-2-plan.md). Its 264.24-second console duration describes the test suite. Earlier synthetic demo timings describe earlier source executions, not current throughput.

## Run locally on the approved Windows machine

Run commands below only within the approved local execution scope.

Dependencies are pinned for CPython 3.13 Windows x86-64. The environment is `.venv`; generated data is restricted to the current user's `AppData/Local/MediFlowAI/phase2` by default. This runtime location is deliberately outside OneDrive. No account, cloud service, API key, or model is needed.

```powershell
.\.venv\Scripts\python.exe -B -m mediflow demo --config config/demo.toml
.\.venv\Scripts\python.exe -B -m pytest tests -q
```

The CLI prints the unique demo directory and run results. Each demo ingests a baseline, late corrections, malformed/duplicate/stale records, and a baseline replay. Inspect `current.json` for the published snapshot and `runs/<run-id>` for detailed evidence. Tests use isolated UUID directories under the approved runtime; they do not remove the evidence of earlier attempts.

Analytical regression checks rebuild expected state independently, compare complete group-key sets and all measures after each batch, and reject duplicate keys. Edge cases include walk-ins, cancelled/no-show appointments, unused patients, late corrections, deleted records, and duplicate delivery. Deliberately corrupted results test that missing groups cannot silently pass the comparison.

To reproduce installation after approval, create a Python 3.13 environment and install the reviewed wheels with `pip --isolated install --no-index --find-links <approved-runtime>/wheelhouse --require-hashes -r requirements-win-py313.lock`. `pip check` must pass. This lock is Windows-specific, not a universal platform lock. No packaging/build backend is required to run the module from this directory.

## Documentation

- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md) and [dictionary](docs/data-dictionary.md)
- [Incremental processing](docs/incremental-processing.md)
- [Recovery runbook](docs/recovery-runbook.md)
- [Milestone 1 verification](docs/phase-3-milestone-1-verification.md)
- [Milestone 2 verification](docs/phase-3-milestone-2-verification.md)
- [Acceptance scenarios](docs/acceptance-scenarios.md)
- [Dependency review](docs/dependency-licenses.md)
- [Execution plan](docs/phase-2-execution-plan.md)
- [Verification report](docs/phase-2-verification-report.md)
- [Security](SECURITY.md)

This is a Windows, single-writer portfolio implementation. All patient information is synthetic. Analytical snapshots are rebuilt from incrementally maintained canonical state. No cloud execution, AI insight generation, clinical validation, compliance certification, or production-readiness claim is made. The original pipeline-event JSON Schema remains a future integration contract; Phase 2 events are local run-state evidence, not a claim of full contract conformance.

R1 adds a fixed sequential controller and durable stage history. Monitoring services, scheduling, AWS integration, publication and deployment remain outside the implemented scope. The project remains an ordinary folder pending the approved copy-only separation strategy.

## Read execution history

```powershell
.\.venv\Scripts\python.exe -B -m mediflow history --root <approved-pipeline-root> --limit 100
```

History reads bounded JSON evidence without opening DuckDB or creating runtime paths. It reports corrupt evidence and incomplete outcomes explicitly. Results are ordered by invocation UUID, then legacy run UUID, not by time; `truncated` indicates omitted results. Old manifests without controller records remain visible with `stage_history_unavailable`. The command does not schedule jobs, repair records, or infer that an unfinished process is alive.

## Configurable isolated runtime

See [runtime configuration](docs/runtime-configuration.md) before running a copy. `MEDIFLOW_RUNTIME_ROOT` selects an absolute local boundary. Existing recorded test counts above describe retained R1 evidence; release-repair verification is recorded separately.

## Retained release-repair verification

November 2, 2026: 147 tests passed with zero failures/errors/skips, retaining all 133 R1 cases and the original 86. All seven original crash checkpoints passed. A copied-source 10,000-record demo verified 24 output hashes and unchanged replay using existing dependencies. These retained results were not rerun during the final website audit. Clean-room installation is unverified; short local Windows runtime paths are required.

## License

Original covered materials use the [MIT License](LICENSE), Copyright (c) 2026 Rohith Varma. Read the [scope and exclusions](LICENSE_SCOPE.md) and [third-party review](THIRD_PARTY.md). These files are prepared locally; publication still requires owner approval.
