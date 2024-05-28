# Load the ggplot2 package which provides
# the 'mpg' dataset.
library(ggplot2)

function(input, output) {
  

    # Filter data based on selections
    output$table <- DT::renderDataTable(DT::datatable({
      
      req(input$file)
      data <- read.csv(input$file$datapath)
      
      if (input$result != "All") {
        data <- data[data$test_result == input$result,]
      }
      
      if (input$cat != "All") {
        data <- data[data$category == input$cat,]
      }
      
      if (input$trans != "All") {
        data <- data[data$trans == input$trans,]
      }
      
      data
    }))

}
