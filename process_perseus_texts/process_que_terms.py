#Note: requires Python 3.7, cltk 1.x
import pandas as pd
from cltk.corpus.utils.importer import CorpusImporter
from cltk.tokenize.latin.word import WordTokenizer
from cltk.tokenize.latin.params import latin_exceptions

# MD 7/3/2026: We need to add more exceptions to tokenization with '-ne'
#   The tokens are idenitified by looking at each instance of -ne
#   See identify-mistokenized-ne.ipynb for more detail on the process

addtl_caesar = [
    "aviene",
    "calydone",
    "cicerone",
    "domitione",
    "gobannitione",
    "libone",
    "mithridaten",
    "pharnacen",
    "pharone",
    "puleione",
    "serapione",
    "thapsone",
    "varrone",
    "verticone",
    "vibone",
    "vorene",
    "adfirmatione",
    "aestimatione",
    "altitudine",
    "animadversione",
    "aversione",
    "carne",
    "cohortatione",
    "collatione",
    "collocatione",
    "commendatione",
    "communicatone",
    "communicatione",
    "commutatione",
    "compositione",
    "conclamatione",
    "conclusione",
    "confirmatione",
    "coniuratione",
    "contemptione",
    "contignatione",
    "contione",
    "cothone",
    "crassitudine",
    "cunctatione",
    "deditione",
    "defectione",
    "denuntatione",
    "desperatione",
    "dimicatione",
    "dominatione",
    "eruptione",
    "regione",
    "sene",
    "munitione"
]

addtl_exceptions_cicero = [
    "scipione",
    "exercitatione",
    "consuetudine",
    "disputatione",
    "caepione",
    "lubidine",
    "nuntiatione",
    "flamene",
    "flamine",
    "oblivione",
    "occasione",
    "fuligine",
    "magnitudine",
    "sollicitudine",
    "excusatione",
    "valetudine",
    "promulgatione",
    "remissione",
    "nonne",
    "reclamatione",
    "multitudine",
    "discessione",
    "suspicione",
    "retractatione",
    "moderatione",
    "congressione",
    "supplicatione",
    "consolatione",
    "defetigatione",
    "defatigatione",
    "inscriptione",
    "simulatione",
    "reversione",
    "offensione",
    "dubitatione",
    "sectione",
    "apricatione",
    "lentone",
    "necessitudine",
    "excursione",
    "recusatione",
    "cognitione",
    "dissensione",
    "tamen",
    "carbone",
    "auctione",
    "sentionone",
    "sentione",
    "coniunctione",
    "admixtione",
    "meditatione",
    "direptione",
    "colluvione",
    "solone",
    "recordatione",
    "postulatione",
    "centone",
    "narbone",
    "leptine",
    "latrone", 
    "nundinatione",
    "oratione",
    "similitudine",
    "significatione",
    "defensione",
    "remuneratione",
    "correctione",
    "delectatione",
    "divine",
    "tuberone",
    "contione",
    "exstructione",
    "opinione",
    "contentione",
    "pisone",
    "applicatione",
    "circumscriptione",
    "gratulatione",
    "exceptione",
    "retardatione",
    "legatione",
    "cogitatione",
    "turpione",
    "curione",
    "pactione",
    "coversione",
    "turpitudine",
    "solitudine",
    "lectione",
    "praedicatione",
    "perturbatione",
    "mansuetudine",
    "petitione",
    "venditione",
    "charybdine",
    "scatone",
    "imitatione",
    "navigatione",
    "vicissitudine",
    "flamene",
    "consensione",
    "calene",
    "approbatione",
    "admiratione",
    "conversione",
    "myrmillone",
    "glabrione",
    "nominatione",
]

failed_token_split = [
    "—"
]

# DL the latin model if not already in possession
corpus_importer = CorpusImporter("latin")
corpus_importer.import_corpus("latin_models_cltk")

# Load data
df = pd.read_csv("full_data_text_perseus.csv", sep="|", index_col=0)

# Init tokenizer
tokenizer = WordTokenizer()

# Tokenize
def tokenize(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    text = text.replace("—", " ")
    return " ".join(tokenizer.tokenize(str(text), enclitics_exceptions=latin_exceptions + addtl_caesar + addtl_exceptions_cicero))

df["tokens"] = df["text"].apply(tokenize)

#MD 6/2/2026: Added to separate Cicero from Caesar
caesar = df[df['commentary'].isin(['gallic', 'civil', 'spanish', 'alexandrine', 'african'])]
cicero = df[df['commentary'].isin(['amicitia', 'senectute', 'philippics'])]

# Save 
caesar.to_csv("full_data_text_perseus_tokenized.csv")
cicero.to_csv("cicero_text_perseus_tokenized.csv")

print(f"Done. {len(df)} rows tokenized.")
print(df[["text", "tokens"]].head(2).to_string())