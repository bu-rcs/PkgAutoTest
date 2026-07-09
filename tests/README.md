# PkgAutoTest self-tests

A small [pytest](https://docs.pytest.org/) suite that validates PkgAutoTest's own
code against a checked-in fixture (not against live cluster modules). Each feature
is its own `test_<feature>.py` module; shared machinery lives in `conftest.py`.

The first module, [test_invalid_qsub.py](test_invalid_qsub.py), covers the
`qsub_valid` feature: `find_qsub.py` flags tests whose qsub options are rejected by
`qsub -w p`, and `pkgtest.nf` marks those FAILED via the local `reportInvalid`
process without submitting them to SGE.

## Two tiers (the `--mode` option)

| Mode | `module` / `qsub` | Pipeline executor | Needs |
| ---- | ----------------- | ----------------- | ----- |
| `local` (default) | **stubbed** (see [stubs/](stubs/)) | `local` | python≥3.9, tqdm, pytest, nextflow — no Lmod, no SGE, no `module load` |
| `integration` | **real** Lmod + real `qsub` | `sge` | an SCC node with Lmod + SGE, plus python≥3.9 & nextflow |

Both tiers build the same fixture (a fake module `pkgselfcheck/1.0` with a valid
`test.qsub` and an invalid `test.bad.qsub`) and assert the same results.

## Running locally (no module load, no SGE)

```bash
# One-time: create the environment (on the SCC, `module load miniconda` first).
conda env create -f tests/environment.yml
conda activate pkgautotest-selftest

# Run
bash tests/run_local.sh -v
```

## Running the integration tier (on an SCC node)

```bash
module load python3 nextflow           # or use the conda env
bash tests/run_integration.sh --project scv -v
```

`--project` sets the SGE `-P` project for the submitted job (default `rcstest`).
Add `--executor local` to exercise integration mode without submitting to SGE.

## How results are reported

- **Console**: one line per test plus a summary (`2 passed` / `1 failed in ...`).
  On failure, pytest shows the actual vs expected values.
- **Exit code**: non-zero if any test fails — usable in cron/CI.
- **JUnit XML** (optional): `bash tests/run_local.sh --junitxml=tests/results.xml`.

## Continuous integration

The **local** tier runs automatically on GitHub Actions for every push to `main`
and every pull request (see [`.github/workflows/tests.yml`](../.github/workflows/tests.yml)).
The runner installs Python + Nextflow + Java, points `/bin/sh` at bash (find_qsub.py
uses a `|&` bashism), and runs `tests/run_local.sh`. The integration tier is SCC-only
and is not run in CI.

## Adding a new test

Create `tests/test_<feature>.py` with one or more `test_*` functions. Reuse the
`run_env` fixture from `conftest.py` (it builds the fixture and exposes
`run_find_qsub()`, `run_pipeline()`, `read_csv()`, and `row_by()`), or add new
fixtures/fixture files for other scenarios. pytest discovers `test_*.py`
automatically. Mark cluster-only tests with `@pytest.mark.integration`.

## Layout

```
tests/
  conftest.py            # options (--mode/--project/--executor/--keep) + run_env fixture
  test_invalid_qsub.py   # the qsub_valid feature test (2 tests)
  fixtures/              # test.qsub, test.bad.qsub, modulefile.lua.in (templates)
  stubs/                 # fake `module` and `qsub` used in local mode
  environment.yml        # conda env for local runs
  pytest.ini
  run_local.sh run_integration.sh
```
