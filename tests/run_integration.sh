#!/bin/bash
# Run the self-test suite in INTEGRATION mode on an SCC node: real Lmod `module`,
# real `qsub`, and the real SGE scheduler (`--executor sge`). Requires python>=3.9
# and nextflow to be available (e.g. `module load python3 nextflow`).
# Extra args are passed through to pytest, e.g.:
#   bash tests/run_integration.sh --project scv -v
exec pytest "$(dirname "$0")" --mode integration "$@"
