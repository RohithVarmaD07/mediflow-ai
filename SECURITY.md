# Security and dependency boundaries

This implementation accepts bounded local synthetic JSON Lines from the approved runtime source directory. It does not accept public uploads, real patient data, SQL expressions, models, credentials, or network endpoints. Source paths are checked for root containment and existing reparse points. Input files are limited to 20 MB and records to 16 KiB. Unknown fields and unsupported contracts are rejected.

DuckDB uses two threads, a 512 MB database memory setting, disabled external access, and disabled extension autoinstall/autoload. Queries are authored SQL with bound record values. PyArrow reads only generated plaintext Parquet; no encrypted-Parquet decryption properties, custom KMS clients, Arrow IPC input, or native C++ prebuffer APIs are used. The program is not an operating-system sandbox against a hostile local administrator or concurrent file replacement attacker.

The approved AppData runtime has ordinary, non-reparse ancestors, inherits user/system/administrator access, and passed a durable-write/atomic-replace probe. No ACLs or OneDrive settings were changed. The Python environment is in the source folder; active databases and runtime state are outside OneDrive. Total logical working bytes across this project and the runtime are checked before runs, with a 100 MB pipeline reserve within the 2 GB allowance. Filesystem allocation and peak RAM are not measured by this check.

## Advisory applicability

- DuckDB 1.4.2 fixes the encryption issue that blocked 1.4.1. No advisory was listed for the selected release by PyPI at review.
- Pygments 2.20.0 fixes CVE-2026-4539. No advisory was listed for this selected release at review.
- Arrow CVE-2026-25087 concerns an IPC C++ API not exposed by Python bindings, according to the advisory.
- Arrow CVE-2026-92287 requires configured Parquet decryption with a KMS client. This implementation has neither; plaintext generated output is the only Parquet input.
- pytest CVE-2025-71176 describes Unix temporary-directory handling. Execution here is Windows; tests use a private approved runtime. Do not activate a Linux CI test job with this pin without a new platform/security review.

These are recorded applicability decisions, not claims that packages contain no vulnerabilities. A change in input trust, platform, encryption, extension use, or dependencies requires reassessment. See dependency documentation for sources and retained hashes/licenses. No independent penetration test or broad vulnerability scanner has run.

Keep vulnerability reports private for owner review. No public reporting channel or supported production release is advertised.
