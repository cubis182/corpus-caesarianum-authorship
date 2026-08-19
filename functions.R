# author: Matthew DeHass
# date created: 7/21/2026
# name: functions.R

# Desc --------------------------------------------------------------------

# This R file contains a selection of functions used in this repository.
# By the end of the project, all the functions should be moved here.
# Each code section in this file corresponds to the file the functions
# were originally designed for. This does not mean they are only used
# there!

library(conflicted)
library(factoextra)
# library(dplyr)
library(ggrepel)
library(tidyverse)
library(cluster)
library(dendextend)
library(combinat)
library(MASS)
library(multcomp)
library(ggtext)
library(printr)
library(magrittr)
library(logrittr)
library(data.table)
library(collapse)
library(logger)
library(progress)


# data-processing.Rmd -----------------------------------------------------



# Utilities

# modes: "title", "book", "section"
get_title_segment <- function(string, mode = "book") {
  split_str <- unlist(strsplit(string, "_"))

  # We use gsub to ensure there are no spaces, might be unnecessary
  gsub(" ", "", paste(
    split_str[1],
    if (mode != "title") paste("_", split_str[2]),
    if (mode == "section") paste("_", split_str[3])
  ))
}

# add a version of `attributes<-` which returns the object too

cicero_works <- "(philippics|senectute|amicitia|brutus|deiotaro)"
sallust_works <- "(catilinae_sallusti|iugurthine)"
# reorder works so ones by the same author go together.
reorder_works <- function(source_data) {
  
  # move Cicero to the end, to keep authors separated
  bind_rows(
    filter(source_data, str_starts(title, cicero_works)),
    filter(
      source_data, 
      !str_starts(title, cicero_works) & !str_starts(title, sallust_works)),
    filter(source_data, str_starts(title, sallust_works)),
  )
}

