
params.csv_input = "" // Path to CSV File produces by find_qsub.py script
params.executor = 'sge'  // Set the executor as 'sge' by default but can be changed via arguments
params.errorStrategy = 'ignore' // "ignore"- will continue with other tests if there is an error
			    // "terminate" - kill all tests when error is encountered
params.qsub_path = ""
params.project = "rcstest"  // Value to be used for the -P directive for qsub
params.keep_passed = "true" // If true, the passed tests will be kept in the output directory
params.test_results_dir = ""     // Directory where the per-test result files are published.
                            // Defaults to test_results_<csv_input basename>

nextflow.enable.dsl=2

// NOTE: These are assigned WITHOUT 'def' on purpose so that they are visible
// inside the process directives and the workflow.onComplete handler.
csv_base = params.csv_input ? file(params.csv_input).getName().replaceFirst(/\.csv$/, '') : "input"
test_results_dir = params.test_results_dir ? params.test_results_dir : "test_results_${csv_base}"
report_file = "report_${csv_base}.csv"

// THE REPORT'S COLUMNS, DEFINED ONCE HERE: report column name -> the shell
// variable holding its value in the runTests script.  The header line and the
// value line of every per-test result file are both generated from this map,
// so they cannot drift apart, and the header is passed to collect_report.py in
// the onComplete handler.  To add a column, add an entry here and set that
// variable in the script below.  Order is preserved and is the column order.
//
// The values are literal shell text, not Nextflow variables: the per-row
// values from the input CSV are assigned to shell variables at the top of the
// script so that everything in this map is resolved by bash at run time.
report_columns = [
    'job_number'     : '$JOB_ID',
    'hostname'       : '$HOSTNAME',
    'qsub_file'      : '$QSUB_FILE',
    'test_result'    : '$TEST_RESULT',
    'module'         : '$MODULE',
    'tests_passed'   : '$PASSED',
    'tests_failed'   : '$FAILED',
    'log_error_count': '$LOG_ERRORS',
    'exit_code'      : '$EXIT_CODE',
    'installer'      : '$INSTALLER',
    'category'       : '$CATEGORY',
    'install_date'   : '$INSTALL_DATE',
    'workdir'        : '$WORKDIR',
    'test_path'      : '$TEST_PATH',
]
report_header = report_columns.keySet().join(', ')
report_values = report_columns.values().join(', ')


workflow {

    // Load the csv file and split the rows into tuples.
    // Then execute runTests process.  Each test publishes its own single-row
    // CSV into test_results_dir as it completes; the rows are concatenated into
    // report_file by collect_report.py in the onComplete handler below.
    // We deliberately do NOT use collectFile() here: it is a terminal barrier
    // that never fires if a task dies without emitting its output file, which
    // would hang the whole pipeline (see also issue #18).
    Channel.fromPath(params.csv_input, checkIfExists: true, type:'file') \
        | splitCsv(header:true) \
        | map { row-> tuple(row.module_name, row.version, row.module_name_version, row.module_pkg_dir, row.module_installer, row.module_install_date, row.module_category, row.module_prereqs , row.test_path, row.qsub_options) } \
        | runTests

}


// Assemble report_file from the published row files.  This runs even when the
// pipeline errors out or tasks are ignored, so a partial run still produces a
// usable report.  collect_report.py also reconciles the collected rows against
// the input CSV and records any test that produced no row at all.
workflow.onComplete {

    def collector = file("${projectDir}/collect_report.py")
    def collector_cmd = collector.exists() ? collector.toString() : "collect_report.py"

    def cmd = [ collector_cmd,
                "--test_results_dir", test_results_dir,
                "--input", params.csv_input,
                "--output", report_file,
                "--header", report_header ]

    println "Collecting report: ${cmd.join(' ')}"

    try {
        def proc = cmd.execute()
        def out = new StringBuffer()
        def err = new StringBuffer()
        proc.waitForProcessOutput(out, err)
        if( out ) println out.toString().trim()
        if( err ) System.err.println err.toString().trim()
        if( proc.exitValue() != 0 )
            System.err.println "WARNING: collect_report.py exited with status ${proc.exitValue()} - the report is incomplete, see the summary above."
    }
    catch( Exception e ) {
        System.err.println "ERROR: could not run collect_report.py (${e.message})."
        System.err.println "       Assemble the report by hand with:"
        System.err.println "       collect_report.py --test_results_dir ${test_results_dir} --input ${params.csv_input} --output ${report_file}"
        System.err.println "       (the header is taken from the result files when --header is not given)"
    }
}


