# Notes from the project meetings

## January 28, 2025
1. Automation: run all package testing on a monthly basis with a cronjob.
  * We need a post-testing script that reads in the results.csv file and emails everyone with failed tests, maybe with a 2 week deadline to fix it.
  * once this is in place a v1.1 release will be done.
  * Package authors who aren't in RCS anymore have theirs emailed to Brian.

## June 4, 2024
1. using `--no_exclude` and `-d` to get  `/share/module.8/test`:  Add this to the find_qsub.py help message.
2. Tutorial meeting scheduled for Friday 6/7 at 10am.
3. Apps team members + Charlie were added to the rcstest project by Brian.

## May 28, 2024
1. Dennis tested `find_qsub.py -m` flag and it seems to work.
   Yun - suggested maybe we should list in the error file for modules that don't currently have a test.  Dennis - Something we can discuss with Brian next time.
2. Reviewed and tested `--no_exclude`, determined that the `--no_exclude` and `-d` to get results for only the `/share/module.8/test` directory.
3. We are good to present the PkgAutotest to the team on Wednesday.  Dennis will complete pull request, tag it with version 1.0, and update the SCC module.
   Andy - Maybe we should have office hours on Fridays where people can try it and ask questions.
5. We all agree we should have a test setup to check nextflow script and find_qsub.py script and compare to expected output.  We will create an issue for this task.
6. Apps team need to be added to rcstest project.  Dennis will ask Brian about the status of this task.

## May 21, 2024
1. find_qsub.py - can now specify a module:
`find_qsub.py -m gcc/13.2.0 out.csv`
or 
`find_qsub.py -m gcc/13.2.0,python3 out.csv`
2. find_qsub.py - all /share/pkg.* directories are searched by default. A new "--no_exclude" flag has been added, when present the /share/module.8/test and rcstools directories are searched for modules with test directories.
3. To do: Approve pull request to merge develop back into main, tag 1.0 release.
4. To do: a test setup. Maybe something like a directory in the git repo of modules that will produce a known set of passes and fails for the nextflow pipeline.

## May 14, 2024
1. find_qsub.py - capability to add module versions is not quite implemented.
2. Reviewed & edited README.md
3. Dennis & Andy looked @ Rshiny.
   * Did some work on getting this working.
   * Need to figure out how to get Rshiny to select the right CSV.

## May 7, 2024
1. find_qsub.py - single module testing is implemented. The module names can be comma separated:
   * `python3 find_qsub.py -m gcc tests.csv` OR `python3 find_qsub.py -m gcc,R tests.csv`
   * TODO:  add capability to include module versions:  `python3 find_qsub.py -m gcc/12.2.0,R tests.csv`
   * TODO:  add example of calling find_qsub.py to its help message.
2. Dennis added a section to `pkgtest.nf`. This tacks on a line of bash code to kill any instances of Xvfb launched by the job. This is to workaround the trapping of all user signals for Nextflow jobs which is built into Nextflow shell handling. This prevents Xvfb from running until the job terminates. Seems to work! Brian suggests removing the filter for Xvfb and just killing any child processes, this covers any case where the test might have put something into the background.  Issue #18.
3. Dennis:  vscode is handy to view Nextflow results. Running `less` in its terminal makes directories in links, ctrl-click on them to see the directories.
* demo'd - it works nicely.
4. Review the README.  Needs an update fo new find_qsub.py help message, example nextflow qsub. Add section on running from /projectnb/rcstest.
5. Goal for 5/14 meeting: do a 1.0 release and publish via /share/module.8/rcstools, then schedule an RCS app team meeting to show everyone how to run it. 

## April 30, 2024
1. Yun ran a complete test, see issue #17.
* GUI processes are still running until the end of the job (12 hrs).
* Easy to go from the report.csv to a directory for a job with the log.txt/results.txt files to investigate a failed job.
2. (brian) - future feature request: add the runtime for each job to the report.csv.
* this would take some time. As a quick fix adding the SGE job id for each job lets us look this up.
3. Xvfb running for 12 hours, see issue #18.
4. Remaining stuff:
* find_qsub.py - bring back single module testing - (brian) not done yet.
* Rshiny display
* Xvfb fix
* Documentation here plus short instructions on the software install wiki.

## April 25, 2024
1. Test of instructions for nextflow by Andy. See issue #16.
2. Nextflow can be run with a "resume" flag, ex. `nextflow run <script> -resume`  This should let us run a short nextflow job to schedule everything, then go back later and re-run with -resume to finish the analysis of the test jobs.
   * we'll need to test this.
3. The nextflow wait issue with Xvfb may be due to the nextflow .command.run script. There may (should?) be some setting we can change that will keep Nextflow from waiting for all process id's in a job to exit before exiting the job. 

