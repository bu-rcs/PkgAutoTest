"""Shared pytest machinery for the PkgAutoTest self-test suite.

Two run tiers, selected with --mode:

  * local (default)  -- `module` and `qsub` are replaced by stubs in tests/stubs/,
                        and the pipeline runs with `--executor local`. No Lmod, no
                        SGE, no `module load`; runs anywhere with the conda env
                        (see tests/environment.yml).
  * integration      -- the real Lmod `module` and real `qsub` are used, and the
                        pipeline runs on the real scheduler (`--executor sge` by
                        default). Requires an SCC node.

Each feature under test is its own tests/test_<feature>.py module. They obtain a
per-test `run_env` fixture that builds a throwaway fake module on disk and exposes
helpers to run find_qsub.py and the Nextflow pipeline and to parse their CSVs.
"""

import os
import shutil
import subprocess
import csv
import sys
from pathlib import Path

import pytest

# Repo layout.
TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parent
FIND_QSUB = REPO / "scripts" / "find_qsub.py"
PKGTEST_NF = REPO / "nextflow" / "pkgtest.nf"
FIXTURES = TESTS_DIR / "fixtures"
STUBS = TESTS_DIR / "stubs"

# The fake module used by the fixture.
MOD = "pkgselfcheck"
VER = "1.0"
MOD_VER = f"{MOD}/{VER}"


def pytest_addoption(parser):
    parser.addoption(
        "--mode", action="store", default="local",
        choices=["local", "integration"],
        help="local: stub module/qsub + executor local (default). "
             "integration: real module/qsub + SGE (requires an SCC node).",
    )
    parser.addoption(
        "--project", action="store", default="rcstest",
        help="SGE project used for the qsub -P directive (integration/sge only).",
    )
    parser.addoption(
        "--executor", action="store", default=None,
        help="Nextflow executor. Default: 'local' in local mode, 'sge' in integration mode.",
    )
    parser.addoption(
        "--keep", action="store_true", default=False,
        help="Keep the per-test work directory instead of deleting it.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: test only meaningful on a live SCC (Lmod + SGE)")


@pytest.fixture(scope="session")
def mode(request):
    return request.config.getoption("--mode")


@pytest.fixture(scope="session")
def project(request):
    return request.config.getoption("--project")


@pytest.fixture(scope="session")
def executor(request, mode):
    chosen = request.config.getoption("--executor")
    if chosen:
        return chosen
    return "local" if mode == "local" else "sge"


def _have(cmd):
    """Is `cmd` runnable? Handles both PATH binaries and exported shell functions
    (like Lmod's `module`), by asking bash whether the name resolves to anything."""
    return subprocess.run(
        ["bash", "-c", f"command -v {cmd} >/dev/null 2>&1 || type {cmd} >/dev/null 2>&1"]
    ).returncode == 0


