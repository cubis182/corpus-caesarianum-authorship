# corpus-caesarianum-authorship
Collaboration between Signe Janoska-Bedi and Matthew DeHass on a study of the authorship of the texts in the Corpus Caesarianum (Bellum Gallicum, Bellum Alexandrinum, Bellum Hispaniense, Bellum Africum)

File Definitions (WIP):

**feature_csv_files**: All .csv files in this directory follow the same format. The columns of these files are feature values (i.e. singular, indicative, nominative, etc.), the rows are sections of a work. The asterisks are additional information about the style of variables (whether they are arranged like Gorman 2020 or bare frequencies of individual features). If unnamed, the data includes the Corpus Caesarianum. Each field is the number of times that feature occurs in the text.

**process_perseus_texts/\*_data_text_perseus_tokenized.csv**: Files containing the tokenized (i.e. word split) version of the corpus caesarianum. The columns come in the following format:
  (line): line number
  commentary: title of commentary (gallic | civil | alexandrine | african | spanish)
  book: book number
  text: source text
  src: CTS URN referencing the work and section
  chapter: chapter number
  tokens: tokenized form of the text

**postagged/**: Directory of files where each row is a separate word in the Corpus Caesarianum, tagged with the (Universal Dependencies)[https://universaldependencies.org/#language-] scheme. Processed in data-processing.Rmd


Sources:
Gorman, Robert. “Author Identification of Short Texts Using Dependency Treebanks without Vocabulary.” Digital   Scholarship in the Humanities 35, no. 4 (2020): 812–25. https://doi.org/10.1093/llc/fqz070.
