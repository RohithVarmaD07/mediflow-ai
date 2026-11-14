# Local runtime configuration

Set `MEDIFLOW_RUNTIME_ROOT` before starting Python to choose an isolated absolute local directory. With the variable unset, the default remains the current user's `AppData/Local/MediFlowAI/phase2` beneath the home directory. No private username is embedded in source. Relative, empty and UNC values are rejected. Selection does not create directories; existing runtime containment and reparse-point checks apply before writes.

```powershell
$env:MEDIFLOW_RUNTIME_ROOT = Join-Path $HOME 'AppData/Local/MediFlowAI/reproduction-unique'
# Use a new directory; never reuse historical evidence for release verification.
.\.venv\Scripts\python.exe -B -m pytest tests -q
.\.venv\Scripts\python.exe -B -m mediflow demo --config config/demo.toml
```

These commands assume the existing reviewed Windows CPython 3.13 environment and pinned dependencies. They do not install dependencies. A copied source checkout may use the existing environment's absolute Python path. This verifies source-directory independence, not a clean-room installation or another operating system.

Storage accounting includes the original default runtime, selected runtime and active project, without double-counting nested roots. Other environments/copies must also be included in the operator's 2 GB aggregate audit. Existing runtime artifacts are neither migrated nor deleted. Keep the selected directory outside synchronization services and network shares; reject reparse-point ancestors. Mapped network drives and arbitrary synchronization services are not detected automatically.

The runtime variable is read once at process import. Change it only between invocations. Invalid configuration fails before pipeline initialization and creates no startup evidence. A valid selected boundary retains existing invocation, transaction, publication and recovery behavior. Code fingerprint changes intentionally block recovery of older committed-but-unpublished work; do not bypass that gate or upgrade an active pending run. Keep the prior implementation for recovery under separately reviewed operational instructions.

Use a short runtime base: deeply nested Windows paths can exceed filesystem limits, especially under packaged-app AppData redirection. A deep-path demo failed during release verification; its evidence is retained. Extended-prefix containment normalization does not enable arbitrary-length filesystem writes. No Windows registry or long-path system setting is changed.
