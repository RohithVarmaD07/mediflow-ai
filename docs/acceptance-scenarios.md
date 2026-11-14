> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# Implemented acceptance and evidence mapping

| Capability | Executable evidence |
| --- | --- |
| Seeded source reproducibility | tests/unit/test_generation.py |
| Contract/types/timestamps | tests/unit/test_validation.py |
| Duplicate/conflict classification | tests/unit/test_deduplication.py |
| Source-version ordering | tests/unit/test_version_ordering.py |
| Path boundary enforcement | tests/unit/test_path_security.py |
| Durable evidence format | tests/unit/test_evidence.py |
| Actual DuckDB/Parquet pipeline | tests/integration/test_pipeline.py |
| Full-history oracle and analytical reconciliation | tests/integration/test_incremental_equivalence.py |
| Complete group-key sets, duplicate-key rejection, and every intermediate snapshot | tests/integration/test_incremental_equivalence.py |
| Missing/extra/duplicate/empty output mutations and incorrect measures | tests/integration/test_incremental_equivalence.py |
| Walk-ins, zero-activity patients, cancelled-only groups, tombstones, and late corrections | tests/integration/test_incremental_equivalence.py |
| Late date corrections | tests/integration/test_late_arrivals.py |
| Quarantine and corrected resubmission | tests/integration/test_quarantine_reprocessing.py |
| Seven subprocess failure checkpoints, writer lock, retry bounds | tests/integration/test_recovery.py |
| Snapshot hashes and source tampering | tests/integration/test_parquet_publication.py |
| Startup failures, real lock contention, rejected paths and invocation linkage | tests/integration/test_hardening.py |
| Incompatible implementation/SQL/schema/configuration/dependency/legacy recovery | tests/integration/test_hardening.py |
| Explicit invariants including optimized-Python subprocesses | tests/integration/test_hardening.py |
| Original startup exception preserved if outcome writing fails | tests/integration/test_hardening.py |

Success requires no failing/skipped critical cases, zero canonical duplicate keys, exact input accounting, equality against the independent oracle, safe published snapshots, traceable failures, and measured resource use below the allowance. Actual results and unresolved limitations are in the verification report. No throughput target is claimed before measurement.

Milestone 1 retained result: **86 passed, zero failures/errors/skips** in the [Milestone 1 report](phase-3-milestone-1-verification.md). Its JUnit artifact is `<approved-runtime>/tests/results-milestone1-final.xml`. The [Phase 2 report](phase-2-verification-report.md) retains earlier 41/67-test results and failures. R0 inspects documentation/evidence only; it does not execute these tests. R1 execution is recorded separately in the [Milestone 2 report](phase-3-milestone-2-verification.md); historical counts remain unchanged.

## R1 coverage

| Capability | Executable evidence |
| --- | --- |
| Fixed stage order, dependency/duplicate rejection, failure blocking, bounded operation retries and original-error preservation | [Controller unit tests](../tests/unit/test_orchestration.py) |
| Bounded record validation, corruption, illegal transitions, incomplete outcome, overwrite refusal, legacy/limited reads | [History unit tests](../tests/unit/test_history.py) |
| Pipeline stage order, read-only history CLI, no database access, stage failures and legacy manifests | [Controller integration tests](../tests/integration/test_controller.py) |
| Recovered run/attempt identities and crashes at added controller boundaries | [Controller recovery tests](../tests/integration/test_controller_recovery.py) |

The original 86 cases and seven crash points must remain represented and passing in the final suite. Added checks do not establish hardware power-loss durability or secure multi-user operation. Actual counts, failures, timings and resource use belong in the Milestone 2 report.

Final R1 result: **133 passed, zero failures/errors/skips**, including all original 86 cases and seven crash checkpoints. See the [Milestone 2 report](phase-3-milestone-2-verification.md) for the retained demo defect, fix and final evidence.
