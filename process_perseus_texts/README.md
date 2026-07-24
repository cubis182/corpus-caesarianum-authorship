# Process Perseus Texts
*Folder for structured, tokenized textual data and code for cleaning and tagging the corpora*

**cicero_text_perseus_tokenized.csv**: Table with each Cicero text in the corpus in plaintext. Each row is a new section and contains both the original text and pre-tokenized text processed in *process_que_terms.py*. The tokenization is performed to prepare the data for Stanza, which struggled to separate -que on its own.

**full_data_text_perseus_tokenized.csv**: Table with each Caesar work in plaintext. Same format as Cicero: each row is a new section and contains both the original text and pre-tokenized text processed in *process_que_terms.py*. The tokenization is performed to prepare the data for Stanza, which struggled to separate -que on its own.

**full_data_text_perseus.csv**: Table with each Caesar work in plaintext, exactly as extracted by corpus_caesarianum_scraper.ipynb.

**identify-mistokenized-ne.ipynb**: Notebook for exploring words ending in *-ne*, as the *process_que_terms.py* script was treating *-n(e)* as an enclitic in many inappropriate situations, such as in *multitudine*, *divine*, or *flamen*.

**latincy_processor_variants.py**: Includes custom processors for various tasks in the Stanza pipeline. Processors that can be replaced in Latin are the tokenizer, multi-word tokenizer, POS tagger, morphology tagger, lemmatizer, and dependency parser. [Stanza's documentation](https://stanfordnlp.github.io/stanza/pipeline.html#processor-variants) discusses the process in more detail, although examples using the custom pipeline are not included. This code is not to be run independently. Importing the `ProcessorVariant` into another Python script activates them, so that they can be referred to by name in the Pipeline's processor argument.

**latincy_tests.ipynb**: Uses the processor variants from *latincy_processor_variants.py* and tests their results against Stanza's default processors.

**postag_perseusDL.py**: This script serves two purposes. First, the `csv_postag()` function handles parsing the tokenized CSV files in this folder with Stanza and outputting the results to the *postagged* folder. Second, the `select_random()` function engages a command-line interface for reviewing words from the corpus. Words are selected from the corpus randomly to give as representative a sample as possible. The only adjustment made to pure randomness is re-randomizing until the all the variables we study are represented at least once. This way, rare features don't escape analysis. The random selection pulls the same number from each document (which is the whole document for short works, and book-by-book otherwise), ensuring each text is represented. The user enters whether each feature is correct, incorrect, or 'NA' if the feature isn't applicable to the word. If the parent word is correct, `parent_form` is marked as correct; all other parent fields are judged based on the accuracy of the parent word, not whether it is the correct parent in the first place. If unfamiliar with the concept of syntactic parents and trees, see Abeillé 2003. For Latin specifically, see Bamman and Crane 2006 for a shorter overview of their design and significance, and Bamman et al. 2007 for the Perseus Latin Dependency Treebank guidelines as an example.

**process_que_terms.py**: Handles tokenization using CLTK 1.121.0, given the lackluster results with Stanza. Because it uses an older version of the CLTK, python 3.7 is required.

**que stoplist.txt**: A brief list of ambiguous terms ending in -que

**sallust_text_perseus_tokenized.csv**: A table witheach Sallust work in plaintext, in the same format as Cicero and Caesar. Each row is a new section and contains both the original text and pre-tokenized text processed in *process_que_terms.py*. The tokenization is performed to prepare the data for Stanza, which struggled to separate -que on its own.

Anne Abeillé, ed. Treebanks: Building and Using Parsed Corpora. Vol. 20. Text, Speech and Language Technology. Kluwer Academic Publishers, 2003.

Bamman, David, and Gregory Crane. “The Design and Use of a Latin Dependency Treebank.” In Proceedings of the Fifth Workshop on Treebanks and Linguistic Theories, edited by Joakim Nivre and Jan Hajic. 2006.

Bamman, David, Passarotti, Marco, Gregory Crane, and Savina Raynaud. Guidelines for the Syntactic Annotation of Latin Treebanks (v1.3). Tufts Digital Library, 2007. https://github.com/PerseusDL/treebank_data/blob/master/v1/latin/docs/guidelines.pdf.




