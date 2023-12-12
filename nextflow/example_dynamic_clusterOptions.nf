
params.index = "./input_new_params_clusterOptions.csv"
nextflow.enable.dsl=2

workflow {
    Channel.fromPath(params.index) \
        | splitCsv(header:true) \
        | map { row-> tuple(row.module, row.qsub_test, row.clusterOptions) } \
        | runTests
}

process runTests {
    clusterOptions {clusterOptions}
    executor 'sge'
    
    errorStrategy 'terminate'
    tag "$module"
    input:
    tuple val(module), val(qsub_test), val(clusterOptions)
    

    script:
    """
    echo $NSLOTS $QUEUE
    echo     
    echo $module $qsub_test >> log.txt
    bash $qsub_test log.txt >  results.txt 2>&1

    if [ "\$(grep -c -v Passed results.txt)" -gt 0 ]
    then
       exit 1  
    fi 


    """
}



