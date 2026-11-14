# Recovery runbook

Always operate under the approved AppData runtime. Stop concurrent writers; do not remove a live OS lock or copy an open database between machines.

Run the original command again after interruption. Before schema initialization or new ingestion, the pipeline checks committed-but-unpublished ledger entries for exact compatibility, then republishes matching snapshots. A prior run without a committed ledger row is marked interrupted_before_commit. The retried input is then classified normally, so already-committed records become duplicates rather than new rows.

Failure checkpoints tested: raw_copy, before_commit, after_commit, parquet_write, before_pointer, after_pointer, evidence. The hidden CLI fault option only works when MEDIFLOW_TEST_FAULTS=1 and exits the subprocess with code 77. It is used only by controlled tests. Tests verify final counts, replay behavior, recovery references, and terminal run states.

Transient PermissionError operations retry at most three times with 0.05/0.1 second backoff. Other failures propagate with evidence; schema errors are not retried blindly. Retry success and exhaustion are tested. Partial raw/staging files can be overwritten on recovery; old published snapshots remain immutable.

If checksum validation fails, preserve evidence and investigate instead of overwriting trusted raw files. If the storage guard fails, request review before cleanup or increasing the limit. Test evidence is retained. No automatic broad deletion exists.

The tests establish subprocess-crash recovery. They do not establish hardware power-loss durability, recovery from disk corruption, antivirus interference under all conditions, or disaster recovery. Operating-system rename semantics and the approved local filesystem are assumptions.

## Milestone 1 hardening

Each invocation receives a UUID before target-path validation. Durable JSON under the approved runtime `invocations/<uuid>.json` records startup stage, timestamps, outcome, and exception type; successful invocations link to the run manifest. Startup stages are storage, lock, database, and recovery. Failure records omit exception messages to avoid copying sensitive values; recognized safety errors also receive an allowlisted error code. If final evidence writing fails during another exception, the original error propagates with an evidence-failure note. These are invocation outcomes, not a scheduler or execution-history service.

Pending recovery requires an exact fingerprint of implementation Python files, SQL (including schema), TOML configuration, JSON contracts, Python version, DuckDB version, and PyArrow version. All pending entries are checked before any recovery publication. The connection closes if compatibility or schema initialization fails. A mismatch raises `INCOMPATIBLE_RECOVERY`; it does not rewrite the ledger, apply schema SQL, or publish new snapshots. Completed historical runs do not require this fingerprint.

Older pending runs without a fingerprint are blocked rather than guessed compatible. Preserve the database, raw inputs, snapshots, and evidence. Review the original implementation and configuration before approving a recovery procedure. Do not manually overwrite a production fingerprint to bypass the guard. This conservative policy also blocks harmless source edits; automatic migrations are outside this milestone.

Relationship and row-accounting checks raise explicit errors before the transaction and remain effective with Python optimization enabled. Canonical writes and the committed ledger remain in the same transaction; snapshot publication retains its existing atomic pointer protocol.

If the approved evidence location is inaccessible or storage is exhausted, durable invocation evidence cannot be guaranteed. An abrupt process termination leaves the last recorded startup/pipeline state; this milestone does not infer a terminal invocation outcome or provide heartbeats. The storage guard remains a preflight reserve check, not an operating-system quota. Compatibility assumes project files are not edited while an invocation is running.

## Evidence navigation and implementation changes

The [Milestone 1 report](phase-3-milestone-1-verification.md) identifies the latest retained 86-test suite. Under the approved runtime, invocation records are in `invocations/<uuid>.json`; individual pipeline roots hold `runs/<run-id>/manifest.json`, metrics, reconciliation, quality, outputs and events. Follow the invocation/run identifiers rather than guessing the latest folder. A startup failure can occur before a run ID exists. An unfinished invocation means completion was not recorded; it does not establish a live process.

Before any approved implementation/configuration change, resolve pending runs using the original matching implementation or propose a reviewed preservation/recovery procedure. Do not edit fingerprints, remove an OS lock, or restore a snapshot pointer independently of its database and evidence. Current code deliberately blocks incompatible pending recovery. No automated upgrade or downgrade procedure exists.

R0 ran no recovery commands. R1 execution was separately approved; preserve all historical runtime artifacts and reports. See the [R1 plan](phase-3-milestone-2-plan.md) and [execution report](phase-3-milestone-2-verification.md).

## Controller history during recovery

The next invocation recovers compatible pending publication using a new publish/finalize attempt and the original run ID before executing its own ingestion. Original stage records are not rewritten. A normal replay still gets a new run ID and is classified by the existing deduplication rules. No controller-level whole-stage retry is performed automatically.

Use the read-only `history` command to inspect stage records. `completion_not_recorded` is intentionally distinct from success or proof that a process is alive. A process can exit after publication or finalization but before its invocation outcome is written; the next command can replay safely while the old history remains incomplete. If history is corrupt, preserve it; no automatic repair or deletion is provided. An unreadable/unattributable history header cannot reliably establish prior attempt numbering and is a limitation, not evidence of a new first execution.

Do not change implementation, SQL, contracts or configuration while a run is pending; these files participate in the compatibility fingerprint. Rollback requires matched source/runtime state, never only a snapshot pointer. Stage evidence cannot be guaranteed when the evidence filesystem fails. The OS lock, database ledger and snapshot checks retain their existing authority.
