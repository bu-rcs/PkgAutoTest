# Notes from the project meetings

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
