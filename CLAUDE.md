# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

PkgAutoTest is an automated test harness for SCC (Boston University Shared Computing Cluster) software modules. It discovers per-module `test.qsub` scripts under `/share/pkg.8/...`, then runs each one as an SGE job via a Nextflow pipeline and aggregates pass/fail results into a CSV report.

The deployed entry point is the SCC `pkgautotest` module (loaded via `module use /share/module.8/rcstools; module load pkgautotest`), which exposes `find_qsub.py`, `nf_pkgtest`, and the env var `$PKGTEST_SCRIPT` pointing at `nextflow/pkgtest.nf`.

## Pipeline (four-stage flow)

1. **`scripts/find_qsub.py`** — walks the published-module tree, finds `test.qsub` (and variants matching `test.*.qsub`, e.g. `test.gpu.qsub`, `test.mpi.qsub`) under each module's `tests/` dir, parses qsub options out of those files (stripping `-j`, `-P`, `-N`), and emits a CSV row per test file. Each row carries `module_name`, `version`, `module_pkg_dir`, `test_path`, `qsub_options`, etc. This CSV is the contract between stages.
2. **`nextflow/pkgtest.nf`** — DSL2 workflow. `splitCsv` → one `runTests` process per row. The process copies the module's `tests/` dir into the Nextflow work dir, appends an Xvfb-kill block to the qsub script (see issue #18), runs it under `bash`, then derives PASSED/FAILED from `results.txt` + exit code. `errorStrategy` defaults to `ignore` so one bad test doesn't kill the run. Each task writes its result as a single-row `test_metrics.csv` and `publishDir` copies it into `--test_results_dir` (default `test_results_<input>`) as soon as that task finishes. Key params: `--csv_input`, `--project` (default `rcstest`), `--executor` (`sge`|`local`), `--keep_passed` (default `true`), `--errorStrategy`, `--test_results_dir`.
3. **`nextflow/collect_report.py`** — concatenates the per-test result files into `report_<input>.csv`, run from `workflow.onComplete` and also standalone. It reconciles the collected rows against the input CSV and writes a `NO_RESULT` row for any test that produced none, so the report always has one row per input row; it exits non-zero on any discrepancy. This replaced `collectFile`, which was a terminal barrier that hung the pipeline whenever a task died without emitting its output.
4. **Report CSV** — consumed by `rshiny/` (Shiny dashboard: `ui.R` + `server.R`) for browsing results.

A test PASSES iff exit code is 0 AND `results.txt` contains only the word "Passed" (no other non-Passed lines). "Error" counts and log-file "error" counts are reported but don't gate pass/fail.

**A failed Nextflow task means Nextflow could not create the environment to run the test** (e.g. the qsub submission was rejected, or the job was `qdel`'d). Problems with a module's own files or tests — an unreadable `tests` dir, a `test.qsub` that errors — are reported as `FAILED` rows while the task succeeds, because `runTests` writes its row from an `EXIT` trap that always exits 0. A `qdel`'d or `h_rt`-killed job still ends up as `NO_RESULT`: the trap does run and the row lands in the work dir, but `.command.run` traps the signal itself and records a non-zero `.exitcode`, so Nextflow skips `publishDir` regardless of what our script exits with.

## Common commands

```bash
# Standard pipeline run (on SCC)
module load nextflow/25.04.7
module use /share/module.8/rcstools && module load pkgautotest
find_qsub.py module_list.csv                       # discover tests
nf_pkgtest module_list.csv                          # wrapper that runs `nextflow $PKGTEST_SCRIPT --csv_input ...` as an SGE job
# or run the pipeline directly with custom params:
nextflow $PKGTEST_SCRIPT --csv_input module_list.csv --project scv --executor local --keep_passed false

# Single-module quick test (after a fresh module install)
scripts/test_module.sh <mod_name> <mod_ver>         # generates CSV + runs nf_pkgtest

# Resume a partially-completed run (uses Nextflow cache)
nextflow $PKGTEST_SCRIPT --csv_input module_list.csv -resume

# Filter to specific modules
find_qsub.py -m gdal gdal.csv                       # all versions of gdal
find_qsub.py -m gdal/3.8.4 gdal3.8.4.csv            # specific version
find_qsub.py --no_exclude ...                       # include /share/module.8/{test,rcstools}

# Monthly cron entry point
scripts/pkgauto_cron.sh                             # creates timestamped dir, qsubs pkgauto_email.qsub
```

There is no separate test/lint/build step — this repo *is* the test runner. Validate changes by running the pipeline against a small CSV (`nextflow/example.csv` is a reference).

## Things to know when editing

- **`pkgtest.nf` script block runs inside Bash inside Nextflow inside SGE.** Nextflow expands `$var` itself; escape with `\$` to pass through to bash (e.g. `\$WORKDIR`, `\$EXIT_CODE`). Heredocs and `cat > ... << EOF` blocks must be flush-left — Nextflow's triple-quoted block is indentation-sensitive.
- **`clusterOptions` injects per-row `qsub_options`** from the CSV verbatim. A malformed `qsub_options` field in the CSV produces SGE submit failures ("Unknown option") — fix `find_qsub.py`'s extraction, not the pipeline.
- **The report's columns are defined once**, by the `report_columns` map near the top of `pkgtest.nf` (column name → the shell variable holding its value). Both the header line and the value line of each result file are generated from it, and the header is passed to `collect_report.py` as `--header`. To add a column: add a map entry, set that shell variable in the script, and add the name to `NO_RESULT_FIELDS` in `collect_report.py` if it should be filled from the input CSV. `test_path` is the key the collector reconciles on and must stay in the header.
- **`runTests` writes its row from a bash `EXIT` trap** installed before anything that can fail, so a row exists however the script exits, and the trap always exits 0 so the row gets published. Read `RC=\$?` first in the trap. Don't add a failure path that exits non-zero before the trap is installed.
- **`NF_TEST_DIR`** shell variable tracks the copied test dir for conditional cleanup based on `--keep_passed`. Don't rename without updating the cleanup branch at the bottom of `runTests`.
- **`.gitignore` excludes `test*/` and `*.csv`** (and lists itself, so it is untracked) — generated input/report CSVs, `test_results_*/` dirs and per-run test scratch dirs are not committed. Don't add `git add -A` from this tree.
- **Cron production runs** live in `/projectnb/rcstest/cronjobs/<timestamp>/`; `scripts/pkgauto_email.qsub` is the qsub'd job (loads `pkgautotest`, runs pipeline against `modules_crontab.csv`, re-runs `collect_report.py` in case the pipeline was killed, then builds `fail_report_*.csv` by grepping `FAILED|NO_RESULT`). `email_notif.pl` posts failures to ServiceNow (currently commented out) and splits report rows positionally, so new report columns must be appended at the end.
- **`Notes.md`** contains design history and prior debugging notes; consult before changing report semantics or PASS/FAIL logic.
