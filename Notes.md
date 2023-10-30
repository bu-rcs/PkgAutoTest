# Notes from the project meetings

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
