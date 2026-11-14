"""Bounded retries and an OS-owned single-writer lock."""
from contextlib import contextmanager
import os
import time
import msvcrt


def retry(operation, delays=(0.05, 0.1)):
    for attempt in range(len(delays) + 1):
        try:
            return operation()
        except PermissionError:
            if attempt == len(delays):
                raise
            time.sleep(delays[attempt])


@contextmanager
def writer_lock(root):
    path = root / "state" / "writer.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as f:
        if path.stat().st_size == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError("WRITER_BUSY") from exc
        try:
            yield
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def fault(selected, point):
    if selected == point:
        if os.environ.get("MEDIFLOW_TEST_FAULTS") != "1":
            raise RuntimeError("FAULT_INJECTION_NOT_AUTHORIZED")
        os._exit(77)
