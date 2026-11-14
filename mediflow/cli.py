"""Command-line entry points; no service or cloud connection."""
import argparse
import json
import time
import uuid
from pathlib import Path
from .config import APPROVED, load, runtime, usage
from .evidence import atomic_json
from .generate import demo_batches, write_batch
from .incremental import run


def main():
    parser = argparse.ArgumentParser(prog="mediflow")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo")
    demo.add_argument("--config", default="config/demo.toml")
    single = commands.add_parser("run")
    single.add_argument("--root", required=True)
    single.add_argument("--batch", required=True)
    single.add_argument("--fault", default=None, help=argparse.SUPPRESS)
    history = commands.add_parser("history")
    history.add_argument("--root", required=True)
    history.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.command == "history":
        from .history import list_history
        print(json.dumps(list_history(Path(args.root), args.limit)))
        return 0
    if args.command == "run":
        print(json.dumps(run(Path(args.root), Path(args.batch), args.fault), default=str))
        return 0
    config = load(args.config)
    root = runtime(APPROVED / "runs" / ("demo-" + str(uuid.uuid4())))
    reports = []
    started = time.perf_counter()
    batches = demo_batches(config["seed"], config["patients"], config["appointments"], config["as_of"])
    for i, rows in enumerate(batches):
        batch = write_batch(root, f"batch-{i}", rows, config)
        reports.append(run(root, batch))
    reports.append(run(root, root / "source" / "batch-0"))
    result = {"root": str(root), "elapsed_seconds": time.perf_counter() - started,
              "working_storage_bytes": usage(), "runs": reports}
    atomic_json(root / "demo-results.json", result)
    print(json.dumps(result, default=str))
    return 0
