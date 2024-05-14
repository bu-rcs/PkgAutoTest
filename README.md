# PkgAutoTest

This repo contains a [Nextflow](https://www.nextflow.io/docs/latest/index.html) pipeline and several scripts to perform automated testing of the SCC module software packages.

## Running the Pipeline

First one needs to get a copy of the scripts.  On the SCC load the `nextflow` and `pkgautotest` module to get the latest stable release:

```bash
module load nextflow
module use /share/module.8/rcstools
module load pkgautotest
```

Alternatively, you can clone the repository:

```bash
git clone https://github.com/bu-rcs/PkgAutoTest/
```

There are three general steps to run this Nextflow pipeline:

1. [Step 1](#step-1---run-find_qsubpy) - Use `find_qsub.py` script to search for modules to test and generate a CSV input file to be used as Nextflow input.
2. [Step 2](#step-2---nextflow-pipeline) - Run the nextflow pipeline using the CSV input generated in step 1.
3. [Step 3](#step-3---review-the-results) - Review the results.

If you run into an issue, take a look at the [Troubleshooting](#troubleshooting) section.

## Step 1 - run `find_qsub.py`

After loading the SCC `pkgautotest` module, the `find_qsub.py` will be available on the $PATH environment variable.  Run the script with the `-h` flag to get a description of the required and option arguments.

```bash
find_qsub.py -h
```

Here are two examples of how to use the script.

- **Find all module tests in `/share/pkg.8`**

  The following command will search published modules in `/share/pkg.8` for available tests and generate a CSV file called `module8_list.csv`, which will contain the results of the search.

  ```bash
  find_qsub.py module8_list.csv
  ```

- **Find all module tests for a specific module**

  The command below will search published modules in `/share/pkg.8` for named "gdal" and generate a summary CSV file called `gdal.csv`.

  ```bash
  find_qsub.py -m gdal gdal.csv
  ```

For each row, in the CSV file, represents a single module found that has a `test.qsub` file. **Variants of `test.qsub` are allowed with the pattern `test.*.qsub`**.  For example, a test directory might have a `test.qsub` and a  `test.gpu.qsub` for tests that run on CPU and GPU nodes. A test directory might only contain a `test.mpi.qsub` to hint that the test will be running MPI-based software. If a test directory has more than one test.qsub-type file there will be a row for each one in the CSV file.  

The following are the column definitions for the generated CSV file:

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
| qsub_options         | The qsub options specified in the test.qsub file. The `-j`, `-P`, and `-N` qsub arguments are removed if they exist in test.qsub.  |

Before proceeding to step 1, check to see if an error txt file was created and examine it.  Any modules listed in the error file were not processed properly and are excluded from the CSV file.

## Step 2 - Nextflow pipeline
This sections shows a [simplified command](#simple-execution) of running the pipeline.  If you are familiar with Nextflow, you can explore the [Advanced](#advanced) section.

### Simple Execution
To run the Nextflow pipeline the Nextflow software is required.  On the SCC make sure the nextflow module is loaded.

```bash
module load nextflow
```

When using the SCC `pkgautotest` module, run the `nf_pkgtest` command and specify the CSV file generated in [Step 1](#step-1---run-find_qsubpy) as the first argument. In this example we specify `module8_list.csv` as the CSV file.

``` bash
nf_pkgtest module8_list.csv
```

This script will launch Nextflow pipeline and will use the CSV file to determine which modules to test. Each module test will be submitted as a job and by default will use `rcstest` project.  See [Advanced section](#advanced) to see how to change the project name.

Here is an example of submitting the pipeline as a batch job:

``` bash
qsub nf_pkgtest module8_list.csv
```


When Nextflow is done, an indication of a successful run is when all the processes are marked as succeeded.  This indicates the jobs were successful submitted and ran, but it does not indicate if the actual module test passed or failed.  One needs to examine the report CSV file that was generated in the working directory.  See [Step 3](#step-3---review-the-results) to learn more about the output CSV file.

In the example below, 167 of 167 processes were submitted and in the console, the Nextflow summary indicates 167 succeeded.  This indicates the Nextflow pipeline ran successfully.

```console
[scc ]$ nextflow pkgtest.nf --csv_input module8_list.csv 
N E X T F L O W  ~  version 21.10.6
Launching `pkgtest.nf` [golden_turing] - revision: ed8e93e871
executor >  sge (167)
[9f/7758d6] process > runTests (fmriprep/23.1.4) [100%] 167 of 167 \ufffd\ufffd\ufffd
./report_module8_list.csv
Completed at: 03-May-2024 10:22:55
Duration    : 1h 2m 56s
CPU hours   : 3.4
Succeeded   : 167
```

If a process failed, check the [Troubleshooting](#troubleshooting) section.  Otherwise proceed to [Step 3](#step-3---review-the-results)

### Advanced

To run the pipeline, type in the `nextflow` command along with the name of the nextflow script, `pkgtest.nf`.  Additionally, include the `--csv_input` flag and include the name of the CSV input file generated in [Step 1](#step-1---run-find_qsubpy).

```bash
nextflow pkgtest.nf --csv_input module8_list.csv
```

If you are using the SCC `pkgautotest` module, the environment variable `$PKGTEST_SCRIPT` will contain the path to the `pkgtest.nf` script, which can be used to run the pipeline:

```bash
module load nextflow
module load autopkgtest
nextflow $PKGTEST_SCRIPT --csv_input module8_list.csv
```

The nextflow pipeline will read in the input CSV and for each row submit a job.  By default the jobs will be submited under project "rcstest".  If another project is desired, add the ``--project`` flag with the name of the project.

```bash
nextflow pkgtest.nf --csv_input module8_list.csv  --project scv
```

One can also run all the tests on the host machine by setting the `--executor` flag to local. This can be useful if you are testing a system that is not yet available in the queue:

```bash
nextflow pkgtest.nf --csv_input module8_list.csv  --executor local
```

Proceed to [Step 3](#step-3---review-the-results) to review the test results.

## Step 3 - Review the results
When the Nextflow pipeline finishes, a CSV file containing the same name as the input CSV file, but with a "report_" prefix (e.g. report_module8_list.csv). Aside from your favorite text editor, on the SCC a spreadsheet tool is available with the `libreoffice` software. VSCode has a convenient built-in CSV display and there is a plugin ("Rainbow CSV") available to enhance CSV viewing. The following are the column definitions for the CSV report:

| Column Name                      | Description |
| -------------                    | ------------- |
| job_number                       | The job number for the job. |
| hostname                         | The hostname of the node the job ran on. |
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

A test passes if the following conditions are met:  

  1. "exit code" from running test.qsub is equal to 0.
  2. Only words "Passed" are found in the stdout when running test.qsub.

To examine the logs of a specific test, `cd` into the directory specified in the `workdir` column.  In the directory you will find the following key items:

| Name                      | Description |
| -------------             | ------------- |
| .command.err                | Standard error output for the `.command.sh` script. |
| .command.log                | Standard output for the `.command.sh` script. |
| .command.out                | Standard output for the `.command.sh` script. |
| .command.run                | The qsub script used to submit the job |
| .command.sh                | The bash script Nextflow ran to setup the test and run the test. |
| test                | This is the "test" directory for the module. Nextflow copied the original test directory for the module into this working directory.  Additional files may have been generated in this directory, depending how the `test.qsub` file was written. |
| test/test.qsub         | This is a copy of the `test.qsub` file. There are a few lines added by Nextflow to facilitate running the test inside the pipeline but they do not have any effect on how the job executes. [#18](https://github.com/bu-rcs/PkgAutoTest/issues/18)|
| log.txt                | The log file generated by running the `test.qsub` file. |
| results.txt                | The file contains the standard output of the `test.qsub`, specifically the values of "Passed/Error".  This is used to determine if the module passed or failed the test. |
| test_metrics.csv                | The result of the test in a CSV format. |

## Step 4 - Remove working directories

Due to the copying of the module test directories to the working directories before tests are run a fair amount (several dozen GB) of disk space is consumed by the working directories. After reviewing the Nextflow results it is recommended that you delete at least the working directories from tests that have passed from the `/projectnb/rcstest` project.


## Troubleshooting

**Nextflow Process(es) failed while running Nextflow pipeline.**

This issues is most likely to occur when the scheduler has an issue with the qsub options being used by Nextflow.  Some modules require specific resources and some of those qsub options are extracted by the find_qsub.py script, which are saved under the column **qsub_options** in the resultant CSV file.  The following are some suggestions on ways to troubleshoot this issue.

- **OPTION 1:** In the directory where the nextflow script ran, there should be a hidden file called `.nextflow.log`.  This will contain information about the nextflow pipeline and actions taken for each process.  In this file, search for the keyword "Error" or "Failed" to find which process (or modules) failed to start the test. Sometimes additional information is shown in these logs that may indicate what went wrong.

  Below is an example exerpt from a `.nextflow.log` file of a "Failed" job submission for module R/4.3.1 test.

    ```console
    ...
    May-03 16:13:07.131 [Task submitter] DEBUG nextflow.executor.GridTaskHandler - Failed to submit process runTests (R/4.3.1) > exit: 5; workDir: /projectnb/rcstest/milechin/PkgAutoTest/nextflow/work/43/1835ee47a432b38cdffc3c7599a607
    qsub: Unknown option 
    ...
    ```

    Notice that in this example it indicates "qsub: Unknown option" as the issue.  `cd` into the `workDir` defined in the error message and examine the hidden file `.command.run`.  This is the qsub script submited to the scheduler.  Examine the qsub options and make sure all of them are defined properly.  If any are not correct, check the `qsub_options` column in the input CSV file to make sure those are extracted properly from the original test.qsub file.

- **OPTION 2:** If you are able to identify the hash code for the process, such as `9f/7758d6`, then you can navigate to the working directory of that process.  In the directory where you ran the Nextflow script, there is a `work` directory.  `cd` into the `work` directory.  This directory will contain  2 character named directories.  `cd` into the directory that matches the hash code for the module test.  For our example it is `9f`.  Within this directory will be additional directories with longer hash values.  `cd` into the directory that matches the starting of the hash of interest.  For our example it is `7758d6...`.  

    Now you are in the working directory of the module.  Run `ls -la` to see the hidden files.  Examine the log files to search for any error messages that may indicate what went wrong.

- **OPTION 3:** By default this Nextflow script will ignore Failed processes and continue to the next one.  This option can be disabled and the additional benefit is one will get additional information about the issue.  To terminate Nextflow upon error, add the `errorStrategy` flag, like in the example below:

  ```console
  nextflow pkgtest.nf --csv_input module8_list.csv  --errorStrategy terminate
  ``` 

**Nextflow Process(es) are running forever**
  
Use `qstat` to determine the job numbers of the stuck jobs.  The job name will contain the module name and version number.  Use `qdel job_number` to delete the job.  It may take Nextflow a couple minutes to determine the job was deleted.  Nextflow will most likely error this test and so the results will not be included in the report CSV file.
