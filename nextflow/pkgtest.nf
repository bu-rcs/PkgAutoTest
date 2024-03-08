
params.csv_input = "" // Path to CSV File produces by find_qsub.py script
params.executor = 'sge'  // Set the executor as 'sge' by default but can be changed via arguments
params.errorStrategy = 'ignore' // "ignore"- will continue with other tests if there is an error
			    // "terminate" - kill all tests when error is encountered
params.qsub_path = ""
params.project = ""  // Value to be used for the -P directive for qsub

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

    ## PREP
    TEST_RESULT=FAILED
    TEST_DIR=`dirname $test_path`
    QSUB_FILE=`basename $test_path`
    WORKDIR=`pwd`

    echo TEST_DIR=\$TEST_DIR
    echo QSUB_FILE=\$QSUB_FILE
    
    ## COPY TEST DIRECTORY INTO workDIR
    cp -r \$TEST_DIR .
    cd \$TEST_DIR
    echo $NSLOTS $QUEUE
    echo     

    ## RUN MODULE TEST
    echo \$QSUB_FILE >> \$WORKDIR/log.txt
    EXIT_CODE=`bash \$QSUB_FILE \$WORKDIR/log.txt >  \$WORKDIR/results.txt; echo \$?`

    ## POST PROCESSING
    cd \$WORKDIR

    PASSED=`grep -iow 'Passed' results.txt | wc -l`
    FAILED=`grep -iow 'Error' results.txt | wc -l`
    LOG_ERRORS=`grep -iow 'error' log.txt | wc -l`

    # Test result fails if words other than "Passed" are found in 
    # results.txt
    if [ "\$(grep -c -v Passed results.txt)" -eq 0 ] && [ \$EXIT_CODE -eq 0 ]
    then
       TEST_RESULT=PASSED  
    fi 


    # Write the test result metrics to a csv file
    cat > test_metrics.csv << EOF
    results,module, tests_passed, tests_failed, log_error_count, exit_code, installer, category, install_date,  workdir
    \$TEST_RESULT, $module_name_version, \$PASSED, \$FAILED, \$LOG_ERRORS, \$EXIT_CODE, $module_installer, $module_category, $module_install_date,  \$PWD
    EOF

    """
}




