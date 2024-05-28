# Load the ggplot2 package which provides
# the 'mpg' dataset.
library(ggplot2)

data <- read.csv("report_module8_list.csv")

fluidPage(
  
  
  titlePanel("Basic DataTable"),
  
  mainPanel(
    fileInput(inputId = "file", label = "Choose CSV File", accept = ".csv")
  ),

  # Create a new Row in the UI for selectInputs
  fluidRow(
    column(4,
        selectInput("result",
                    "Test Result:",
                    c("All",
                      unique(as.character(data$test_result))))
    ),
    column(4,
        selectInput("cat",
                    "Category:",
                    c("All",
                      unique(as.character(data$category))))
    ),
    column(4,
        selectInput("trans",
                    "Cylinders:",
                    c("All",
                      unique(as.character(mpg$trans))))
    )
  ),
  # Create a new row for the table.
  DT::dataTableOutput("table")
)
