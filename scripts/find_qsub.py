#!/bin/env python3

# Prototype of a script that finds test.qsub files.
# This uses the "module avail" function to find files to test.

# The output is a CSV file with this information:
# Info like module_installer and module_install_date are extracted from the notes.txt file.
# module_name, version, module_name_version,module_pkg_dir, module_installer,module_install_date,module_category,module_prereqs, test_path,qsub_options
# openmpi,4.1.5,openmpi/4.1.5,/share/pkg.8,bgregor,06/27/23,libraries,prereqs;go;here,/share/pkg.8/openmpi/4.1.5/test/test.qsub,-P scv



# TODO: make it work to find R code and other special cases
# TODO: Add installer username to the csv file - process the notes.txt file.

# TODO: Implement a class that produces all of the required info
#       for a module.

import argparse
import subprocess
import os
import sys
import csv


# TODO: print output using logging module.
import logging


# List of the column headers, in the output order.
HEADERS=['module_name','version','module_name_version','module_pkg_dir',
         'module_installer','module_install_date','module_category',
         'module_prereqs','test_path','qsub_options']

def extract_qsub_opts(qsub_filename):
    ''' Extract all qsub parameters from the .qsub file '''
    with open(qsub_filename) as f:
        qsubs=[]
        for line in f:
            # if it starts with #$ it's a qsub command.
            if line.startswith('#$'):
                qsubs.append(line.split('$')[1].strip())
        # Remove the "-j y" flag if found.
        qsubs = filter(lambda x: not x.startswith('-j'),qsubs)
        # Join the qsub commands into one line and return.
        return ' '.join(qsubs)
    

def call_module_avail(mod_name):
    ''' call module avail on the mod_name to see what's been published '''
    cmd = f'module -t avail {mod_name}'     
    result = subprocess.run([cmd], shell=True, stderr=subprocess.PIPE)
    stderr = result.stderr.decode("utf-8")
    # For, say, openmpi, stderr is a string like:
    # '/share/module.8/chemistry:\ngromacs/2019.1_openmpi_3.1.4\nnamd/2.13_openmpi\n/share/module.8/libraries:\nopenmpi/2.0.2\nopenmpi/3.1.1_intel-2018\nopenmpi/3.1.1\nopenmpi/3.1.4_gnu-7.4.0\nopenmpi/3.1.4_gnu-8.1
    # so split on newlines, and then look for anything starting with mod_name.
    # this will work even if mod_name has a specified version.
    mods = []
    for mn in stderr.split('\n'):
        if mn.find(mod_name) == 0:
            mods.append(mn.strip())
    return mods

def get_module_base_dir(mod_path):
    ''' Get the module path from the SCC_MODNAME_DIR directory 
        Also return the pkg path, i.e. /share/pkg.8 '''
    mod_path = mod_path.strip()
    # If mod_path ends in /install, remove it.
    index = mod_path.rfind("/install")
    if index >= 0:
        mod_path = os.path.dirname(mod_path)
    # mod_path = '/share/pkg.8/foo/1.0'
    pkg_path = os.path.dirname(os.path.dirname(mod_path))
    return mod_path, pkg_path


def parse_notes_txt(mod_path):
    ''' Parse a notes.txt file and retrieve the name of the person
    who installed the module and the date the notes.txt file was
    created. 
    
    mod_path: directory path to the module, i.e. /share/pkg.8/openmpi/4.1.5
    returns:  'module_installer','module_install_date' '''
    mod_installer = ''
    mod_install_date = ''
    notes_txt = os.path.join(mod_path,'notes.txt')
    if not os.path.isfile(notes_txt):
        # Do we want to raise an exception here?
        # Or print/log error
        #raise f'{notes_txt} not found'
        sys.stderr.print(f'{notes_txt} not found\n')
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
            if len(mod_installer) > 0 and len(mod_install_date) > 0:
                break
    return mod_installer, mod_install_date
    

def find_test_qsub_params(mod_names):
    ''' For every module that's been found find its path based on $SCC_MODNAME_DIR.'''
    # "module show" is preferred over module load because it doesn't require
    # the loading of prereqs.  The downside is parsing the setenv line.
    #
    # TODO:  This is super long. Break down into sub-functions.
    #
    test_list = []
    for mn in mod_names:
        cap_name = mn.split('/')[0].upper()
        cmd = f'module show {mn} |& xargs -0  echo'     
        result = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE)
        mod_show_txt = result.stdout.decode("utf-8").split('\n')
        
        # Filter stdout for SCC_{cap_name}_DIR.
        scc_lines = filter(lambda x: x.find(f'SCC_{cap_name}_DIR')>=0, mod_show_txt)
        # Find the line that starts with setenv
        # Get the module directory
        for line in scc_lines:
            if line.find('setenv') >= 0:
                # Sample string: setenv("SCC_OPENMPI_DIR","/share/pkg.8/openmpi/4.1.5/install")
                # split on " then it's the 4th element.
                mod_path = line.split('"')[3].strip()
                break # all done!
        mod_path, pkg_path = get_module_base_dir(mod_path)
        # Then, look for a test/test.qsub. If this isn't found
        # there's no need to keep extracting parameters.
        test_path = os.path.join(mod_path,'test','test.qsub')
        if os.path.isfile(test_path):
            qsub_opts = extract_qsub_opts(test_path)
            # Get the notes.txt info
            mod_installer, mod_install_date = parse_notes_txt(mod_path)
            # Get the module category. Look for the
            # whatis lines.
            whatis_lines = list(filter(lambda x: x.find(f'whatis') >=0, mod_show_txt))         
            mod_cat = ''
            for line in whatis_lines:
                if line.find('whatis("Categories:') >= 0:
                    # This looks like:   whatis("Categories:   programming")
                    mod_cat = line.split(':')[1].strip().split('"')[0]
                    break
            # Get prereqs, if any.
            prereq_lines = filter(lambda x: x.find(f'prereq') >=0, mod_show_txt)
            mod_prereqs=[]
            for line in prereq_lines:
                # Looking for lines like:  prereq("openmpi/4.1.5_gnu-12.2.0")
                # ***TODO:  Handle the rare prereq_any cases
                if line.find('prereq(') >= 0:
                    mod_prereqs.append(line.split('"')[1])
            mod_prereqs = ';'.join(mod_prereqs)
        
            # Build an output dictionary for this row of the eventual CSV file.
            # To be used with the csv.DictWriter:  
            #   https://docs.python.org/3/library/csv.html#csv.DictWriter
            row = {'module_name':mn.split('/')[0],
                   'version':mn.split('/')[1],
                   'module_name_version':mn,
                   'module_pkg_dir':mod_path,
                   'module_installer':mod_installer,
                   'module_install_date':mod_install_date,
                   'module_category':mod_cat,
                   'module_prereqs':mod_prereqs,
                   'test_path':test_path,
                   'qsub_options':qsub_opts}
            test_list.append(row)
    return test_list

def save_csv(test_list, out_csv):
    ''' Save the CSV using a Python DictWriter'''
    if not test_list:
        sys.stderr.write('save_csv(): test_list is empty!\n')
        exit(-1)
    with open(out_csv, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS, dialect='unix')
        # This writes the header row
        writer.writeheader()
        # Now loop and write out each row. Each row is a dictionary whose
        # keys match the headers.
        for row in test_list:
            writer.writerow(row)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Find test.qsub files")
    parser.add_argument("mod_name") 
    parser.add_argument("out_csv")
    
    args = parser.parse_args()
    
    mod_names = call_module_avail(args.mod_name)
    test_list = find_test_qsub_params(mod_names)
    
    save_csv(test_list, args.out_csv)
    
