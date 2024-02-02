
params.index = "/projectnb/dvm-rcs/milechin/git/PkgAutoTest/nextflow/temp/test.csv"
nextflow.enable.dsl=2

workflow {
    Channel.fromPath(params.index) \
        | splitCsv(header:true) \
        | map { row-> tuple(row.module_name, row.version, row.module_name_version, row.module_pkg_dir, row.module_installer, row.module_install_date, row.module_category, row.module_prereqs , row.test_path, row.qsub_options) } \
        | runTests
}


process runTests {
    beforeScript = 'source $HOME/.bashrc'
    clusterOptions "$qsub_options"
    executor 'sge'
    executor.jobName = {"nf-test-$module_name_version"}
    errorStrategy 'ignore'
    tag "$module_name_version"
    input:
    tuple val(module_name), val(version), val(module_name_version), val(module_pkg_dir), val(module_installer), val(module_install_date), val(module_category), val( module_prereqs ), val(test_path), val(qsub_options)
    

    script:
    """
    echo $NSLOTS $QUEUE
    echo     
    echo $module_name_version $test_path >> log.txt
    bash $test_path log.txt >  results.txt 2>&1

    if [ "\$(grep -c -v Passed results.txt)" -gt 0 ]
    then
       exit 1  
    fi 


    """
}



