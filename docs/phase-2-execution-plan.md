> Sanitized documentation copy: private paths replaced with placeholders; original evidence is unchanged. Placeholder commands are not directly executable.

# Approved Phase 2 execution record

Scope: MediFlow only, using existing Python 3.13.2 and eight approved dependencies. DuckDB was changed to 1.4.2 and Pygments to 2.20.0 by explicit owner approvals. Runtime was separately approved at <approved-runtime>. Source changes remain in the listed MediFlow files. No Git commits, remote repositories, deployment, cloud resource, model, or paid service is involved.

Sequence: review PyPI metadata and advisory applicability; validate ordinary AppData ancestors and permissions; probe fsync/replace; download exact wheels and compare SHA-256; retain bundled licenses; create the local environment; offline hash-locked install; pip check; implement source/SQL/CLI; run meaningful tests with retained JUnit evidence; fix observed failures; run three standard demos; record measurements and limitations.

The package installer uses no source builds or unapproved extras. Sandbox network access initially failed DNS; a native approval allowed the read-only metadata checks and later the approved wheel download/runtime writes. Native approval controls were not disabled.

Storage allowance is 2,000,000,000 logical bytes for the project and external runtime together, with conservative reserves. No unrelated directory is a cleanup target. Phase 3 requires separate approval.
