#!/bin/bash -l

# Monthly crontab entry looks like:

#  0 0 1 * * 
# That's midnight on day 1 of each month.  


cd /projectnb/rcstest/cronjobs

module use /share/module.8/rcstools

# use the default versions.
module load nextflow pkgautotest 

# Timestamped run directory
RUN_DIR=$(date +"%Y_%m_%d_%H_%M")

mkdir $RUN_DIR
cd $RUN_DIR

# Submit the testing job
qsub $SCC_PKGAUTOTEST_DIR/PkgAutoTest/scripts/pkgauto_email.qsub

# and done!
