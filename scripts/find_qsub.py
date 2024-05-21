#!/bin/env python3

# Prototype of a script that finds test.qsub files.
# This uses the "module avail" function to find files to test.

# The output is a CSV file with this information:
# Info like module_installer and module_install_date are extracted from the notes.txt file.
# module_name, version, module_name_version,module_pkg_dir, module_installer,module_install_date,module_category,module_prereqs, test_path,qsub_options
# openmpi,4.1.5,openmpi/4.1.5,/share/pkg.8,bgregor,06/27/23,libraries,prereqs;go;here,/share/pkg.8/openmpi/4.1.5/test/test.qsub,-P scv


# Run example:
#    Load a python module:
#    module load python3/3.10.12
#    python find_qsub.py -m openmpi out3.csv
#    python find_qsub.py -d /share/pkg.8 out2.csv



# TODO: make it work to find R code and other special cases
# TODO: Add installer username to the csv file - process the notes.txt file.

# TODO: Implement a class that produces all of the required info
#       for a module.

import argparse
import subprocess
import os
import sys
import csv
import glob 
import pprint 
import functools

# TODO: print output using logging module.
import logging
    
    

#%%

@functools.total_ordering
class SccModule():
    # List of the column headers, in the output order.
    HEADERS=['module_name','version','module_name_version','module_pkg_dir',
             'module_installer','module_install_date','module_category',
             'module_prereqs','test_path','qsub_options']
    # If the column headers change, make sure to update to_csv_rows()
    
    ''' Load all the info needed for a module '''
    def __init__(self, name_version):
        ''' module_name_version -string  of the form modname/version 
            modulefile_path - path to the modulefile '''
        self.name_version = name_version

        # validate the argument.
        tmp = name_version.split('/')
        if len(tmp) != 2:
            raise Exception(f'argument not of the form modname/version:  {name_version}')
        self.name, self.version = tmp

        mod_path, self.pkg_dir, self.category, self.prereqs = self.get_module_info()
    
        self.installer, self.install_date = self.parse_notes_txt(mod_path)         

        # test_path is the path to the qsub file. This is a dictionary because
        # multiple test.qsub files might exist.  test.qsub, test.mpi.qsub
        # The test.*.qsub paths are the keys, the values are the qsub options
        # for each.
        self.tests = self.get_test_qsub_info(mod_path)

    def __lt__(self, other):
        ''' Less than - used for sorting. Compare the name_version'''
        return self.name_version < other.name_version

    def get_test_qsub_info(self, mod_path):
        ''' Find all files called test.qsub or test.*.qsub
            extract qsub options. Return a dictionary of the 
            full test.*.qsub path with the qsub_options as values.'''
        test_dir = os.path.join(mod_path,'test')
        testqsubs = glob.glob(os.path.join(test_dir,'test.qsub')) + \
                    glob.glob(os.path.join(test_dir,'test.*.qsub'))
        tests = {}
        for tq in testqsubs:
            tests[tq] = self.extract_qsub_opts(tq)
        return tests                
        

    def get_module_info(self):
        ''' Run "module show" on the module and parse out the
            SCC_MODNAME_DIR variable.
            
            Return the pkg_path ('/share/pkg.8') and the
            module base dir ('/share/pkg.8/foo/1.0') '''
        cmd = f'module show {self.name_version} |& xargs -0  echo'     
        result = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE)
        mod_show_txt = result.stdout.decode("utf-8").split('\n')
        
        # Filter mod_show_txt for SCC_{cap_name}_DIR. Replace any hyphens
        # with underscores
        cap_name = self.name.upper().replace('-','_')
        scc_lines = filter(lambda x: x.find(f'SCC_{cap_name}_DIR')>=0, mod_show_txt)
        # Find the line that starts with setenv
        # Get the module directory
        mod_path = None
        for line in scc_lines:
            if line.find('setenv') >= 0:
                # Sample string: setenv("SCC_OPENMPI_DIR","/share/pkg.8/openmpi/4.1.5/install")
                # and strings in Lua can use double or single quotes. Let's split this up
                # by commas and then by the close parentheses
                tmp = line.split(',')[-1] # '"/share/pkg.8/openmpi/4.1.5/install")'
                tmp = tmp.split(')')[0] # /share/pkg.8/openmpi/4.1.5/install" or '/share/pkg.8/openmpi/4.1.5/install'
                mod_path = tmp.replace('"','').replace("'","")
                break # all done!
        if not mod_path:
            raise Exception(f'SCC_{cap_name}_DIR variable could not be determined for {self.name_version}')
        # pass mod_path off to get_module_base_dir() to get it in the correct format along
        # with the pkg_path.
        
        whatis_lines = list(filter(lambda x: x.find('whatis') >=0, mod_show_txt))         
        mod_cat = ''
        for line in whatis_lines:
            if line.find('whatis("Categories:') >= 0:
                # This looks like:   whatis("Categories:   programming")
                # replace any single quotes in the line with double quotes
                # to make the split reliable
                line = line.replace("'",'"')
                mod_cat = line.split(':')[1].strip().split('"')[0]
                break
        # Get prereqs, if any.
        prereq_lines = filter(lambda x: x.find('prereq') >=0, mod_show_txt)
        mod_prereqs=[]
        for line in prereq_lines:
            # Looking for lines like:  prereq("openmpi/4.1.5_gnu-12.2.0")
            # ***TODO:  Handle the rare prereq_any cases
            if line.find('prereq(') >= 0:
                line = line.replace("'",'"')
                mod_prereqs.append(line.split('"')[1])
        mod_prereqs = ';'.join(mod_prereqs)
        mod_path, pkg_dir = self._get_module_base_dir(mod_path)
        return  mod_path, pkg_dir, mod_cat, mod_prereqs

    def _get_module_base_dir(self, mod_path):
        ''' Get the module path from the SCC_MODNAME_DIR directory 
            Also return the pkg path, i.e. /share/pkg.8 '''
        mod_path = mod_path.strip()
        # If mod_path contains install, remove it. Usually this is
        # /share/pkg.8/openmpi/4.1.5/install
        # but sometimes it's /share/pkg.8/berkeleygw/3.1.0/install/berkeleygw
        # This works for all cases.
        mod_path = mod_path.split('/install')[0]
        # mod_path is now like  '/share/pkg.8/foo/1.0'
        # so extract the dirname twice to get the /share/pkg.X path or
        # other pkg install path.
        pkg_path = os.path.dirname(os.path.dirname(mod_path))
        return mod_path, pkg_path
    
    def extract_qsub_opts(self, qsub_file, ignore_flags=['-j', '-P', '-N']):
        ''' Extract all qsub parameters from the .qsub file. Ignore
            flags in the list ignore_flags '''
        with open(qsub_file) as f:
            qsub_cmds=[]
            for line in f:
                # if it starts with #$ it's a qsub command.
                if line.startswith('#$'):
                    qsub_cmds.append(line.split('$')[1].strip())

            def startswith(elem):
                has_no_flags = False
                for f in ignore_flags:
                    has_no_flags = has_no_flags or elem.startswith(f)
                return not has_no_flags 
            
            qsub_cmds = filter(startswith,qsub_cmds)
            # Join the qsub commands into one line and return.
            return ' '.join(qsub_cmds)
    
    def parse_notes_txt(self, mod_path):
        ''' Parse a notes.txt file and retrieve the name of the person
        who installed the module and the date the notes.txt file was
        created. 
        
        mod_path: directory path to the module, i.e. /share/pkg.8/openmpi/4.1.5
        returns:  'module_installer','module_install_date' '''
        mod_installer = 'unknown'
        mod_install_date = 'unknown'
        notes_txt = os.path.join(mod_path,'notes.txt')
        if not os.path.isfile(notes_txt):
            # Do we want to raise an exception here?
            # Or print/log error
            #raise f'{notes_txt} not found'
            sys.stderr.write(f'{notes_txt} not found for {self.name_version}\n')
            return mod_installer, mod_install_date

        with open(notes_txt) as f:
            # Looking for these lines:
            # INSTALLER: bgregor
            # INSTALLED: 12/20/23
            for line in f:
                if line.find('INSTALLER') >= 0:
                    mod_installer = line.split(':')[1].strip()
                if line.find('INSTALLED') >= 0:
                    mod_install_date= line.split(':')[1].strip()
                if mod_installer != 'unknown' and mod_install_date != 'unknown':
                    break
        return mod_installer, mod_install_date
    
    def __str__(self):
        ''' Print a copy of this as a string '''
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(vars(self))
        
    def to_csv_rows(self):
        ''' Return a list of CSV formatted rows in the proper header order.'''
        # List of the column headers, in the output order.
        rows = []
        # One row per entry in the self.tests dictionary.
        for test in self.tests:
            # Put the entries into a dictionary using the headers as keys.
            # Then extract in the HEADERS order and format a string.
            # If the headers change, make sure to update this.
            rd = {'module_name': self.name,
                  'version':self.version,
                  'module_name_version':self.name_version,
                  'module_pkg_dir':self.pkg_dir,
                  'module_installer':self.installer,
                  'module_install_date':self.install_date,
                  'module_category':self.category,
                  'module_prereqs':self.prereqs,
                  'test_path':test,
                  'qsub_options':self.tests[test]}
            # Convert to a list in the HEADERS order
            row = []
            for head in SccModule.HEADERS:
                row.append(rd[head])
            # Format to a string and store
            row = ','.join(row)
            rows.append(row)
        return rows
           
    
