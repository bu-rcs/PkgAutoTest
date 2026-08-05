#!/bin/bash
# Run the self-test suite in LOCAL mode: stubbed module/qsub, pipeline --executor local.
# No Lmod, no SGE, no `module load` (requires the conda env in tests/environment.yml).
# Extra args are passed through to pytest, e.g.:
#   bash tests/run_local.sh -v --junitxml=tests/results.xml
exec pytest "$(dirname "$0")" --mode local "$@"
