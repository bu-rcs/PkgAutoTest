# Notes from the project meetings

## January 30, 2024
1. TO-DO from last meeting
  * (yun) Modify newpkg - remove statements about Spack. Remove copies of example files and readme's that clutter the test directory, replace with a symlink to copies of an examples dir in the newpkg module. For bash example tests modify as above to print into to stderr.
    * v0.1.9 needs a few minor tweaks:  make a copy of test.qsub, not a symlink. Make a data/ dir.  Put the 4 files (bash_tests.txt, readme.*) in newpkg/ver/install/doc, symlink to that doc directory. (Done)
    * Add a check for 1 log file argument to test.qsub, i.e. "test.qsub /path/to/logfile" is right, "test.qsub" prints an error. If a full path to the log file isn't given, make it assume to write it to the working directory. "sh test.qsub mylog" (Done)
    * See item 2 below, near the top of test.qsub set an environment variable "TEST_COMPLETE=-1" 
then down at the bottom check that, if TEST_COMPLETE=-1 print Error and return exit code 9999 (which we mean "not implemented"). A comment by TEST_COMPLETE=-1 tells us to set this to something else when completed.
	(Yun commented on this - bash exit code range only from 0-255, so I picked 255 as the exit code for this purpose, sysexits.h used up to 78. ) （Done）
  * (brian) work on find_qsub.py command line arguments and implementing new CSV output.
    * This is in progress.
  * (dennis) work on processing stdout/stderr stuff into the report, working with the nextflow log. (none yet)
  * (brian) - email for test account to be created. (DONE) Mike said why?  
2. (Dennis) - When `newpkg` creates a new module, I was thinking we should have the template `test.qsub` fail by default.  That way if for some reason it is not updated, it will fail the test and will get our attention. At the top of test.qsub, have a print statement print "Error" with a comment to delete this before publication. This helps us find tests that are not completed yet. 
3. (Dennis) - This maybe for best practices for test.qsub.  I noticed that for my module "autconf" when the module failed to load, it tested the system autoconf binary instead.  I am thinking maybe we need to use $SCC_<MODULE_NAME>_BIN to make sure the correct binary is being tested.
* This should be listed in a best practices guide, generally check locations of binaries to see if they're in the right place in /share/pkg.8. This can be added to the bash_tests.txt list of recipes.
4. New student interns are here! We need to check that the stderr output lines like: "   >&2 echo "File size check failed, test #2 of 3"" work with nextflow.
5. TODO:
  * (Brian) finish find_qsub.py changes for the new CSV format.
  * (Yun) newpkg changes
  * (Dennis) test stderr in the nextflow report. See what happens. Also handle new CSV format, including auto-loading of prereq modules. 


## January 9, 2024
Brian, Yun, Dennis, Andy

1. Went through Dennis' Nextflow investigations, as documented in issue 4.
  * Use of Nextflow tracers and the Nextflow log give us greater access to what's happening with each job.
  * The Nextflow log output has an option to print stderr, which would let us modify the test.qsub files so that they provide more error information to stderr. The log can be run anytime once a workflow is completed. Example:
```
# pseudo-bash
if [ file_size_check_passed ] then
   echo "Passed"
else
   echo "Error"
   >&2 echo "File size check failed, test #2 of 3"
fi
```
2. We could manipulate the return error code to indicate which tests failed using bit shifting and masking to embed test counts and test indices.
3. CSV format:
```
# note: qsub_options must NOT include "-j y" otherwise the stderr output above won't work right!
# module_prereqs: semicolon separated
# Example:
module_name, version, module_name_version,module_pkg_dir, module_installer,module_install_date,module_category,module_prereqs, test_path,qsub_options
openmpi,4.1.5,openmpi/4.1.5,/share/pkg.8,bgregor,06/27/23,libraries,prereqs;go;here,/share/pkg.8/openmpi/4.1.5/test/test.qsub,-P scv
```
4. How to run find_qsub.py: Brian will work on ideas before the next meeting.
5. TO DO:
   * (yun) Modify newpkg - remove statements about Spack. Remove copies of example files and readme's that clutter the test directory, replace with a symlink to copies of an examples dir in the newpkg module. For bash example tests modify as above to print into to stderr.
   * (brian) work on find_qsub.py command line arguments and implementing new CSV output.
   * (dennis) work on processing stdout/stderr stuff into the report, working with the nextflow log.
   * (brian) - email for test account to be created. (DONE).
   
