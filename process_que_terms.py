import pandas as pd
from cltk.corpus.utils.importer import CorpusImporter
from cltk.tokenize.word import WordTokenizer

# DL the latin model if not already in possession
corpus_importer = CorpusImporter("latin")
corpus_importer.import_corpus("latin_models_cltk")

# Load data
df = pd.read_csv("full_data_text_perseus.csv", sep="|", index_col=0)

# Init tokenizer
tokenizer = WordTokenizer("latin")

# Tokenize
def tokenize(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    return " ".join(tokenizer.tokenize(str(text)))

df["tokens"] = df["text"].apply(tokenize)

# Save 
df.to_csv("full_data_text_perseus_tokenized.csv")

print(f"Done. {len(df)} rows tokenized.")
print(df[["text", "tokens"]].head(2).to_string())