#%%    
def get_modules_from_dir(directory, pkg_path=None, exclude_dirs=['test','rcstools'], only_module_name=None):
    ''' From a directory of publichsed modules (like /share/module.8), search down to find all module/version pairs.
        Find symlinks and use them to build modname/version strings, as this is how they are published.
        
        Note that .lua links are the ones we want, ignore any .tcl links at the moment.
        
        This works in private module installs too.
        
        pkg_path is an optional filter to only see links in a particular pkg install directory
        like '/share/pkg.8
        
        only_module_name (a list) is a filter that returns only modules with that name.
    '''
    modules = []
    
    # Remove any entries in only_module_name with a / as those refer to specific
    # modules.
    specific_modules = []
    if only_module_name:
        incoming = only_module_name.copy()
        only_module_name = []
        for i  in  incoming:
            if i.find('/') >= 0:
                specific_modules.append(i)
                # Also add the module name to the other list.
                only_module_name.append(i.split('/')[0])
            else:
                only_module_name.append(i)

    # Recursively search for symlinks to lua modulefiles.
    for info in os.walk(directory):
        # info is a tuple like:  ('/share/module.8/chemistry/berkeleygw', [], ['3.1.0.lua', '2.1.lua'])        
        # If pkg_path is provided, remove this if the symlink is not to that pkg_path
        if pkg_path:
            filt_info2 = []
            for f in info[2]:
                fpath = os.path.join(info[0],f)
                if os.path.islink(fpath):
                    rpath = os.path.realpath(fpath)
                    if os.path.commonpath([pkg_path,rpath]) == pkg_path:
                        filt_info2.append(f)
            # Replace the info[2] list with the filtered links
            info = (info[0], info[1], filt_info2)
        # If the exclude_dirs have shown up, skip this one and carry on.
        skip = False
        for ex in exclude_dirs:
            if info[0].find('/'+ex) >= 0:
                skip = True
        if skip:
            continue
                
        mod_name = os.path.basename(info[0])
        # If only_module_name is provided, only keep if one of the elements in only_module_name is found.
        if only_module_name:    
            if mod_name not in only_module_name:
                continue
        # Filter the versions down to ones ending in .lua
        versions = filter(lambda x: os.path.splitext(x)[1]=='.lua', info[2])
        # Remove any versions here that is not a symlink.
        versions = filter(lambda x: os.path.islink(os.path.join(info[0],x)), versions)
        # and now from the lua files get the version number
        versions = map(lambda x: os.path.splitext(x)[0], versions)
        # and for each version join it to the mod_name and store
        modules.extend((mod_name + '/' + x for x in versions))
    
    # By virtue of these being found in the published modules directory they are
    # assumed to be published!  Return the list of modname/version strings.
    
    # If specific module versions were requested, make sure only those are here
    # so if gcc/13.2.0,python3 was requested all gcc ones would have been found,
    # now remove any gcc mod_name/version that is not gcc/13.2.0
    remove_modules = []
    for specific in specific_modules:
        smod, sver = specific.split('/')
        for m in modules:
            mod,ver = m.split('/')
            if smod == mod:
                # module name matched
                # does the version match?
                if not sver == ver:
                    remove_modules.append(m)
    # now prune the modules list:
    modules = [m for m in modules if m not in remove_modules]
    return modules 
