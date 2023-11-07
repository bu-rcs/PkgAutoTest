# Notes from the project meetings

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