## December 19, 2023
Brian, Yun, Dennis

1. Recap of Nextflow breakthrough from last week.
2. The trace report from NF should be easily parseable by Perl or Bash to give detailed error reporting on a module that failed one or more of its tests: https://www.nextflow.io/docs/latest/tracing.html#trace-report
3. Exit codes can be set to give more info on failed tests.
4. There is some configuration possible for the HTML execution report:  https://www.nextflow.io/docs/latest/config.html#config-report
5. Dennis suggests adding the module installer name to the CSV file (found in notes.txt).

TODO after Intersession:
1. Come up with a version 1.0 specification:
   * define CSV format for Nextflow input
   * define exact way to call find_qsub.py and how we want to use it.
   * Create Nextflow pipeline with any customizations
   * error reporting tool (prob. in Perl) that gives more detail than Nextflow does.
2. Create a test account to handle running tests.  "rcstest" is in line with rcsr, rcspy. All apps group users need to be able to log in as rcstest.

## December 12, 2023
Brian, Yun

1. Looking into Nextflow:
* we can select a penv (omp or mpi_N_tasks_per_node):  https://www.nextflow.io/docs/latest/process.html#process-penv
* we can select cpus: https://www.nextflow.io/docs/latest/process.html#process-cpus
* and time: https://www.nextflow.io/docs/latest/process.html#process-time
* or arbitrary things like mem_per_core with clusterOptions: https://www.nextflow.io/docs/latest/process.html#process-clusteroptions
* so if this info is in the CSV from find_qsub.py then this should be readable and set up using the Dynamic Process info as described in issue #4.

2. Nextflow test:
* In the code nextflow/ folder look at the `example_dynamic_clusterOptions.nf` and `input_new_params_clusterOptions.csv` files. These use cluster options pulled from the test.qsub file and a dynamic process to let us set arbitrary per-test queue options.

3. TODO:
* Brian - work on find_qsub.py -> extract qsub options, add to CSV format.
* Yun - look into modifying or customizing the reporting. Can this be done from within Nextflow? Or post-modify report.html with Perl or something?
* Modify newpkg so it doesn't always create template test.qsub files, or makes them unrunnable or easily identifiable so they don't get picked up by find_qsub.py. Or rename to test.qsub.template, or use an MD5 hash to identify. 

## December 5, 2023
Brian, Yun, Dennis, Andy

1. Done since last meeting:
* (brian) find_qsub.py - prototype of finding test.qsub files.  Sample output CSV format created.
* (dennis & andy) - Nextflow progress. sample: `/projectnb/scv/milechin/nextflow`  

2. find_qsub.py  improvements
* use "module show" instead of "module load" and parse for SCC_NAME_DIR - this avoids having to load prequisites.
3. Nextflow - nextflow sample at `/projectnb/scv/milechin/nextflow`
* nextflow essentially replaces a call to qsub. How can we specify resources (i.e. multiple cores) to nextflow?  It could be parsed by find_qsub.py and included in the input CSV format. This would have to be handled inside of nextflow. Or, multiple CSV files for single core, 4 core, GPU, etc with a matching nextflow config for each category of job.
* Feasability? - lots of custom work to make nextflow work like this. But - the Nextflow reporting is highly detailed and may solve a lot of issues for reporting.
* Can we add custom columns to the report - count of pass/fail tests?  Would we need to modify test.qsub to make this easier to do? Can Nextflow produce CSV in addition to HTML for use in other tools? n 
4. (yun) Fixes to existing test.qsub
* Should be runnable by any account.
* Some test.qsub write to the test directory (permissions problem)
* should be written so that test.qsub can be _submitted_ from any directory - avoid issues with relative directory usage, etc.
5. A new account, `rcstest` would be useful to run the Nextflow test framework.
6. TO DO:
* (brian) - fix find_qsub.py use `module show` and extract qsub command parameters for the csv - key columns: omp, gpu, gpu_c, mpi
* (yun & andy) - investigate Nextflow capabilities further, especially diff. process runners for different jobs (1 core, 4 core, etc). Also look into customizing the HTML/text report, or the "Trace Report" as discussed above.
* (dennis) - enjoy your vacation
  

