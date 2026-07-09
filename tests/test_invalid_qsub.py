"""Self-test for the invalid-qsub feature.

Feature under test:
  * find_qsub.py emits a `qsub_valid` column (True/False) from `qsub -w p`.
  * pkgtest.nf branches on it: valid tests run normally; invalid tests are marked
    FAILED by the local `reportInvalid` process and are never submitted to SGE.

The shared `run_env` fixture (see conftest.py) builds a fake module `pkgselfcheck/1.0`
with two test files: a valid `test.qsub` and an invalid `test.bad.qsub` (bogus PE).
"""


def test_find_qsub_populates_qsub_valid(run_env):
    """find_qsub.py sets qsub_valid=True for the good qsub and False for the bad one."""
    rows = run_env.read_csv(run_env.run_find_qsub())

    valid = run_env.row_by(rows, "test_path", endswith="/test.qsub")
    invalid = run_env.row_by(rows, "test_path", endswith="/test.bad.qsub")

    assert valid["qsub_valid"] == "True"
    assert invalid["qsub_valid"] == "False"


def test_pipeline_fails_invalid_gracefully(run_env):
    """The pipeline PASSES the valid test and FAILS the invalid one without submitting
    it (reportInvalid path -> job_number == NA)."""
    rows = run_env.read_csv(run_env.run_pipeline())

    valid = run_env.row_by(rows, "qsub_file", equals="test.qsub")
    invalid = run_env.row_by(rows, "qsub_file", equals="test.bad.qsub")

    # Valid test ran and passed.
    assert valid["test_result"] == "PASSED"

    # Invalid test failed gracefully, handled locally (never submitted to SGE).
    assert invalid["test_result"] == "FAILED"
    assert invalid["job_number"] == "NA"
    assert invalid["exit_code"] == "1"
