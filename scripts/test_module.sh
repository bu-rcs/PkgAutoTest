#!/bin/bash

module purge
module use /share/module.8/rcstools
module load nextflow
module load pkgautotest

MOD_NAME=$1
MOD_VER=$2
echo "module to test: $MOD_NAME/$MOD_VER"

CSV=${MOD_NAME}.csv
echo "test csv generated: $CSV"
find_qsub.py -m $MOD_NAME/$MOD_VER $CSV
nf_pkgtest $CSV
