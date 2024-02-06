
params.csv_input = "" // Path to CSV File produces by find_qsub.py script
nextflow.enable.dsl=2

workflow {

// Load the csv file and split the rows into tuples.
// Then execute runTests process
    Channel.fromPath(params.csv_input) \
        | splitCsv(header:true) \
        | map { row-> tuple(row.module_name, row.version, row.module_name_version, row.module_pkg_dir, row.module_installer, row.module_install_date, row.module_category, row.module_prereqs , row.test_path, row.qsub_options) } \
        | runTests
}


process runTests {

    beforeScript 'source $HOME/.bashrc' // To make module command available.
    clusterOptions "$qsub_options" // Specify qsub options from CSV file
    executor 'sge'
    errorStrategy 'ignore'  // "ignore"- will continue with other tests if there is an error
			    // "terminate" - kill all tests when error is encountered
    tag "$module_name_version" // Used for reporting.

    input:
    tuple val(module_name), val(version), val(module_name_version), val(module_pkg_dir), val(module_installer), val(module_install_date), val(module_category), val( module_prereqs ), val(test_path), val(qsub_options)
    

    script:
    """
    echo $NSLOTS $QUEUE
    AUTHOR=$module_installer
    CATEGORY=$module_category
    echo     
    echo $module_name_version $test_path >> log.txt
    bash $test_path log.txt 1>  results.txt 

    if [ "\$(grep -c -v Passed results.txt)" -gt 0 ]
    then
       exit 1  
    fi 


    """
}



