#!/bin/bash -l

CSV_INPUT=$1

if [ -z "$CSV_INPUT" ]; then
    printf "No CSV input argument provided.\n\nExample:\nrun_tests.sh module_list.csv\n\n"
    exit 1
fi

if ! [ -f $CSV_INPUT ]; then
  printf "Input CSV file does not exist.\n\nInput file given: $CSV_INPUT\n\n"
  exit 1
fi

# Load required module
module load nextflow

# Run nextflow pipeline with example csv file
nextflow pkgtest.nf --csv_input $CSV_INPUT





