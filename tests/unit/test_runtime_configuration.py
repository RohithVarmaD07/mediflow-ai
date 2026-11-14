"""Runtime selection and aggregate storage accounting without legacy writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from mediflow import config


def test_default_matches_existing_user_location():
    assert config.runtime_root({}) == Path.home() / "AppData" / "Local" / "MediFlowAI" / "phase2"


def test_custom_absolute_root_selected_without_creation(root):
    target = root / "custom-not-created"
    assert config.runtime_root({"MEDIFLOW_RUNTIME_ROOT": str(target)}) == target
    assert not target.exists()


@pytest.mark.parametrize("value", ["", "relative", "../escape", "C:relative", r"\\server\share\runtime"])
def test_invalid_runtime_root_rejected(value):
    with pytest.raises(ValueError, match="INVALID_RUNTIME_ROOT"):
        config.runtime_root({"MEDIFLOW_RUNTIME_ROOT": value})


@pytest.mark.parametrize("nested", [True, False])
def test_budget_counts_preserved_and_custom_roots_once(root, monkeypatch, nested):
    legacy = root / "legacy"
    selected = legacy / "new" if nested else root / "new"
    project = root / "project"
    for path, payload in [(legacy / "old.bin", b"123"), (selected / "new.bin", b"4567"), (project / "source.bin", b"89")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    monkeypatch.setattr(config, "DEFAULT_RUNTIME", legacy)
    monkeypatch.setattr(config, "APPROVED", selected)
    monkeypatch.setattr(config, "PROJECT", project)
    assert config.usage() == 9
    monkeypatch.setattr(config, "LIMIT", 10)
    config.budget(1)
    with pytest.raises(RuntimeError, match="STORAGE_BUDGET"):
        config.budget(2)


def test_process_imports_share_custom_boundary(root):
    target = root / "process-boundary"
    code = "from mediflow.config import APPROVED; from mediflow import cli,incremental,history; import json; print(json.dumps([str(APPROVED),str(cli.APPROVED),str(incremental.APPROVED),str(history.APPROVED)]))"
    child = subprocess.run([sys.executable, "-B", "-c", code], cwd=config.PROJECT,
        env=dict(os.environ, MEDIFLOW_RUNTIME_ROOT=str(target)), capture_output=True, text=True, timeout=60)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == [str(target)] * 4
    assert not target.exists()


def test_selected_boundary_preserves_escape_rejection(root, monkeypatch):
    selected = root / "selected"
    monkeypatch.setattr(config, "APPROVED", selected)
    assert config.runtime(selected / "child").is_dir()
    with pytest.raises(ValueError, match="PATH_OUTSIDE_ROOT"):
        config.runtime(root / "outside")


@pytest.mark.parametrize("outside", [False, True])
def test_extended_drive_resolution_preserves_containment(root, monkeypatch, outside):
    target = root / "child"
    resolved = root.parent / "outside" if outside else target
    original = Path.resolve
    def resolve(path, *args, **kwargs):
        if path == target:
            return Path("\\\\?\\" + str(original(resolved)))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", resolve)
    if outside:
        with pytest.raises(ValueError, match="PATH_ESCAPE"):
            config.safe_path(root, target)
    else:
        assert config.safe_path(root, target) == target
