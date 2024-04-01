# PkgAutoTest
This repo contains a Nextflow pipeline and several scripts to perform automated testing of the SCC module software packages.


## Summary

Clone the repository. 

```console
git clone https://github.com/bu-rcs/PkgAutoTest/
```
There are two steps to perform the automated test:

1. Use `find_qsub.py` script to search for modules to test and generate a CSV input file to be used as Nextflow input.
2. Run the nextflow pipeline using the CSV input generated in step 1.
3. Review the results.


## Step 1 - run `find_qsub.py`

The `find_qsub.py` script is located under the `scripts` directory.  Run the script with `-h` to get the usage information for the script.

```console
find_qsub.py -h

positional arguments:
  out_csv               output CSV file for use with Nextflow pipeline.

options:
  -h, --help            show this help message and exit
  -m MOD_NAME, --mod MOD_NAME
                        Name of a specific module to test.
  -d DIRECTORY, --dir DIRECTORY
                        Module publication directory to search for modules to
                        test. This will find all available modules in that
                        directory. Use paths like /share/module.8
  -p PKG_PATH, --pkg PKG_PATH
                        Limit tests to a particular /share/pkg directory.
                        Defaults to /share/pkg.8. Use ALL for modules found in
                        any directory.
  --err ERR_FILE        File to write errors to. Defaults to errors.log. If
                        there are no errors this file is not created.
```

The command below will search `/share/module.8` directory for modules that are published and have a test available. It will also generate a CSV file, named `module8_list.csv', that will be used as an input for the nextflow pipeline. 

```console
find_qsub.py -d /share/module.8 module8_list.csv
```

For each row, in the CSV input file, represents a single module found that has a test.qsub file.  The following are the column definitions for the generated CSV file:


| Column Name          | Description |
| -------------        | ------------- |
| module_name          | Name of the module. |
| version              | Version value of the module. |
| module_name_version  | Module name and Version number combined. |
| module_pkg_dir       | Base directory for the module. |
| module_installer     | The username of the installer of the module extracted from the notes.txt file.|
| module_install_date  | The installation date extracted from the notes.txt file. |
| module_category      | The category for the module extracted from the modulefile.lua. |
| module_prereqs       | The list of module pre-requisite extracted from the test.qsub file. |
| test_path            | The the full path to the test.qsub file. |
| qsub_options         | The qsub options specified in the test.qsub file.*  |

*TODO: Indicate which qsub options are filtered out by `find_qsub.py`.

## Step 2 - Nextflow pipeline

To run the Nextflow pipeline the Nextflow software is required.  On the SCC load the nextflow module.

```console
module load nextflow
```

To run the pipeline, type in the `nextflow` command along with the name of the nextflow script, `pkgtest.nf`.  Additionally, include the `--csv_input` flag and include the name of the CSV input file generated in Step 1.

```console
nextflow pkgtest.nf --csv_input module8_list.csv
```

The nextflow pipeline will read in the input CSV and for each row submit a job.  By default the jobs will be submited under project "rcstest".  If another project is desired, add the ``--project`` flag with the name of the project.

```console
nextflow pkgtest.nf --csv_input module8_list.csv  --project scv
```

One can also run all the tests on the host machine by setting the `--executor` flag to local:
```console
nextflow pkgtest.nf --csv_input module8_list.csv  --executor local
```


### Troubleshooting

- All the Nextflow processes should run successfully, even if the test itself failed.  If Nextflow indicates an error with a process this may indicate there was an issue submitting the particular module test as a job.  Check the input CSV file and the **qsub_options** column to determine if bad qsub options are being passed to Nextflow.  


## Step 3 - Review the results
When the Nextflow pipeline finishes, a CSV file containing the same name as the input CSV file, but with a "report_" prefix (e.g. report_module8_list.csv).  The following are the column definitions for the CSV report:

| Column Name                      | Description |
| -------------                    | ------------- |
| test_result<sup>1</sup>          | The overall test result. e.g PASSED or FAILED |
| module                           | Name of the module tested.  |
| tests_passed                     | Number of times the word "Passed" was found in the stdout stream of the test.qsub run.  |
| tests_failed                     | Number of times the word "Error" was found in the stdout stream of the test.qsub run.   |
| log_error_count                  | Number of times the word "error" was found in the test.qsub log file. (Not used for PASSED/FAILED evaluation)  | 
| exit_code                        | Exit code from running the test.qsub script. | 
| installer                        | The installer of the module.  | 
| category                         | The category of the module as defined in the modulefile.  |
| install_date                     | The installation date extracted from the notes.txt file for the module.  |
| workdir                          | The Nextflow working directory that contains log files for the job.  |

<sub>1</sup> A test passes if the following conditions are met:  
  1. "exit code" from running test.qsub is equal to 0.
  2. Only words "Passed" are found in the stdout when running test.qsub.

## Examples

examples - test all packages, test on one node, test on a particular queue

