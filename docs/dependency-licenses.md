> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# Dependency verification and licenses

Reviewed for Windows x86-64 / CPython 3.13.2. All eight selected wheels were downloaded from PyPI, their bytes matched the published SHA-256, and bundled license/notice files were extracted into the local dependency review. No extras or source builds were installed. These tools have no service or software purchase fee.

| Package | Version | License | Wheel bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| duckdb | 1.4.2 | MIT (experimental Spark adapter includes Apache-2.0) | 12330535 | `2f7c61617d2b1da3da5d7e215be616ad45aa3221c4b9e2c4d1c28ed09bc3c1c4` |
| pyarrow | 21.0.0 | Apache-2.0; bundled third-party notices retained | 26087551 | `186aa00bca62139f75b7de8420f745f2af12941595bbbfa7ed3870ff63e25636` |
| pytest | 8.4.2 | MIT | 365750 | `872f880de3fc3a5bdc88a11b39c9710c3497a547cfa9320bc3c5e62fbf272e79` |
| colorama | 0.4.6 | BSD-3-Clause | 25335 | `4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6` |
| iniconfig | 2.1.0 | MIT | 6050 | `9deba5723312380e77435581c6bf4935c94cbfab9b1ed33ef8d238ea168eb760` |
| packaging | 25.0 | Apache-2.0 OR BSD-2-Clause | 66469 | `29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484` |
| pluggy | 1.6.0 | MIT | 20538 | `e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746` |
| Pygments | 2.20.0 | BSD-2-Clause | 1231151 | `81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176` |

Total wheel download: 40,133,379 bytes. Exact dependency constraints are satisfied by the pinned Windows/Python environment; `pip check` passed. DuckDB and PyArrow have native cp313-win_amd64 wheels; the remaining wheels are platform-independent. All eight Requires-Python constraints include 3.13. Pytest's conditional exceptiongroup/tomli requirements do not apply to Python 3.13. Optional extras are not enabled.

## Security review and applicability

PyPI release-specific vulnerability metadata was retrieved for all eight packages. It listed no findings for DuckDB 1.4.2, Pygments 2.20.0, Colorama, iniconfig, packaging, or pluggy. Absence from a feed is not proof of absence of vulnerabilities. Arrow and pytest entries were investigated against advisory scope:

- [DuckDB encryption advisory](https://github.com/duckdb/duckdb/security/advisories/GHSA-vmp8-hg63-v2hp): fixed in the approved 1.4.2 version.
- [Pygments ReDoS advisory](https://github.com/advisories/GHSA-5239-wwwm-4pmq): fixed in approved 2.20.0.
- [Arrow IPC advisory](https://github.com/advisories/GHSA-rgxp-2hwp-jwgg): affected C++ prebuffer API is not exposed by Python bindings; IPC files are not pipeline inputs.
- [Arrow KMS advisory release notes](https://arrow.apache.org/blog/2026/10/08/26.0.0-release/): vulnerable behavior requires configured encrypted-Parquet decryption with a custom KMS client. Neither is implemented; only local generated plaintext Parquet is read. No version change was made.
- [pytest Unix tmpdir advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g): platform-specific Unix path issue; current execution is Windows with owner-scoped runtime test directories. Linux test activation requires a separate review.

No unresolved advisory relevant to the restricted implemented paths was identified in the reviewed sources. This statement is scoped to this review and feature set, not blanket package security certification. Native wheel bundled components were not separately scanned by a vulnerability scanner. Reassess before accepting untrusted Parquet, enabling encryption, changing platform, or activating remote CI.

The local file `<approved-runtime>/install/dependency-review.json` retains metadata, exact wheel hashes, all extracted license texts, and feed findings. License notices remain in installed distribution metadata. Original project materials now have a locally prepared [MIT license](../LICENSE), with [scope exclusions](../LICENSE_SCOPE.md) and a [third-party summary](../THIRD_PARTY.md). Final publication remains subject to owner review.
