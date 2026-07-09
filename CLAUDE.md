# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

PkgAutoTest automates testing of software module packages installed on BU's Shared Computing Cluster (SCC). It discovers `test.qsub` files shipped alongside published Lmod modules, submits each as an SGE batch job via a Nextflow pipeline, and reports pass/fail results. It is **SCC-specific**: it assumes Lmod (`module` command), the SGE scheduler (`qsub`/`qstat`/`qdel`), and the `/share/module.8` + `/share/pkg.8` directory layout. Most of it cannot be exercised off the cluster.

## Pipeline (three stages)

The system is a linear data pipeline where each stage's output feeds the next. Understanding the flow across [scripts/find_qsub.py](scripts/find_qsub.py) → [nextflow/pkgtest.nf](nextflow/pkgtest.nf) → report is the key to the codebase.

1. **Discovery** — [scripts/find_qsub.py](scripts/find_qsub.py) walks a module-publication directory (default `/share/module.8`), resolves each `modname/version` symlink to its `/share/pkg.*` install dir via `module show`, finds `test/test.qsub` (and variants `test.*.qsub`, e.g. `test.gpu.qsub`), extracts qsub options and module metadata, and writes an **input CSV** (one row per test.qsub). Runs module queries in parallel via `multiprocessing.Pool` sized by `$NSLOTS`.
2. **Execution** — [nextflow/pkgtest.nf](nextflow/pkgtest.nf) reads that CSV and `branch`es each row on the `qsub_valid` column. Rows with `qsub_valid == True` go to the `runTests` process (one SGE job each): it copies the module's `test` dir into the Nextflow work dir, runs the qsub script with `bash`, then determines PASS/FAIL. Rows that are **not** `True` go to the `reportInvalid` process — pinned to `executor 'local'` so **no** job is submitted to the scheduler (their qsub options were rejected by `qsub -w p` and would be rejected again at submission) — which records the test as `FAILED` (`exit_code=1`, `job_number=NA`) and writes an error to `results.txt`. Both processes emit a per-job `test_metrics.csv` with the same 13-column layout; Nextflow's `collectFile` concatenates them into a single **`report_<input>.csv`**.
3. **Reporting** — the report CSV is consumed by [scripts/email_notif.pl](scripts/email_notif.pl) (emails failed-test details to each module's installer, falling back to `bgregor`) and optionally by the [rshiny/](rshiny/) Shiny app for interactive filtering.

### Pass/fail logic (the core rule — keep the two definitions in sync)

A test PASSES iff: exit code of `test.qsub` is `0` **AND** `results.txt` (stdout of the test) contains at least one `Passed` and **no** lines lacking `Passed`. This is implemented as a shell condition in the `runTests` process ([nextflow/pkgtest.nf](nextflow/pkgtest.nf)). `find_qsub.py`'s `qsub_valid` column is a separate, earlier check (`qsub -w p`) that validates qsub option syntax at discovery time. `pkgtest.nf` acts on it: a `qsub_valid != True` row is an automatic `FAILED` (via `reportInvalid`, not run), so it never reaches the pass/fail rule above. Note the gotcha this design exists for: the CSV's `qsub_options` are injected into each job's `clusterOptions`, so invalid options would make SGE reject the job *at submission* — before any in-`runTests` guard could run. That is why invalid rows are diverted to a separate local process instead of being guarded inside `runTests`.

## Commands

```bash
# 1. Discover tests → input CSV (module load python3 first)
find_qsub.py out.csv                    # all modules under /share/module.8
find_qsub.py -m gdal out.csv            # only modules named "gdal"
find_qsub.py -m gdal/3.8.4 out.csv      # a specific version
find_qsub.py -p /share/pkg.8 out.csv    # limit to one pkg install dir
find_qsub.py -h                         # full options

# 2. Run the pipeline (module load nextflow first)
nextflow nextflow/pkgtest.nf --csv_input out.csv                 # -> report_out.csv
nextflow nextflow/pkgtest.nf --csv_input out.csv --project scv   # change -P project (default rcstest)
nextflow nextflow/pkgtest.nf --csv_input out.csv --executor local  # run on host, not SGE
nextflow nextflow/pkgtest.nf --csv_input out.csv --keep_passed false  # delete work dir of passed tests
nextflow nextflow/pkgtest.nf --csv_input out.csv -resume         # resume from Nextflow cache
nextflow nextflow/pkgtest.nf --csv_input out.csv --errorStrategy terminate  # stop on first failure (default: ignore)

# Convenience: discover + run for one module after install
scripts/test_module.sh gdal 3.8.4
```

When installed as the SCC `pkgautotest` Lmod module, `find_qsub.py` and `nf_pkgtest` are on `$PATH`, `$PKGTEST_SCRIPT` points at `pkgtest.nf`, and `$SCC_PKGAUTOTEST_DIR` at the install root. [nextflow/nf_pkgtest](nextflow/nf_pkgtest) is the thin wrapper: `nf_pkgtest <input.csv>`.

There is no build step, no linter config, and no test suite for this repo's own code — "testing" here means running the pipeline against real modules on the cluster.

## Exclusions and skips

- **Exclusion file** ([scripts/exclude.csv](scripts/exclude.csv), `module_name,reason`) — modules never tested (e.g. `vscode`, `casa`, `miniconda`). Loaded by `get_excluded_modules()`; override path with `--exclusion`. `fhspl` is *always* excluded even with `--inc_extra_mod_dirs`.
- `find_qsub.py` writes a **`skipped.log`** listing modules skipped for having no `test.qsub`, and an **`errors.log`** (only if errors occurred) for modules whose metadata could not be parsed. Always check these before trusting the input CSV.

## Automation

Monthly cron ([scripts/pkgauto_cron.sh](scripts/pkgauto_cron.sh)) makes a timestamped run dir under `/projectnb/rcstest/cronjobs` and `qsub`s [scripts/pkgauto_email.qsub](scripts/pkgauto_email.qsub), which runs discovery → pipeline (`--keep_passed false`) → filters FAILED rows → `email_notif.pl`.

## Gotchas

- **CSV columns are positional contracts across stages.** `find_qsub.py`'s `SccModule.HEADERS`, the two `map{}` tuples in [nextflow/pkgtest.nf](nextflow/pkgtest.nf) (valid → `runTests`, invalid → `reportInvalid`), **both** `test_metrics.csv` heredocs (`runTests` and `reportInvalid` must stay byte-identical in header/column count for `collectFile(keepHeader:true)` to merge cleanly), and `email_notif.pl`'s hard-coded field indices (`split /,/)[2,3,4,9,12]`) all depend on column order/count. Changing one requires changing the others.
- The `runTests` script block is a Nextflow (Groovy) string: shell variables must be escaped as `\$VAR`, while `$module_name` etc. are Nextflow interpolations. Get this wrong and the shell silently misbehaves.
- Nextflow reporting "succeeded" means the *job ran*, not that the *module test passed* — always read the report CSV.
- `.gitignore` excludes `work/`, `.nextflow/`, `*.log*`, and `*.csv`, so generated CSVs and run artifacts (present in the working tree) are untracked by design.