# Replace ambiguous names
replace_ambiguous <- function(data, use_parent) {
  # Replace ambiguous names (i.e. Imp can be Imperfective or Imperative)
  replace_value <- function(column, to_replace, replace_string) {
    # Rename "Imp" to "Imperative" in mood category
    levels(data[[column]]) <- c(levels(data[[column]]), replace_string)
    sequence <- which(data[[column]] == to_replace)
    data[[column]][sequence] <- replace_string
    remove(sequence)

    data[[column]][data[[column]] == to_replace] <- replace_string
    if (is.factor(data[[column]])) data[[column]] <- droplevels(data[[column]]) # Remove the old "Imp", if a factor
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


# Cleans data from ./postagged folder by altering and renaming variables
# in a way convenient for the analysis in data-processing.Rmd.
# Does not modify in place, so the result must be assigned to the data frame
# passed in.
# If not used in data-processing.Rmd, the default value for the second argument
# CANNOT be used, unless the use_parent parameter is defined in the YAML header.
prepare_data <- function(data, use_parent = params$use_parent) {
  # The Bellum Alexandrinum may represent two clear stages of composition,
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

  data %<>% replace_ambiguous(use_parent)
  
  # Remove all words which have "X" as their part of speech
  data %<>% filter_out(tag == "X")

  data
}

## Gorman Variables -------

# Filters to rows which have ZERO NA values in them
no_na <- function(tib, vec) {
  if (NA %in% vec) {
    return(tib)
  }
  tib <- filter(tib, .data[[vec[1]]] != FALSE)
  vec <- vec[2:length(vec)]
  return(no_na(tib, vec))
}

# Given a matrix which includes a set of column names in the source_data, return the number of rows that have valid data in all columns
variable_count <- function(matrix, source_data, pb) {
  pb$tick()
  subset_of_data <- source_data %>%
    tidytable::select(all_of(matrix)) %>%
    no_na(colnames(.))
  
  return(nrow(subset_of_data))
}

# combinations_n <- 2

# Get rid of values that don't appear in more than 20% of the corpus
cull <- function(combinations) {
  print(paste("Length before culling: ", as.character(length(combinations$a))))

  # Get rid of features which occur in less than 20% of the corpus
  filtered <- combinations |> filter(num > (nrow(data) / 5))

  print(paste("Length after culling: ", as.character(length(filtered$a))))
  return(filtered)
}

# This function returns a list of all combinations of a variable which occur
variable_combinations <- function(combinations_n, source_data) {
  cols <- if (params$use_parent) colnames(source_data |> tidytable::select(tag:parent_Deprel & !parent_form & !parent_lemma)) else colnames(source_data |> tidytable::select(tag:Gender))

  select_combinations <- combn(cols, combinations_n)

  # length(select_combinations)

  # Get a table showing the number of times all the features in a combination are attested
  combination_freqs <- apply(X = select_combinations, MARGIN = 2, FUN = variable_count, source_data = source_data, pb = progress_bar$new(total = length(select_combinations) * combinations_n))

  tib_select_combinations <- as_tibble(select_combinations)

  # Get the length of the column
  col_len <- nrow(tib_select_combinations)

  # Add a new row with the frequency each one occurs
  tib_select_combinations[(col_len + 1), ] <- as.list(as.character(combination_freqs))

  # Time to take out the trash!
  remove(col_len)

  # transpose
  # browser()

  tib_select_combinations <-
    tib_select_combinations |>
    # The number of columns depends on the $ of combinations, hence the code in the following line
    mutate(type = c(letters[1:combinations_n], "num")) |>
    # Don't select 'num'
    pivot_longer(!type) |>
    pivot_wider(names_from = type, values_from = value) |>
    dplyr::select(!name) |>
    mutate(across(num, as.integer))

  # browser()

  arrange(tib_select_combinations, num)

  tib_select_combinations <- tib_select_combinations |>
    filter(num > 0) |>
    arrange(num)

  return(tib_select_combinations |> cull() |> dplyr::select(-num))
}

# Requires a row from a tibble that only includes valid column names and no numerics / other data types
# Discards any data points that occur less than 30 times
# USE THIS TO COUNT A VARIABLE OR SET OF VARIABLES!!!!
get_var_combos <- function(var_combn, source_data) {
  # browser()

  # This is used to select the desired columns
  selection_char <- as.character(var_combn)
  selection_char <- selection_char[!is.na(selection_char)]

  var_combos <- source_data[selection_char]
  # browser()
  # Added this line to avoid the expensive na.omit() operation
  var_combos <- var_combos[complete.cases(var_combos), ]

  var_combos <- collapse::fcount(var_combos, drop = TRUE) #|> na.omit()
  # Added next line to avoid expensive string comparisons

  if (nrow(var_combos) > 0) {
    # final.table <- table(var_combos) #|> as_tibble()

    # browser()

    return(var_combos) #|> filter(n > 30)) #initially not 30, but nrow(source_data / 5)
  } else {
    return(NULL)
  }
}

# This function takes a set of variable combinations (one_combinations,
# two_combinations, etc.) and applies the get_var_combos function to all
# of them, creating a data frame out of it. Any in the lower quartile are
# culled.

count_var_combos <- function(var_combn, source_data) {
  list_combn <- apply(var_combn, MARGIN = 1, get_var_combos, source_data = source_data) |> bind_rows()

  # unlist()

  # browser()
  # list_combn <- list_combn

  # browser()
  # Initially removed low-frequency items, but that resulted in NA values in the final data.
  # I've decided, though, that the reduction in quality is worth the increase in performance and lower memory usage. I remove anything below the lower quartile
  lower_quartile <- quantile(list_combn$N)[["25%"]]
  .GlobalEnv$lower_quartiles <- c(.GlobalEnv$lower_quartiles, lower_quartile)
  return(list_combn[list_combn$N > lower_quartile, ]) # subset(list_combn, list_combn > nrow(source_data) / 10)) # |> as_tibble() |> filter(V1 > 30))
}

# Some helper functions for the upcoming run_combos and get_vars function
# which creates the final data frame are in the cell below. They're a
# refactoring of the above cell, which should get replaced soon.

convert_row_to_character <- function(row_of_factors) {
  row_of_factors |> mutate(across(where(is.factor), as.character))
}

has_all_feature_types <- function(row_from_source_data, character_vector_of_feature_values) {
  # Unnecessary when using apply() around this function
  # row_from_source_data %<>% mutate(across(everything(), as.character))

  # if (!is.character(row_from_source_data)) {
  #   row_from_source_data %<>% mutate(across(where(is.factor), as.character))
  # }

  # Only return true for this row if ALL characters in the vector on the left are in the row on the right
  # Note on optimization: %chin% is supposedly faster than %in%
  all(character_vector_of_feature_values %in% row_from_source_data)
}

get_number_rows_with_feature_types <- function(vector_of_feature_values, source_data) {
  # browser()
  fn_name <- "get_number_rows..."

  count_of_feature_values <- sum(
    apply(X = source_data, MARGIN = 1, FUN = has_all_feature_types, character_vector_of_feature_values = vector_of_feature_values)
  )
  log_debug("{fn_name}: The feature values '{paste0(vector_of_feature_values, collapse = ',')}' occurred {count_of_feature_values} times in the dataset.")

  count_of_feature_values
}

# Okay, now we create functions used down below for transposing the data
# (ensuring rows are observations and columns are variables) and selecting
# the top *n* variables by relative frequency.

# all_vars <- all_vars |> mutate(title = unlist(title)

# First, like Gorman, remove ones appearing in less than 20% of the corpus. For section-by-section, that's 134 / 5 = 27

# Recommended operation on the output of get_vars()
transpose_all_vars <- function(all_vars) {
  all_vars <- all_vars |> mutate(title = unlist(title))

  all_vars <- pivot_wider(
    all_vars,
    values_fn = sum,
    names_from = pasted,
    values_from = n,
    values_fill = 0
  )

  return(all_vars |> as_tibble())
}

# Reduces output of transpose_all_vars to top n variables; maximum value for n is 18,000
select_top_variables <- function(all_vars, n) {
  # For logging
  fn_name <- get_logger_meta_variables(log_level = INFO)$fn

  # An optimization step to reduce the size of the data we're dealing with
  number_of_variables <- length(unique(all_vars$pasted))
  number_of_rows <- nrow(all_vars)
  min_val <- sort(all_vars$n, decreasing = TRUE)[1:(n * (number_of_rows / number_of_variables))] |>
    min()

  log_info("{fn_name}: Number of variables is {number_of_variables}, minimum value in sections 1:{(n * (number_of_rows / number_of_variables))} is {min_val}.")

  original_length <- nrow(all_vars)
  all_vars_reduced <- all_vars %>=% filter(n > min_val)
  log_info("{fn_name}: Data frame reduced from {original_length} rows to {nrow(all_vars_reduced)}.")

  # Get a list of the distinct variables
  variables <- unique(all_vars_reduced$pasted)
  log_info("{fn_name}: Number of variables to compare is {format(length(variables), big.mark = ',')}")

  # NOTE: COMMENTING THIS OUT FOR NOW, TO SEE HOW THE HEURISTIC PERFORMS
  # For each distinct variable, sum up its values across all works, then store in a list
  #browser()
  combined_vars <- lapply(variables, FUN = function(var) sum(all_vars_reduced$n[all_vars_reduced$pasted == var]))
  combined_vars %<>% unlist

  # Add the names to the list
  names(combined_vars) <- variables

  sorted <- sort(combined_vars, decreasing = TRUE)[1:n]
  to_filter_by <- names(sorted)
  
  all_vars |> filter(pasted %in% to_filter_by)
}

# Now, lets create a function that gets one long tibble with every single
# variable in it.

# character select : A character value which is the section/book we're using in this function
count_combinations_per_section <- function(combinations, source_data, title_str) {
  # browser()
  t1 <- proc.time()
  norm_val <- 1000 / nrow(source_data)

  # save processing time by converting source_data to matrix now
  source_data <- as.matrix(source_data)

  # more efficient than using rows
  combinations <- t(as.matrix(combinations))

  counts <- apply(combinations, MARGIN = 2, FUN = get_number_rows_with_feature_types, source_data = source_data)
  counts <- counts * norm_val
  return_value <- bind_cols(t(combinations), tibble(n = counts))
  return_value$title <- title_str
  # dplyr::rowwise() %>%
  # summarize(
  #   n = get_number_rows_with_feature_types(c_across(everything()), source_data)
  # ) %>%
  # bind_cols(combinations, .) |>
  # mutate(n = n * norm_val, title = title_str)

  # browser()
  log_debug("Finished counting combinations for {title_str}")
  print(proc.time() - t1)
  
  
  return_value
}

run_combos <- function(source_data, title_str, pb) {
  t1 <- proc.time()

  all_vars <- count_var_combos(combinations, source_data) |>
    unite(col = "pasted", -N, sep = "|", na.rm = TRUE) |>
    as_tibble(.name_repair = "universal_quiet")

  # browser()

  names(all_vars)[1] <- "pasted"

  # browser()

  # Normalize frequencies by occurrence per 1000 words
  norm_val <- 1000 / nrow(source_data)
  all_vars <- all_vars |>
    mutate(n = N * norm_val) |>
    dplyr::select(-N)

  all_vars <- all_vars |>
    mutate(title = title_str) # The titles should all be the same...


  delta_time <- proc.time() - t1
  log_debug(paste(names(delta_time), delta_time, sep = ": ", collapse = ", "))
  pb$tick()
  
  return(all_vars)
}

# mode: whether to divide the data into commentaries, books, or chapters
# If getting the variables from an existing data frame, make sure they're
# in the combinations variable and use_preset is set to TRUE
get_vars_gorman <- function(mode = "book", source, presupplied_variables = NULL) {
  if (mode == "book") {
    # browser()
    source_data <- source |>
      rowwise() |>
      mutate(title = get_title_segment(title))
  } else if (mode == "commentary") {
    source_data <- source |>
      rowwise() |>
      mutate(title = get_title_segment(title, "title"))
  } else if (mode == "chapter") {
    source_data <- source
  } else {
    return(NULL)
  }

  if (is.null(presupplied_variables)) {
    all_vars <- source_data |>
      group_by(title) %>%
      # lazy_dt() |>
      group_map(~ run_combos(.x, .y, pb = progress_bar$new(total = length(unique(source_data$title))))) |>
      bind_rows() |>
      mutate(title = unlist(title))
  } else {
    # browser()
    all_vars <- source_data |>
      # For debugging:
      # slice_sample(n = 100) |>
      rowwise() |>
      # check whether this line is necessary
      # mutate(title = unlist(strsplit(title, "_"))[1:2] |> paste(collapse="_")) |>
      group_by(title) %>%
      group_map(~ count_combinations_per_section(presupplied_variables, source_data = .x, title_str = .y)) |>
      bind_rows() |>
      mutate(title = unlist(title)) |>
      unite(col = "pasted", 1:5, sep = "|", na.rm = TRUE)
  }

  return(all_vars)
}

# Each of these feature combinations is a column, 
#   each row a document or document section, and 
#   the cells are the normalized frequencies within those documents.

# Pass an output from get_vars(), get the variables back in table form 
#   so they can be passed into the get_vars() function with a new dataset. 
#   That way, a new dataset can be processed with the same variables as another.
combinations_from_existing <- function(all_vars) {
  # Get the names() attribute
  vars_unsplit <- all_vars |>
    dplyr::select(-title) |>
    colnames()


  # lapply over the names, using strsplit on each one
  split_vars <- lapply(X = vars_unsplit, FUN = strsplit, split = "[|]")

  split_vars <- unlist(split_vars, recursive = FALSE)

  # For each item in the list (which is a character vector), we construct 
  #   a data frame where each column is the character vector. 
  #   NAs should appear in rows that aren't attested
  combinations_new <- data.frame(labels = letters[1:5])

  for (item in split_vars) {
    combinations_new <- cbind(combinations_new, item[1:5])
  }

  # Transpose the data frame
  combinations_new <- t(combinations_new) |>
    as_tibble(.name_repair = "unique") |>
    slice(-1)

  combinations_new
}

get_count_by_title_features <- function(title, feature_char, source_data, pipe = TRUE) {
  # Remove space from the title
  title_selected <- gsub(pattern = " ", replacement = "", title)

  # Split column name into a character vector
  if (pipe)  vars_unsplit <- unlist(strsplit(feature_char, "[|]"))
  else vars_unsplit <- unlist(strsplit(feature_char, "[.]"))

  # Filter source_data to the title, 
  #   using partial matches with str_starts() from stringr package
  filtered_data <- source_data |> 
    filter(str_starts(gsub(" ", "", title), title_selected))

  # Pass character vector and source_data to 
  #   get_number_rows_with_feature_types()
  count_from_source_data <- get_number_rows_with_feature_types(
    vars_unsplit, 
    source_data = filtered_data
    )
  # Normalize the value per 1000 words
  (count_from_source_data / nrow(filtered_data)) * 1000
}

## CUSTOM FEATURE SET
#> This feature set is a hodge-podge developed from research, with the sources
#> described in more detail in the data-processing notebook.
#> 
# The following code is run just like `run_combos()`
# Output is three-column tibble: title, pasted, n
# Avoid using the default values of the parameters to this function.
run_custom <- function(
    source_data, 
    title_str, 
    pos_ngrams = feature_ngrams(source_data, "tag", 3),
    lemmas = get_top_lemmas(source_data)
    ) {
  # Features to use:
  # High-frequency lemmas (concatenated with POS tag)
  # POS frequencies
  # POS n-grams
  
  #POS
  pos <- unique(as.character(source_data$tag))
  pos_count <- map_dbl(pos, ~ nrow(source_data[source_data$tag == .x,]) / nrow(source_data))
  final_pos_count <- tibble(pasted = pos, n = pos_count)
  
  # LEMMAS
  final_lemmas <- count_lemmas(source_data, lemmas)
  
  # POS NGRAMS
  final_pos_ngrams <- count_ngrams(source_data, pos_ngrams)

  return_df <- bind_rows(final_pos_count, final_lemmas, final_pos_ngrams)
  
  log_debug("Finished {title_str}")
  
  # Multiply all frequencies by 1,000
  return_df |> mutate(title = title_str, n = n * 1000)
}

get_vars_custom <- function(mode = "book", source) {
  if (mode == "book") {
    # browser()
    source_data <- source |>
      rowwise() |>
      mutate(title = get_title_segment(title))
  } else if (mode == "commentary") {
    source_data <- source |>
      rowwise() |>
      mutate(title = get_title_segment(title, "title"))
  } else if (mode == "chapter") {
    source_data <- source
  } else {
    return(NULL)
  }
  
  lemmas <- get_top_lemmas(data)
  pos_ngrams <- feature_ngrams(data, "tag", 3, top = 100)
  pos <- unique(data$tag); pos <- data$tag[data$tag != "PUNCT"]
  
  source_data |>
    group_by(title) %>%
    group_map(~ run_custom(.x, .y, pos_ngrams, lemmas)) |>
    bind_rows() |>
    mutate(title = unlist(title))
  
}

# Get n-grams of a feature from the column.
# .unique tells whether to return unique values, or to return copies of every
#   n-gram. (So, if NOUN|NOUN|NOUN appears 20 times, it will appear 20 separate
#   times in the list when this argument is FALSE)
# top is accepts an integer as an argument, saying the number of top ngrams to
#   include. Pass NULL to return all
feature_ngrams <- function(source_data, colname, n, .unique = TRUE, top = NULL) {
  var <- source_data[[colname]]
  to_exclude <- c("PUNCT", "X")
  var <- var[var %notin% to_exclude]
  # For each variable, paste it with the *n* following items in the sequence.
  # The if statement ensures anything indexed past the end is discarded
  combos_with_repetition <- imap_chr(var, ~ {
    # browser()
    if (.y + (n - 1) < length(var)) paste0(var[.y:(.y + (n - 1))], collapse = "|") else NA_character_
    })
  combos_with_repetition <- na.omit(combos_with_repetition)
  
  # Get only the top n-grams, if requested
  if (length(top) > 0) {
    tab_ngrams <- sort(table(combos_with_repetition), decreasing = TRUE)
    combos_with_repetition <- names(tab_ngrams[1:top])
  }
  
  # Return only unique values
  if (.unique) unique(combos_with_repetition) else combos_with_repetition
}


# For lemmas, I would recommend sticking to top 20-25; some content words, 
#   such as 'castra', begin to peek in. These will not help us distinguish 
#   authors.
# Methods include "tf" and "tf-idf" currently
get_top_lemmas <- function(source_data) {
  
  # Get top lemmas, removing undesirable ones
  exclude <- c(".", "Caesar", "?", "castra", "hostis", "bellum", "publicus", 
               "legio", "dies", "miles", "magnus", "noster")
  lemmas <- source_data %>%
    filter_out(lemma %in% exclude) 
  lemmas <- paste(lemmas$lemma, lemmas$tag, sep = "|")  
  names(sort(table(lemmas), decreasing = TRUE)[1:51])
}

# Counts lemma-tag combos provided from the get_top_lemmas function.
count_lemmas <- function(source_data, lemma_tag_combos) {
  source_data %<>% unite(col = pasted, lemma, tag, sep = "|")
  tibble(
    pasted = lemma_tag_combos,
    n = map_dbl(lemma_tag_combos, ~ nrow(source_data[source_data$pasted == .x,]) / nrow(source_data))
  )
}

count_ngrams <- function(source_data, pos_ngrams) {
  # Split the n_grams
  # Turning into a tibble unnecessary, but helps
  n <- length(str_split(pos_ngrams[1], "[|]")[[1]])
  ngrams_in_section <- feature_ngrams(source_data, "tag", n, FALSE)
  
  counts <- map_dbl(pos_ngrams, ~ sum(str_count(ngrams_in_section, coll(.x))) / nrow(source_data))

  tibble(
    pasted = pos_ngrams,
    n = counts
  )
}


# Set pipe to FALSE if each combined variable is separated by periods instead
verify_random_cell <- function(all_vars, source_data, pipe = TRUE) {
  # For logging purposes
  fn_name <- get_logger_meta_variables(log_level = INFO)$fn

  # Select a random cell from all_vars
  rand_row <- slice_sample(all_vars)
  column_number <- sample(2:ncol(rand_row), size = 1) # column number of the 
                                                      # targeted cell, excluding 
                                                      # titles
  cell <- rand_row[, column_number]

  # Get its title and column name
  title <- rand_row$title
  colname <- names(all_vars)[column_number]

  log_info("{fn_name}: Selecting all_vars[title == {title}, '{colname}']")
  log_info("{fn_name}: Value of cell is {cell}")

  count_from_source_data <- get_count_by_title_features(
    title = title, 
    feature_char = colname, 
    source_data = source_data,
    pipe
    )

  log_info("{fn_name}: The count retrieved from the source data is {count_from_source_data}")
  log_info("{fn_name}: count == cell: {signif(count_from_source_data, digits = 2) == signif(cell, digits = 2)}")
  (signif(count_from_source_data, digits = 2) == signif(cell, digits = 2))[[1]]
}

# Wrapper around dist() and as.dist() which allows the user to supply a function 
#   as a custom distance measure. 
# The first two arguments of the custom method must be the vectors to be compared.
# The return value of the function passed to the method argument must be a 
#   single double
# ... contains other arguments to be passed to the custom method.
# Retains default behavior of get_dist() if a string is supplied.
custom_dist <- function(m, method, diag = FALSE, upper = FALSE, ...) {
  # If a function is supplied, use it to create a distance matrix.
  if (typeof(method) == "closure") {
    
    # To convert the results to class "dist", all the code is wrapped in 
    #   brackets and placed in the first argument to `as.dist()`
    as.dist({
      # Get the number of observations (i.e. documents)
      observations <- nrow(m)
      
      # Each column of the following variable (to_compare) will be a length two 
      #   integer vector that lets us select every combination of rows.
      # Each column will also be the 2D coordinate in the distance matrix.
      to_compare <- combn(observations, 2)
      
      # Result matrix, which we initialize as an empty matrix full of zeroes
      dist_matrix <- matrix(
        data = 0.0, 
        nrow = observations, 
        ncol = observations
        )
      
      anonymous <- function(x) {
        # Get two rows as vectors
        vec_a <- as.numeric(m[x[1],])
        
        vec_b <- as.numeric(m[x[2],])
        
        # Raise an error if the number of arguments is incorrect.
        tryCatch(
          error = function(cnd) {
            if (pmatch("unused argument", cnd$message, nomatch = 0L) > 0L) {
              rlang::abort(
                message = paste0(
                  "Expected method with at least two arguments,",
                  glue::glue(" method has {length(formals(method))} arguments"
                             )
                  )
                )
            } else stop(cnd)
          },
           distance <- method(vec_a, vec_b, ...) 
        )
        
        # Add the distance to the matrix
        tryCatch(
          error = function(cnd) {
            if (pmatch("replacement length", cnd$message, nomatch = 0L) > 0L) {
              rlang::abort(message = paste0(
                "Expected distance method to return a single double,",
                " got a vector of length ",
                glue::glue("{length(distance)}: {distance[1:5]...}")))
            } else stop(cnd)
          },
          {
            dist_matrix[x[2], x[1]] <<- distance
            if (upper) dist_matrix[x[1], x[2]] <<- distance
          }
        )
      }
      
      apply(X=to_compare, MARGIN=2, anonymous)
    
      rownames(dist_matrix) <- rownames(m)
      
      dist_matrix
    },
    diag,
    upper)
    
  } else if (
    pmatch(
      method, 
      c(
        "pearson", 
        "spearman", 
        "kendall", 
        "euclidean", 
        "maximum", 
        "manhattan", 
        "canberra",
        "binary", 
        "minkowski"
        )
      )
    ) {
    factoextra::get_dist(m, method, diag, upper)
  }
}

minmax <- function(a, b) {
  min <- sum(map2_dbl(a, b, ~ min(c(.x, .y))))
  max <- sum(map2_dbl(a, b, ~ max(c(.x, .y))))
  value <- min / max
  1.0 - value
}