process runTests {

    beforeScript 'source $HOME/.bashrc' // To make module command available.
    clusterOptions "-P ${params.project} -N nf_${module_name}_${version} ${qsub_options}" // Specify qsub options from CSV file
    executor params.executor
    errorStrategy params.errorStrategy  
    tag "$module_name_version" // Used for reporting.

    // Publish this test's single-row CSV as soon as the task finishes.  The
    // file is named after the module and its qsub file, which is unique per
    // input row, so a re-run of the same test overwrites its previous row.
    // The row is matched back to its input row on the test_path column inside
    // the file, not on this name.
    publishDir test_results_dir, mode: 'copy', overwrite: true,
               saveAs: { fn -> (module_name_version + '_' + file(test_path).getName())
                                   .replaceAll('[^A-Za-z0-9._-]', '_') + '.csv' }

    input:
    tuple val(module_name), val(version), val(module_name_version), val(module_pkg_dir), val(module_installer), val(module_install_date), val(module_category), val( module_prereqs ), val(test_path), val(qsub_options)

    output:
    path 'test_metrics.csv'
     
    script:
    """

    ## INITIALIZE ENVIRONMENT VARIABLES
    TEST_RESULT=FAILED                  # INITIATE AS FAILED. UPDATED WHEN TEST IS PASSED
    PASSED=NA                           # SET TO A COUNT ONCE THE TEST HAS RUN
    FAILED=NA                           # SET TO A COUNT ONCE THE TEST HAS RUN
    LOG_ERRORS=NA                       # SET TO A COUNT ONCE THE TEST HAS RUN
    EXIT_CODE=NA                        # SET TO THE TEST'S EXIT CODE ONCE IT HAS RUN
    TEST_DIR=`dirname $test_path`       # PATH TO THE TEST DIRECTORY FROM INPUT CSV
    QSUB_FILE=`basename $test_path`     # PATH TO QSUB FILE FROM INPUT CSV
    WORKDIR=`pwd`                       # THE BASE WORKING DIRECTORY FOR THIS PROCESS
    LOG=\$WORKDIR/log.txt               # LOG FILE USED FOR QSUB ARGUMENT
    RESULTS=\$WORKDIR/results.txt       # TEXT FILE WHERE RESULTS OF A TEST ARE STORED.
    METRICS=\$WORKDIR/test_metrics.csv  # SINGLE-ROW CSV WITH THIS TEST'S RESULT

    ## VALUES FROM THE INPUT CSV, AS SHELL VARIABLES SO THAT THE report_columns
    ## MAP AT THE TOP OF THIS PIPELINE CAN REFER TO THEM BY NAME.
    MODULE="$module_name_version"
    INSTALLER="$module_installer"
    CATEGORY="$module_category"
    INSTALL_DATE="$module_install_date"
    TEST_PATH="$test_path"

    ## WRITE THE TEST RESULT INFORMATION TO A CSV FILE.
    ## THIS IS RUN FROM AN EXIT TRAP SO THAT A ROW IS PRODUCED NO MATTER HOW
    ## THIS SCRIPT EXITS.  A TEST THAT DIES WITHOUT REACHING THE POST
    ## PROCESSING THEREFORE SHOWS UP IN THE REPORT AS FAILED WITH NA COUNTS
    ## INSTEAD OF SILENTLY VANISHING.
    ##
    ## THE TRAP ALWAYS EXITS 0.  A FAILURE IN HERE - THE TEST DIRECTORY COPY,
    ## OR THE TEST ITSELF - IS A PROBLEM WITH THE MODULE'S FILES OR TESTS, AND
    ## BELONGS IN THE REPORT AS A FAILED ROW.  IT IS ALSO THE ONLY WAY TO GET
    ## THE ROW PUBLISHED, SINCE NEXTFLOW DISCARDS THE OUTPUTS OF A TASK THAT
    ## EXITS NON-ZERO.  A FAILED NEXTFLOW TASK THEREFORE MEANS NEXTFLOW COULD
    ## NOT CREATE THE ENVIRONMENT TO RUN THE TEST AT ALL (E.G. THE QSUB SUBMIT
    ## ITSELF FAILED), WHICH IS WHAT WE WANT TO BE ALERTED TO.
    write_row() {
    RC=\$?   # EXIT STATUS THAT TRIGGERED THE TRAP. MUST BE READ FIRST.

    # EXIT_CODE IS STILL NA ONLY IF WE NEVER GOT AS FAR AS RECORDING THE
    # TEST'S OWN EXIT CODE.  USUALLY THAT MEANS THE SCRIPT DIED DURING SETUP
    # (THE TEST DIRECTORY COPY, THE cd, THE QSUB FILE EDIT), BUT THE TEST MAY
    # ALSO HAVE STARTED AND BEEN INTERRUPTED - SO REPORT THE STATUS THAT
    # TRIGGERED THE TRAP AS THE EXIT CODE WITHOUT CLAIMING WHICH IT WAS.
    if [ "\$EXIT_CODE" = NA ] && [ \$RC -ne 0 ]
    then
        echo "ERROR: exit code \$RC and no test exit code was recorded"
        EXIT_CODE=\$RC
    fi

cat > \$METRICS << EOF
${report_header}
${report_values}
EOF

    exit 0
    }
    trap write_row EXIT

    ## COPY TEST DIRECTORY INTO WORK DIRECTORY
    ## A FAILURE HERE ABORTS THE SCRIPT (BASH -e) AND THE EXIT TRAP ABOVE
    ## RECORDS IT AS A FAILED ROW WITH THE COPY'S EXIT CODE.
    cp -r \$TEST_DIR \$WORKDIR


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
    echo keep_passed=${params.keep_passed}

    # CD INTO TEST DIRECTORY
    BASE_NAME=`basename \$TEST_DIR` 
    NF_TEST_DIR=\$WORKDIR/\$BASE_NAME     # GET THE NAME OF THE TEST DIRECTORY
    cd \$NF_TEST_DIR

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


    # Check if the test directory should be kept or deleted based on the test result and keep_passed parameter
    if [[ \$TEST_RESULT == PASSED &&  ${params.keep_passed} == true ]]
    then
        echo "Parameter keep_passed=${params.keep_passed}, keeping the test directory."
    elif [[ \$TEST_RESULT == PASSED &&  ${params.keep_passed} == false ]]
    then
        echo "Parameter keep_passed=${params.keep_passed} and test result is \$TEST_RESULT, therefore deleting the test directory."
        rm -rf \$NF_TEST_DIR
    fi

    """
}
