
params.csv_input = "" // Path to CSV File produces by find_qsub.py script
params.executor = 'sge'  // Set the executor as 'sge' by default but can be changed via arguments
params.errorStrategy = 'ignore' // "ignore"- will continue with other tests if there is an error
			    // "terminate" - kill all tests when error is encountered
params.qsub_path = ""
params.project = "rcstest"  // Value to be used for the -P directive for qsub

nextflow.enable.dsl=2


workflow {

    // Load the csv file and split the rows into tuples.
    // Then execute runTests process
    Channel.fromPath(params.csv_input, checkIfExists: true, type:'file') \
        | splitCsv(header:true) \
        | map { row-> tuple(row.module_name, row.version, row.module_name_version, row.module_pkg_dir, row.module_installer, row.module_install_date, row.module_category, row.module_prereqs , row.test_path, row.qsub_options) } \
        | runTests \
        | collectFile(keepHeader:true, storeDir:'.', name: "report_" +params.csv_input) | view

}


process runTests {

    beforeScript 'source $HOME/.bashrc' // To make module command available.
    clusterOptions "-P ${params.project} -N nf_${module_name}_${version} ${qsub_options}" // Specify qsub options from CSV file
    executor params.executor
    errorStrategy params.errorStrategy  
    tag "$module_name_version" // Used for reporting.
    

    input:
    tuple val(module_name), val(version), val(module_name_version), val(module_pkg_dir), val(module_installer), val(module_install_date), val(module_category), val( module_prereqs ), val(test_path), val(qsub_options)

    output:
    path 'test_metrics.csv'
     
    script:
    """

    ## INITIALIZE ENVIRONMENT VARIABLES
    TEST_RESULT=FAILED                  # INITIATE AS FAILED. UPDATED WHEN TEST IS PASSED
    TEST_DIR=`dirname $test_path`       # PATH TO THE TEST DIRECTORY FROM INPUT CSV
    QSUB_FILE=`basename $test_path`     # PATH TO QSUB FILE FROM INPUT CSV
    WORKDIR=`pwd`                       # THE BASE WORKING DIRECTORY FOR THIS PROCESS
    LOG=\$WORKDIR/log.txt               # LOG FILE USED FOR QSUB ARGUMENT
    RESULTS=\$WORKDIR/results.txt       # TEXT FILE WHERE RESULTS OF A TEST ARE STORED.
    
    ## COPY TEST DIRECTORY INTO WORK DIRECTORY 
    cp -r \$TEST_DIR \$WORKDIR

    # CD INTO TEST DIRECTORY
    cd `basename \$TEST_DIR`

    ## PRINT ENVIRONMENT VARIABLES ASSOCIATED WITH THE TEST
    echo MODULE=$module_name_version
    echo NSLOTS=\$NSLOTS 
    echo QUEUE=\$QUEUE
    echo HOSTNAME=\$HOSTNAME
    echo JOB_ID=\$JOB_ID
    echo TEST_DIR=\$TEST_DIR
    echo QSUB_FILE=\$QSUB_FILE
    echo LOG=\$LOG
    echo RESULTS=\$RESULTS
    echo WORKDIR=\$WORKDIR
    echo USER=\$USER

    ## APPEND XVFB KILL COMMAND TO QSUB FILE (see issue #18 https://github.com/bu-rcs/PkgAutoTest/issues/18)
    echo '\n#### CODE BLOCK INSERTED BY NEXTFLOW ####' >> \$QSUB_FILE
    echo '#### see issue #18 https://github.com/bu-rcs/PkgAutoTest/issues/18' >> \$QSUB_FILE
    echo 'pgrep -P \$\$ -f Xvfb | while read line ; do kill -9 \$line; done' >> \$QSUB_FILE
    echo '#########################################' >> \$QSUB_FILE

    ## RUN MODULE TEST
    EXIT_CODE=`bash \$QSUB_FILE \$LOG >  \$RESULTS; echo \$?`

    ## POST PROCESSING
    cd \$WORKDIR

    # GET COUNT OF 'Passed' KEYWORD IN THE results.txt
    PASSED=`grep -iow 'Passed' results.txt | wc -l`

    # GET COUNT OF 'Error' KEYWORD IN THE results.txt
    FAILED=`grep -iow 'Error' results.txt | wc -l`

    # GET COUNT OF 'error' KEYWORD IN THE log.txt
    LOG_ERRORS=`grep -iow 'error' log.txt | wc -l`

    # THE TEST PASSES IF ONLY WORDS "Passed" ARE FOUND
    # IN results.txt AND THE \$EXIT_CODE IS 0
    if [ "\$(grep -c Passed results.txt)" -gt 0 ] && [ "\$(grep -c -v Passed results.txt)" -eq 0 ] && [ \$EXIT_CODE -eq 0 ]
    then
       TEST_RESULT=PASSED  
    fi 


    # WRITE THE TEST RESULT INFORMATION TO A CSV FILE
cat > test_metrics.csv << EOF
job_number, hostname, test_result,module, tests_passed, tests_failed, log_error_count, exit_code, installer, category, install_date,  workdir
\$JOB_ID, \$HOSTNAME, \$TEST_RESULT, $module_name_version, \$PASSED, \$FAILED, \$LOG_ERRORS, \$EXIT_CODE, $module_installer, $module_category, $module_install_date, \$PWD
EOF

    """
}




