# author: Matthew DeHass
# date created: 7/21/2026
# name: functions.R


# Desc --------------------------------------------------------------------

# This R file contains a selection of functions used in this repository.
# By the end of the project, all the functions should be moved here.
# Each code section in this file corresponds to the file the functions
# were originally designed for. This does not mean they are only used
# there!


# data-processing.Rmd -----------------------------------------------------

# Cleans data from ./postagged folder by altering and renaming variables
# in a way convenient for the analysis in data-processing.Rmd.
# Does not modify in place, so the result must be assigned to the data frame
# passed in.
# If not used in data-processing.Rmd, the default value for the second argument
# CANNOT be used, unless the use_parent parameter is defined in the YAML header.
prepare_data <- function(data, use_parent = params$use_parent) {
  require(magrittr)
  require(tidyverse)

  # This isn't a ratio or count variable
  data %<>%
    mutate(Person = as.factor(Person))

  # T he Bellum Alexandrinum may represent two clear stages of composition,
  # and we might want to respond to Gaertner's argument that the completion
  # of Alex. and the BC. were one project. I'll do this by making sections
  # 1-21 "book" 1 and the rest "book" 2

  # Don't forget the sections are zero-indexed, so 0-20 is the supposedly 
  # Caesarian section, not 1-21.
  # since I'm using a data table, subset without the comma, unlike base R
  data$book[data$path == "alexandrine" & data$section > 20] <- 2


  # We also want to reduce the effect of noisy data on the final results.
  # For the moment, this is only a testing ground based on manual review.
  # I'm still gathering accuracy data, and will take a data-based approach
  # in the next round.
  #
  # The data needs to be split up by section first, then put back into
  # books. The way I recommend doing this is appending both the book and
  # section number to the title to get this result: "*title*\_*x_x(x)*".
  # Then, we use the same code blocks below as in the Letters to Atticus,
  # feeding this new title instead of the base one.

  data %<>%
    rowwise() %>%
    mutate(title = gsub(" ", "", paste(title, "_", book, "_", section)))

  # Replace ambiguous names (i.e. Imp can be Imperfective or Imperative)
  replace_value <- function(column, to_replace, replace_string) {
    # Rename "Imp" to "Imperative" in mood category
    levels(data[[column]]) <- c(levels(data[[column]]), replace_string)
    sequence <- which(data[[column]] == to_replace)
    data[[column]][sequence] <- replace_string
    remove(sequence)

    data[[column]][data[[column]] == to_replace] <- replace_string
    data[[column]] <- droplevels(data[[column]]) # Remove the old "Imp
    return(data)
  }

  data <- replace_value("Mood", "Imp", "Imperative")
  data <- replace_value("Mood", "Ind", "Indicative")
  if (use_parent) {
    data <- replace_value("parent_Mood", "parent_Ind", "parent_Indicative")
    data <- replace_value("parent_Mood", "parent_Imp", "parent_Imperative")
  }

  data
}
