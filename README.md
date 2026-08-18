# corpus-caesarianum-authorship
Collaboration between Signe Janoska-Bedi and Matthew DeHass on a study of the authorship of the texts in the Corpus Caesarianum (Bellum Gallicum, Bellum Alexandrinum, Bellum Hispaniense, Bellum Africum)

**Note**: This repository relies on the PerseusDL/canonical-latinLit repo. To make cleaning up the data easier, a fork at [cubis182/canonical-latinLit](https://github.com/cubis182/canonical-latinLit) has been created and used in the process of cleaning up OCR errors. 

Directory:

**feature_csv_files**: Directory containing data after all processing has been complete and variables have been selected. All .csv files in this directory follow the same format. The columns of these files are feature values (i.e. singular, indicative, nominative, etc.), the rows are sections of a work. The asterisks are additional information about the style of variables (whether they are arranged like Gorman 2020 or bare frequencies of individual features). If unnamed, the data includes the Corpus Caesarianum. Each field is the number of times that feature occurs in the text.

**Images**: Images to be used in the article.

**postagged/**: Directory of files where each row is a separate word in the Corpus Caesarianum, tagged with the (Universal Dependencies)[https://universaldependencies.org/#language-] scheme. Processed in data-processing.Rmd

**process_perseus_texts/\*_data_text_perseus_tokenized.csv**: Files containing the tokenized (i.e. word split) version of the corpus caesarianum. The columns come in the following format:
  (line): line number
  commentary: title of commentary (gallic | civil | alexandrine | african | spanish)
  book: book number
  text: source text
  src: CTS URN referencing the work and section
  chapter: chapter number
  tokens: tokenized form of the text

**rdata-backups**: .RData files with R environments for ease of loading variable sets. Primarily for internal use; data should be re-run for new users.

**requirements**: A list of required packages and software for using the code in this repository. CURRENTLY NEEDS UPDATING
