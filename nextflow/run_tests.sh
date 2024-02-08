#!/bin/bash -l

# Load required module
module load nextflow

# Run nextflow pipeline with example csv file
nextflow pkgtest.nf --csv_input example.csv

# Get the name of the most recent run.
LAST_RUNNAME=`nextflow log -q | tail -1`

# Get only processes with FAILED status and generate report
nextflow log $LAST_RUNNAME -F 'status == "FAILED"' > nf_report.txt