## April 11, 2024
1. TO-DO from last time:
* Xvfb test jobs exited as expected. When run under Nextflow they run for 12 hours (i.e. job timeout). Does Nextflow have some sort of "wait for all processes to complete" behavior?
* find_qsub.py - bring back single module testing - (brian) not done yet.
* Dennis has a draft of instructions on running the Nextflow pipeline:  https://github.com/bu-rcs/PkgAutoTest/tree/develop
2. Target - week of May 5 for RCS App team release, provided Nextflow pipeline issue can be worked out before the end of next week. Main remaining work is find_qsub.py polishing and documentation.  We want this released before tutorials start at the end of May.
3. Andy - take the draft instructions for a test drive next week to see how it goes. The output of find_qsub.py can be cropped to the first 10 rows for expediency.
  * Run from the /projectnb/rcstest directory
  * Nextflow processes should all succeed even if some of the tests fail (we're interested in the nextflow pipeline, not the tests). 
4. Outstanding items:  find_qsub.py module capability, documentation, nextflow debugging, and an Rshiny method to present the Nextflow report. 
5. Andy looked into Rshiny presentation:  https://github.com/bu-rcs/PkgAutoTest/issues/15
* Andy's "App-3" Rshiny app renders a table with row filters, drop downs, etc. based on the "mpg" dataset built into ggplot2. This is exactly what we had in mind. Nextflow can put a copy of the "app.R" Rshiny code in the same directory as its report.csv so the OnDemand Shiny server can open that directory and display the report.csv for a particular pipeline run.
6. Meeting on April 16 is cancelled as Brian, Yun, and Dennis will be on vacation. Next meeting is April 23. 

## April 2, 2024
1. TO-DO from last time:
* newpkg/0.2.1 is released to the SCC. Apps team was notified in the weekly meeting.
* find_qsub.py: completely re-factored, now scans entire `/share/module.8` directory to find published modules, then filters down to `/share/pkg.8` ones (or other dir based on a command line argument). The ability to specify a single module for testing is currently missing but will be added shortly.  Support for test.qsub, test.gpu.qsub, test.mpi.qsub etc is included. 
* Rshiny code - check for next time.
2. move next week's meeting to Thursday.
3. Dennis ran a Nextflow pipeline.
* All jobs ran but the pipeline script stalled/hung at the command line.
* Took 18 hours to complete, but the queue is very busy these days.
* GUI jobs may be running for 12 hours and not terminating properly. Test: job 5845070, just runs Xvfb in the background. Runtime should be 1 second. Does this job for more?
  * /projectnb/scv/bgregor/sandbox/xvfb - gui.qsub
  * Just "Xvfb &" ran in 1 second before the job quit as expected.
  * re-submitted, it will test "xeyes" with out usual timeout command. Job 5845119.
4. Xvfb (GUI testing) jobs should have "killall Xvfb" at the end according to newpkg instructions, but many were written beforehand. find_qsub.py could detect that case and shorten the job time to 1 hour. Depends on the test (job 5845070). Or Nextflow could detect when Xvfb is used and set that in the pipeline. We should think about this.
5. Dennis has a draft of instructions on running the Nextflow pipeline:  https://github.com/bu-rcs/PkgAutoTest/tree/develop
* the README will be very detailed, a simple instruction doc like SCC_INSTRUCTIONS.md will be done when it's ready for the group.
6. Target - week of May 5 for RCS App team release, provided Nextflow pipeline issue can be worked out before the end of next week. Main remaining work is find_qsub.py polishing and documentation.  We want this released before tutorials start at the end of May.

## March 26, 2024
1. newpkg - v0.2.1 release was created. Yun will create an SCC module and remove /share/module.8 links to old versions.
2. find_qsub.py - existing design of the code is crummy. Brian is re-writing to use Python classes. This will re-use much of the existing code but will be much easier to debug and get working 100% correctly.
3. report.csv pretty formatting - this was found quickly:  https://github.com/derekeder/csv-to-html-table   Seems nice, let's try it.
4. (andy) - will look to see if there's a simple RShiny code that'll let you browse to a report.csv and display it.  This is easier to maintain for RCS than an html/css/javascript solution.


## March 19, 2024

1. TODO from last time:
* rcstest project requested.  Done, project is created, owned by Brian. Dennis, Andy, and Yun are added.
* Katia needs to choose new variable for newpkg update
* Fix find_qsub.py bugs (not yet)
2. (dennis) check out find_qsub.py, try to fix bugs.

## March 12, 2024
1. TODO from last time:
* request rcstest project (not done yet)
* newpkg updated as a new release? (after Katia is back from vacation)
2. Running Nextflow on /share/pkg.8
  * find_qsub.py has some bugs in its output csv, needs fixing
  * Dennis ran a repaired csv, wallclock time was ~1 hr. Some tests passed, some failed.
  * Some bugs in Nextflow were found and fixed (to be checked in shortly).
  * The nextflow test fails because Nextflow creates a .lock file and cannot execute another Nextflow instance. This just means the nextflow test.qsub's will have to be tested manually.
  * Current work output directory is `/projectnb/scv/milechin/nf_pkg8`  Check the file report.csv. Note the installer column is not currently reliable due to the find_qsub.py.  A report.html has not yet been created.
  * nextflow work directory is 15GB. 
3. (brian) - fix find_qsub.py bugs. Yun suggests using /share/module.8 and following symlinks to get the directories of published modules. This will be faster & more reliable than searching /share/pkg.8 as is done now.



## March 7, 2024
1. TODO from last time:
* (brian) find_qsub.py takes an argument to check all /share/pkg.8 modules (DONE!) See new arguments in find_qsub.py, also it now needs the `python3/3.10.12` module to be loaded.
* (dennis) set up Nextflow to copy test dirs to Nextflow hash'd working directory.  (DONE (in pull request))
* (brian) Email Mike and Aaron about the `rcstest` account with its `rcstest` project. (DONE.)
  * we'll make an rcstest project but no special user account.
2. rcstest project needs to be created & Apps team members added to it (brian).
3. newpkg updates: add SCC_MODNAME_BASE, remove SCC_MODNAME_TEST & SCC_MODNAME_TESTDOC, don't touch SCC_MODNAME_DIR.
4. Try the Nextflow pipeline on everything in /share/pkg.8 (dennis)
* How long does it take to run? (tests run as concurrent separate jobs)
* The total size of all test directories in /share/pkg.8 is ~15.5GB at present.
5. Check with Charlie about the newpkg script - how much work would it be to insert a newpkg version number into the generated files (notes.txt, modulefile.lua, test.qsub)? Let's see how hard that is before deciding whether or not to do this. (dennis)

## February 27, 2024
1. TODO from last time:
*  (brian) find_qsub.py takes an argument to check all /share/pkg.8 modules/   (not done yet)
*  newpkg is now 0.2.0
2. Question from Katia:
Could you clarify how the “automatic testing” is going to do its task?
Say, I have a regular case: the test directory contains:
-	test.qsub
-	input_file
-	output_expected_file

Where will this test run? Is it going to submitted from its original directory? In this case it will most likely fail due to permissions. Is it going to be copied to $TMPDIR? In this case those tests that copy their files to $TMDIR might fail. Is it going to be copied somewhere else?

* Nextflow runs test.qsub from its own directory, i.e. like: `(pwd is /path/to/nextflow) qsub /share/pkg.8/xyz/1.0/test/test.qsub`  The documentation says to accommodate that (`cp $SCC_XYZ_DIR/../test/input.txt $TMPDIR`). Dennis says Nextflow can be configured to copy the test directory to the Nextflow hash'd working directory so test.qsub gets executed locally. This makes any older test.qsub that expect to read from its own directory work. 

3. (brian) Unpublish older newpkg?  There's no reason to ever use the old ones. They're still runnable directly from their /share/pkg.X directories if needed.  Consensus - yes.  Done.
4. (dennis) newpkg should be more structured and controlled in its releases.
* notes in the newpkg github should be added for releases and announcements made to the Apps team & interns when a new version is released.
5. (dennis) Potential new reporting approach. https://github.com/bu-rcs/PkgAutoTest/pull/10  
* Looks great! The new csv file is very customizable to hold the metrics from each test.qsub.
* Brian requests 3 new columns:   host that ran the test ($HOSTNAME), elapsed time for the test, and OS version.
  OS version needs to be OS-agnostic (i.e. what if we test on Debian?) https://www.redswitches.com/blog/check-linux-version/ 
6. TODO:
* (brian) find_qsub.py takes an argument to check all /share/pkg.8 modules
* (dennis) set up Nextflow to copy test dirs to Nextflow hash'd working directory. 
* (brian) Email Mike and Aaron about the `rcstest` account with its `rcstest` project.

## February 6, 2024
1. TO from last meeting:
* (brian) find_qsub.py - updated CSV output (done)
* (yun) - newpkg updated to 0.1.9. Changes applied.
* (dennis) - stdout/stderr in nextflow, new csv format. Progress made, Dennis will demo.
2. Intern meeting on 2/2 (brian)
  * Documentation needs to be provided to them.
  * use Yun's new test.qsub format with guidelines.
  * Need to look at tutorials, documentation, etc. to get test inputs/outputs, maybe with a time limit of 1 hour of work, if this fails then kick it over to RCS apps team.
  * Consider the software install log - ones with shorter install times seem likely to be easier to test.
3. What is the minimum we need to check for software to make sure it works on a new OS/CPU/etc.?
  * Every module is a special case! The test writer must know what the software does and what it produces. We will frequently rely on users to help us with this. 
  * Did it run? ( check shell error code ) - mininum test, did it run?
    * This catches library errors, SIMD errors, PATH errors, missing input or config file errors.
  * Then do some more simple sanity check:
    * Compare output file to a previously generated reference output file?
    * Check for words in the output file like "success!"
    * do file size checks, etc. as needed to feel assured the software ran correctly.
  * For libraries - do a test program compile with whatever compiler built the module.
    * no need to check that the compiler worked ok, just run the test program.
 4. TODO:
   * (brian) find_qsub.py takes an argument to check all /share/pkg.8 modules/
   * Run current nextflow on whatever is available in /share/pkg.8

     
  

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
