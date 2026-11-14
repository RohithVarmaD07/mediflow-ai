# Third-party licensing review

This is an attribution and dependency summary, not a replacement for upstream license texts. Dependencies retain their own copyright and licenses and are not covered by Rohith Varma's MIT license. No dependency distributions, vendored code or binary libraries are included in this source candidate.

| Dependency | Pinned version | License recorded in retained distribution review |
| --- | --- | --- |
| DuckDB | 1.4.2 | MIT; experimental Spark adapter includes Apache-2.0 |
| PyArrow | 21.0.0 | Apache-2.0, with bundled third-party notices |
| pytest | 8.4.2 | MIT |
| colorama | 0.4.6 | BSD-3-Clause |
| iniconfig | 2.1.0 | MIT |
| packaging | 25.0 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.6.0 | MIT |
| Pygments | 2.20.0 | BSD-2-Clause |

See [dependency review](docs/dependency-licenses.md) and the pinned requirements file. Installed distribution metadata and license/notice hashes were reviewed locally; the historical review is not a current security certification.

When redistributing dependency source or binaries, retain the applicable copyright, permission, disclaimer and attribution notices. MIT requires its notices with copies or substantial portions; BSD licenses require their notices/disclaimers, with BSD-3-Clause also prohibiting endorsement using contributor names without permission. Apache-2.0 requires a license copy, retention of applicable notices, modification notices for changed files and preservation of relevant NOTICE attribution where supplied. Review the exact distributions, including Arrow's bundled components, before building a wheelhouse, container or standalone executable for others. This summary alone is insufficient for such redistribution. The present candidate references dependencies but does not redistribute them.

References: [MIT](https://opensource.org/license/mit), [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0), [BSD-3-Clause](https://opensource.org/license/bsd-3-clause), [BSD-2-Clause](https://opensource.org/license/bsd-2-clause). External references and product names do not imply ownership or endorsement.
