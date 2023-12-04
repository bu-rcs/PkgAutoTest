#!/bin/python3

# Prototype of a script that finds test.qsub files.
# This uses the "module avail" function to find files to test.

# The output is a CSV file with this information:
# module_name,module_version,module_name/version,path_to_test.qsub

# TODO: make it work to find R code and other special cases


import argparse
import subprocess
import os


def call_module_avail(mod_name):
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
    mod_path = mod_path.strip()
    # If mod_path ends in /install, remove it.
    # TODO: Properly do this using os.path, duh.
    index = mod_path.rfind("/install")
    if index >= 0:
        mod_path = os.path.dirname(mod_path)
    return mod_path
    
def find_test_qsub(mod_names):
    # For every module that's been found, load it and find 
    # its path based on $SCC_MODNAME_DIR. 
    
    # TODO: account for module prereqs and load those too
    test_list = []
    for mn in mod_names:
        cap_name = mn.split('/')[0].upper()
        # Loading the module should be replaced by a recursive function call that loads
        # required modules until everything loads successfully. 
        cmd = f'module load {mn} ; echo $SCC_{cap_name}_DIR'     
        result = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8")
        # TODO: FIX THIS SKIP OF ERROR CASES
        if stderr.find('ERROR') >= 0:
            continue
        # otherwise get the module base path
        mod_path = get_module_base_dir(stdout)
        # Then, look for a test/test.qsub.
        test_path = os.path.join(mod_path,'test','test.qsub')
        if os.path.isfile(test_path):
            row = f"{mn.split('/')[0]},{mn.split('/')[1]},{mn},{test_path}{os.linesep}"
            test_list.append(row)
    return test_list

def save_csv(test_list, out_csv):
    with open(out_csv,'w') as f:
        f.write("module_name,module_name_version,test_path" + os.linesep)
        for tl in test_list:
            f.write(tl)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Find test.qsub files")
    parser.add_argument("mod_name") 
    parser.add_argument("out_csv")
    
    args = parser.parse_args()
    
    mod_names = call_module_avail(args.mod_name)
    test_list = find_test_qsub(mod_names)
    
    save_csv(test_list, args.out_csv)
    
