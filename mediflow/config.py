"""Runtime boundary and resource policy."""
from pathlib import Path
import os
import stat
import tomllib

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME = Path.home() / "AppData" / "Local" / "MediFlowAI" / "phase2"


def runtime_root(environ=None):
    """Select a local absolute boundary without creating or migrating any files."""
    environ = os.environ if environ is None else environ
    value = environ.get("MEDIFLOW_RUNTIME_ROOT")
    root = DEFAULT_RUNTIME if value is None else Path(value)
    if not root.is_absolute() or str(root).startswith("\\\\"):
        raise ValueError("INVALID_RUNTIME_ROOT")
    return root


APPROVED = runtime_root()
LIMIT = 2_000_000_000


def resolved_comparison(path):
    """Windows may prefix only long resolved children with extended drive syntax."""
    value = str(path.resolve())
    if os.name == "nt" and value.startswith("\\\\?\\") and len(value) > 6 and value[5:7] == ":\\":
        value = value[4:]
    return Path(value)


def safe_path(root, path):
    root, path = Path(root).absolute(), Path(path).absolute()
    if not path.is_relative_to(root):
        raise ValueError("PATH_OUTSIDE_ROOT")
    for part in (path, *path.parents):
        if part.exists():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
                raise ValueError("REPARSE_POINT")
    if not resolved_comparison(path).is_relative_to(resolved_comparison(root)):
        raise ValueError("PATH_ESCAPE")
    return path


def runtime(path):
    path = safe_path(APPROVED, Path(path))
    path.mkdir(parents=True, exist_ok=True)
    return path


def usage():
    total = 0
    # Keep preserved default evidence in the budget when selecting another root.
    roots = set((DEFAULT_RUNTIME, APPROVED, PROJECT))
    for base in roots:
        if any(base != other and base.is_relative_to(other) for other in roots):
            continue
        if base.exists():
            total += sum(p.stat().st_size for p in base.rglob("*") if p.is_file())
    return total


def budget(reserve=50_000_000):
    if usage() + reserve > LIMIT:
        raise RuntimeError("STORAGE_BUDGET")


def load(path):
    with Path(path).open("rb") as f:
        return tomllib.load(f)