## November 30, 2023
Brian, Yun, Dennis

1. Ideas:
* (Dennis) When testing a GUI program, can we get a screenshot of the headless X server?  Ans: [yes](https://unix.stackexchange.com/questions/365268/how-do-i-take-a-screen-shot-of-my-xvfb-buffer), using the "xwd" utility.
* (Dennis) Could this process be run via Nextflow?
2. Major components:
* Test searching script that finds all test.qsub files (based on specific search criteria) and creates a list to be submitted. 
* A submission script that submits the list of test.qsub's to the queue along with a job to run the post-test analysis.
* Reporting script that analyzes the pass/fail status of all tests, provides a useful report and some standard CSV type data for use in other reporting if desired.
* Improved documentation, guidance, and examples of writing test.qsub scripts. 
3. Meeting schedule:
* Weekly, Tuesdays, 10AM-11AM, viz Zoom.
4.  Minimal starting point:
  * Basic way to run the test searching script so it finds some test.qsb files. 
  * Format of a test.qsub list from the test searching script. Needed for the submission script.
  * Sample output directory for use with the reporting script.
5. Project timeline for remainder of 2023:
 * Dec 5th - issues 1, 2, and 4 prototyped.  Note: issue 2 depends on issue 1 delivering an initial file format in a timely fashion by Brian.




## November 7, 2023
Brian, Yun, Dennis

1. Project goal: A master testing program(s) to test modules on the SCC based off of the initial test.qsub appoach.
* Script that discovers all available test.qsub files and submits them to the cluster.
  * This can include running the in-development "module_check" program on all modules prior to qsub-ing test.qsub. 
* Script (almost certainly Perl) to ingest the output of the test.qsub runs and generates a report of modules that pass/fail
  * Output should include generically formatted like CSV for use in other analytics.  
* Improved documentation and examples on creating effective test.qsub scripts - how do we decide what passes or fails, what to check, creating reference output files, handling GUI programs.
* Annotation for modulefiles to indicate if it's a GPU, GUI, MPI, etc. program. The "whatis" field is already gathered by the module cache and can be extracted using the "spider" program.
  * Used by the code that creates the software page JSON: https://github.com/bu-rcs/rcs_tools/tree/master/software_page
3. Decide on dev and meeting schedule: Weekly for an hour.
* Start with a 2-hour meeting to work out a detailed outline, create issues and a timeline for a prototype. 
5. Dennis found a Python interface to lmod that could be useful:  https://github.com/buildtesters/lmodule
  
TODO: Brian will schedule the 2-hour meeting for the week of Nov 20th (or the following week if needed due to Thanksgiving).  

## October 27, 2023

Brainstorming the components of the project (SI and Brian):   
  1. A test script that tests modulefile:
	   - if env. variables are defined correctly;
	   - if permissions are set correctly;
  2. Test directory:  
	  - write documentation for an "unexperienced" person on how to test software in "test" directory;
	  - what do we do if we need to test multiple executables (or options) installed in the same module?
	  - what do we meanwhile? How do we mark those software packages that have already been installed (or being installed) so we could return to them later?
  3. Report of the usage of a module within a certain time period (Yun). This would help identifying modules that may need to be retired. It should be flexible:
		- time (start,end)
		- report projects
		- report separate users
  4. Create a list of published modules and   
		- separate it into 2 categories: software that has "test" and software that does not
		- also report if this software comes from centos6 (pkg), centos7(pkg.7), alma8(pkg.8) or older than centos6(apps)
  5. For the modules that interact with cloud we need to create a special category in such a way that this automation system recognize those and report them correctly.
