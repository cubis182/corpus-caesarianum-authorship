# corpus-caesarianum-authorship
Collaboration between Signe Janoska-Bedi and Matthew DeHass on a study of the authorship of the texts in the Corpus Caesarianum (Bellum Gallicum, Bellum Alexandrinum, Bellum Hispaniense, Bellum Africum)

Files:

**feature_values.csv**: The columns of this file are feature values (i.e. singular, indicative, nominative, etc.), the rows are sections of the Corpus Caesarianum. Each field is the number of times that feature occurs in the text.

**full_data_text_perseus_tokens.csv**: A file containing the tokenized (i.e. word split) version of the corpus caesarianum. The columns come in the following format:
  (line): line number
  commentary: title of commentary (gallic | civil | alexandrine | african | spanish)
  book: book number
  text: source text
  src: CTS URN referencing the work and section
  chapter: chapter number
  tokens: tokenized form of the text

**postagged-texts.csv**: File where each row is a separate word in the Corpus Caesarianum, tagged with the (Universal Dependencies)[https://universaldependencies.org/#language-] scheme.
