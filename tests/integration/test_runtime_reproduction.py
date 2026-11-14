"""Real subprocess demo and replay isolated from the parent runtime."""
import json
import os
import subprocess
import sys
from mediflow.config import PROJECT, APPROVED
import uuid


def test_isolated_demo_reproduction(root):
    selected = APPROVED / ("isolated-" + uuid.uuid4().hex[:8])
    settings = root / "small-demo.toml"
    settings.write_text('seed = 42\npatients = 5\nappointments = 10\nas_of = "2026-01-01T00:00:00Z"\n')
    env = dict(os.environ, MEDIFLOW_RUNTIME_ROOT=str(selected), PYTHONDONTWRITEBYTECODE="1")
    child = subprocess.run([sys.executable, "-B", "-m", "mediflow", "demo", "--config", str(settings)],
        cwd=PROJECT, env=env, capture_output=True, text=True, timeout=300)
    assert child.returncode == 0, child.stderr
    result = json.loads(child.stdout)
    from pathlib import Path
    demo = Path(result["root"])
    assert demo.is_relative_to(selected)
    assert len(result["runs"]) == 4
    assert all(row["reconciliation"]["difference"] == 0 for row in result["runs"])
    assert result["runs"][-1]["changes"] == {"inserts": 0, "updates": 0, "tombstones": 0}
    assert result["runs"][-1]["outputs"] == result["runs"][-2]["outputs"]
    assert (demo / "current.json").is_file()
    assert len(list((selected / "invocations").glob("*.json"))) == 4