#%%

def save_csv(test_list, out_csv):
    ''' Save the CSV file. '''
    if not test_list:
        raise Exception('save_csv(): test_list is empty!\n')

    with open(out_csv, 'w') as csvfile:
        print(f'Writing {out_csv}')
        sys.stdout.flush()
        # Write the header row
        header = ','.join(SccModule.HEADERS)
        nl = os.linesep
        csvfile.write(f'{header}{nl}')
        for test in test_list:
            for row in test.to_csv_rows():
                csvfile.write(f'{row}{nl}')
                
        
#%%

class SplitArgs(argparse.Action):
    ''' This is used to process comma-separated values in argparse.'''
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [x.strip() for x in values.split(',')])

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Find test.qsub files")
    parser.add_argument("-m","--mod",dest="mod_name", help="Comma-separated names of specific module(s) to test.", default=None, action=SplitArgs)
    parser.add_argument("-d","--dir", dest="directory", 
                        help="Module publication directory to search for modules to test. This will find all available modules in that directory. Default is /share/module.8",
                        default="/share/module.8")
    parser.add_argument("-p","--pkg", dest="pkg_path", default = '/share/pkg.8', help="Limit tests to a particular /share/pkg directory. Defaults to /share/pkg.8. Use ALL for modules found in any directory.")
    parser.add_argument("--err", dest='err_file', default="errors.log", help='File to write errors to. Defaults to errors.log. If there are no errors this file is not created.')
    parser.add_argument("out_csv",help="output CSV file for use with Nextflow pipeline.")
    
    args = parser.parse_args()

    if (not args.mod_name and not args.directory):
        parser.print_help(sys.stderr)
        exit(1)

    if args.pkg_path == 'ALL':
        args.pkg_path = None
    
    mod_names = []
    if args.directory:
        mod_names = get_modules_from_dir(args.directory, pkg_path=args.pkg_path, only_module_name=args.mod_name)
    
    if not mod_names:
        print('No modules were found. Double check the module search directory.')
    
    # From the list of modulename/version strings, build a list of SccModule objects
    # with all of the test info.
    test_list = []
    print('Loading module test info.')
    found_error = False
    err_file = args.err_file
    with open(err_file,'w') as erf:
        for mn in mod_names:
            try: 
                test_list.append(SccModule(mn))
            except Exception as e:
                erf.write(f'{e}{os.linesep}')
                found_error = True
    # No errors found, delete the error file
    if not found_error:
        os.unlink(err_file)
    else:
        print(f'Errors found, check {err_file} for details.')
        print(os.linesep)        
                
    # Sort the SccModule objects by name/version
    test_list.sort()
        
    # Save the output CSV file.
    save_csv(test_list, args.out_csv)
    
