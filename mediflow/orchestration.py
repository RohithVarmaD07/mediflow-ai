"""A fixed sequential controller: no whole-stage retries or scheduling."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
import uuid
from .config import APPROVED, safe_path
from .evidence import clock, now
from .history import STAGES, next_attempt, write_transition

ACTIVE = ContextVar("mediflow_controller", default=None)


class Stage(StrEnum):
    STARTUP = "startup"
    LOCK = "lock"
    CONNECT = "connect"
    RECOVER = "recover"
    INGEST = "ingest"
    PREPARE = "prepare"
    COMMIT = "commit"
    PUBLISH = "publish"
    FINALIZE = "finalize"


@dataclass
class ExecutionContext:
    invocation_id: str
    root_ref: str | None
    sequence: int = 0


@dataclass
class StageAttempt:
    stage_id: str
    attempt_id: str
    attempt_number: int


def classify_failure(exc):
    allowed = {"WRITER_BUSY", "STORAGE_BUDGET", "INCOMPATIBLE_RECOVERY", "PATH_OUTSIDE_ROOT",
               "PATH_ESCAPE", "REPARSE_POINT", "DATABASE_RECONCILIATION", "ROW_ACCOUNTING_INVARIANT",
               "RELATIONSHIP_INVARIANT", "SOURCE_HASH", "RAW_TAMPERED", "SNAPSHOT_HASH"}
    return str(exc) if str(exc) in allowed else "STAGE_FAILED"


class SequentialController:
    def __init__(self, context, run_id=None, recovery=False):
        self.context = context
        self.run_id = run_id
        self.recovery = recovery
        self.stages = ("publish", "finalize") if recovery else STAGES
        self.states = {stage: "pending" for stage in self.stages}

    def record(self, attempt, status, elapsed=None, exc=None):
        record = {"schema_version": "1.0.0", "invocation_id": self.context.invocation_id,
                  "run_id": self.run_id, "stage_id": attempt.stage_id, "attempt_id": attempt.attempt_id,
                  "attempt_number": attempt.attempt_number, "sequence": self.context.sequence + 1,
                  "occurred_at": now(), "elapsed_seconds": elapsed, "status": status,
                  "error_code": classify_failure(exc) if exc else None,
                  "error_type": type(exc).__name__ if exc else None,
                  "recovery_of_run_id": self.run_id if self.recovery else None,
                  "evidence_refs": [], "root_ref": self.context.root_ref, "record_type": "stage_transition"}
        write_transition(record)
        self.context.sequence += 1

    @contextmanager
    def stage(self, stage):
        stage = str(stage)
        if stage not in self.states or self.states[stage] != "pending":
            raise RuntimeError("STAGE_TRANSITION")
        index = self.stages.index(stage)
        if any(self.states[s] != "succeeded" for s in self.stages[:index]):
            raise RuntimeError("STAGE_DEPENDENCY")
        number = next_attempt(self.run_id, stage, self.context.root_ref) if self.recovery else 1
        attempt = StageAttempt(stage, str(uuid.uuid4()), number)
        self.record(attempt, "running")
        self.states[stage] = "running"
        start = clock()
        try:
            yield
        except Exception as exc:
            self.states[stage] = "failed"
            try:
                self.record(attempt, "failed", clock() - start, exc)
                self.block_dependents(stage)
            except Exception as evidence_error:
                exc.add_note("Controller evidence unavailable: " + type(evidence_error).__name__)
            raise
        else:
            self.record(attempt, "succeeded", clock() - start)
            self.states[stage] = "succeeded"

    def execute_stage(self, stage, operation):
        with self.stage(stage):
            return operation()

    def block_dependents(self, stage):
        for following in self.stages[self.stages.index(stage)+1:]:
            if self.states[following] == "pending":
                self.record(StageAttempt(following, str(uuid.uuid4()), 1), "blocked")
                self.states[following] = "blocked"


def root_reference(root):
    try:
        return safe_path(APPROVED, root).relative_to(APPROVED).as_posix()
    except (ValueError, OSError):
        return None