class RunEnv:
    """Builds a throwaway fake module and runs find_qsub.py / the pipeline against it."""

    def __init__(self, workdir, mode, project, executor):
        self.workdir = Path(workdir)
        self.mode = mode
        self.project = project
        self.executor = executor
        self.pkg_root = self.workdir / "pkg"
        self.pkg_dir = self.pkg_root / MOD / VER
        self.modulefiles = self.workdir / "modulefiles"
        self.out_csv = self.workdir / "out.csv"
        self.report_csv = self.workdir / f"report_{self.out_csv.name}"
        self._build_fixture()
        self.env = self._build_env()

    def _build_fixture(self):
        (self.pkg_dir / "install").mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "test").mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "notes.txt").write_text(
            "INSTALLER: selftest\nINSTALLED: 01/01/25\n")

        # Render the modulefile with absolute paths.
        upper = MOD.upper().replace("-", "_")
        lua = (FIXTURES / "modulefile.lua.in").read_text()
        lua = lua.replace("@MOD_UPPER@", upper).replace("@PKGDIR@", str(self.pkg_dir))
        real_lua = self.pkg_dir / f"{MOD}.lua"
        real_lua.write_text(lua)

        # Copy the two test.qsub variants, substituting the project.
        for name in ("test.qsub", "test.bad.qsub"):
            txt = (FIXTURES / name).read_text().replace("@PROJECT@", self.project)
            dest = self.pkg_dir / "test" / name
            dest.write_text(txt)
            dest.chmod(0o755)

        # Publish the modulefile as a symlink (find_qsub only discovers .lua symlinks).
        modname_dir = self.modulefiles / MOD
        modname_dir.mkdir(parents=True, exist_ok=True)
        link = modname_dir / f"{VER}.lua"
        link.symlink_to(os.path.relpath(real_lua, modname_dir))

    def _build_env(self):
        env = os.environ.copy()
        if self.mode == "local":
            # Use the stubs: prepend them to PATH and tell the module stub where the
            # fake package lives. Also delete Lmod's exported `module`/`ml` functions
            # so the child /bin/sh resolves `module` to our PATH stub instead.
            env["PATH"] = f"{STUBS}{os.pathsep}{env.get('PATH', '')}"
            env["STUB_PKG_ROOT"] = str(self.pkg_root)
            for key in list(env):
                if key.startswith("BASH_FUNC_module") or key.startswith("BASH_FUNC_ml"):
                    del env[key]
            # pkgtest.nf's runTests echoes SGE-provided variables ($NSLOTS, $QUEUE,
            # $JOB_ID, ...), and Nextflow runs task scripts with `set -u`, so any
            # unset variable aborts the task. Off-SGE (executor local) these are not
            # set, so provide inert defaults (SGE would supply them for real).
            for key, val in (("NSLOTS", "1"), ("QUEUE", "local"), ("JOB_ID", "local"),
                             ("HOSTNAME", "localhost"), ("USER", "selftest")):
                env.setdefault(key, val)
        return env

    # -- runners -----------------------------------------------------------

    def run_find_qsub(self):
        """Run find_qsub.py against the fixture; return the path to out.csv."""
        cmd = [
            sys.executable, str(FIND_QSUB),
            "--inc_extra_mod_dirs",          # work-dir path contains '/test...'; bypass exclusions
            "-d", str(self.modulefiles),
            "-m", MOD_VER,
            str(self.out_csv),
        ]
        subprocess.run(cmd, cwd=self.workdir, env=self.env, check=True)
        return self.out_csv

    def run_pipeline(self):
        """Ensure out.csv exists, run the Nextflow pipeline; return the report path."""
        if not self.out_csv.exists():
            self.run_find_qsub()
        cmd = [
            "nextflow", str(PKGTEST_NF),
            "--csv_input", self.out_csv.name,     # report_<name> is derived from this
            "--executor", self.executor,
            "--project", self.project,
        ]
        subprocess.run(cmd, cwd=self.workdir, env=self.env, check=True)
        return self.report_csv

    # -- CSV helpers -------------------------------------------------------

    @staticmethod
    def read_csv(path):
        """Return the CSV rows as a list of dicts, keyed and valued by *stripped*
        header names (the report CSV has spaces after commas)."""
        with open(path, newline="") as fh:
            reader = csv.reader(fh)
            header = [h.strip() for h in next(reader)]
            rows = []
            for raw in reader:
                if not raw or not any(cell.strip() for cell in raw):
                    continue
                rows.append({h: v.strip() for h, v in zip(header, raw)})
            return rows

    @staticmethod
    def row_by(rows, col, equals=None, endswith=None):
        """Return the single row whose `col` matches; assert exactly one match."""
        def match(v):
            if equals is not None:
                return v == equals
            if endswith is not None:
                return v.endswith(endswith)
            raise ValueError("row_by needs equals= or endswith=")
        found = [r for r in rows if match(r.get(col, ""))]
        assert len(found) == 1, (
            f"expected exactly one row with {col} "
            f"{'==' if equals is not None else 'endswith'} "
            f"{equals if equals is not None else endswith!r}, got {len(found)}: {rows}")
        return found[0]


@pytest.fixture
def run_env(request, mode, project, executor, tmp_path_factory):
    """Per-test environment. Preflights the mode's external tools (skips with a
    helpful message if missing), builds the fixture on a shared-FS work dir, yields
    a RunEnv, and cleans up unless --keep."""
    # Preflight: required external tooling for this mode.
    missing = []
    if mode == "local":
        if not _have("nextflow"):
            missing.append("nextflow")
    else:  # integration
        for tool in ("module", "qsub", "nextflow"):
            if not _have(tool):
                missing.append(tool)
    if missing:
        pytest.skip(
            f"[{mode} mode] missing required tool(s): {', '.join(missing)}. "
            f"See tests/environment.yml / tests/README.md.")

    # Work dir on a shared filesystem (needed for integration --executor sge; also
    # fine for local). Placed under the repo, not node-local /tmp or /scratch.
    workdir = REPO / "tests" / f".selftest_work.{os.getpid()}.{request.node.name}"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    env = RunEnv(workdir, mode, project, executor)
    try:
        yield env
    finally:
        if not request.config.getoption("--keep"):
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"\n[--keep] work dir retained: {workdir}")
