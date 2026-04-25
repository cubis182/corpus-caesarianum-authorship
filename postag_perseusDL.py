# -*- coding: utf-8 -*-

"""
Filename: postag_perseusDL.py
Author: Matthew DeHass
Date: 12/21/2025
Version: 1.0
Description:
    This script includes the functions I use to process the canoncial-latinLit repo.
    The csv_postag function is the main entry point. Using it lets the user extract text from either the whole repository or a specific path and postag/lemmatize it. The results are saved to a CSV

    NOTE HERE ARE SOME ONGOING ISSUES:
    The '/' is used to signal an apex in Cicero's De Re Publica, so "A/strologorum si/gna"

    daturu's es cenam

License: MIT License
Contact: matthew_dehass@yahoo.com

"""
from _csv import Writer
from stanza.models.common.doc import Word

from typing import Any

import os
from copy import deepcopy
import pdfplumber
import re
import regex
import datetime

from lxml import etree  # type: ignore
from lxml.builder import E
from pathlib import Path
from random import choice
import random
import sys

from dotenv import load_dotenv


Y_DENSITY = 4
EMPTY = 4
DEBUG_DIR = "C:/Users/T470s/Documents/GitHub/cltk-2025-atticus"

# directory of the PDFs at the moment
dir = "C:/Users/T470s/Documents/Letters to Atticus/"

# Testing the pdf cleaning functions on Books 1-8 first; here is the PDF
Vol1 = "BOOKS 1-8 Ciceronis, M_ Tulli, Epistulae Ad Atticum_ Vol_ I, Libri I - -- [9783110953831 - Epistulae ad Atticum] Epistulae ad -- Bibliotheca scriptorum.pdf"
Vol2 = "BOOKS 9-16 Ciceronis, M_Tulli, epistulae ad Atticum__ Vol_II, Libri -- [9783110953824 - Epistulae ad Atticum] Epistulae ad -- Bibliotheca scriptorum Graecorum et -- 9783110953824 -- 6452b88664ff783678ce.pdf"


"""
Procedure:

Every page has 'n' number of lines at the end to be removed, from 0 to max page length.

I did 27 trials with the "layout=True" setting on extract_text and y_density=8. In all of them, 
when going from the bottom up, three empty lines in a row or more were always at the boundary
between the body and footer. There were gaps within the footer, but never more than 2.

It appears that the first line with actual text on it is always the header, need
to do more tests.


"""


def save_output(text: str, method: str = "w") -> None:
    """
    Saves text to a file called 'letters-tests.txt'.
    The directory is specified in the DEBUG_DIR at
    the top of the file."""
    with open((DEBUG_DIR + "./letters-tests.txt"), method, encoding="utf-8") as output:
        output.write(datetime.datetime.now().isoformat() + "\n")
        output.write(str(text) + "\n")
        output.close()


def remove_invalid_characters(text: str) -> str:
    """
    Used in the clean_text() function.
    Cleans up the whole string by removing numeric and empty characters"""
    # Remove numeric
    text = re.sub("[0-9]", "", text)

    # Look for hyphens followed by a line break and zero or
    # more spaces/line breaks. After identifying these, all matches.
    text = re.sub("- *\n[\n ]*", "", text)

    # Remove gaps between words bigger than a space
    text = re.sub("[\n ]+", " ", text)

    text = re.sub("\n\n", "", text)

    # TODO Remove pairs of parentheses where one of the two are
    # right next to a letter. In that case, it's usually an
    # emendation NOTE: I realize there might be an issue where
    # the OCR doesn't correctly identify both parentheses, which
    # could cause this type of algorithm to fail. Need to think about
    # this. This might be a step for manual correction

    # NOTE: I'm not removing punctuation, because I want the choice of
    # including or excluding it at the last stage.

    # NOTE TODO adding a line end after the page to make each one
    # fit on a new line, I'm not committed to doing this permanently,
    # though

    # Add a newline character after each sentence for easy reading.
    # The regex doesn't count occurences of common epistolary abbreviations and abbreviated Praenomina.
    # NOTE need to use the regex module instead of re (installed by -m pip install regex).
    # NOTE    The reason for using regex is because the lookbehind assertion is not a fixed width
    split = regex.split(
        "(?<!Prid|prid|Kal|kal|Non|Id|a|d|Ian|Febr|Mart|Apr|Mai|Iun|Quint|Sext|Sept|Oct|Nov|Dec|Nrib|Luc|Agr|Ap|A|K|D|F|C|Cn|L|Mam|M'|M|N|Opet|Post|Pro|P|Q|Sert|Ser|Sex|S|St|Ti|T|Vol|Vop)\\.",
        text,
    )
    text = ".\n".join(split)

    text = re.sub("[-–—'\"”“]", "", text)

    return text


dir_path = Path(__file__)
dir_path = dir_path.parents[0]
sys.path.append(str(dir_path))
os.chdir(dir_path)

# Get the OLLAMA API key
load_dotenv("./ollama.env")
ollama_key = os.getenv("OLLAMA_API_KEY")

# TODO CREATE A TABLE OF CONTENTS FOR ALL THESE NEW FUNCTIONS!!!!

s_xml_template = """
<root xmlns:xsi="http://www.w3.org/2001/XMLSchema">
    <work reviewed="UNREVIEWED">
        <title/>
        <author/>
        <path></path>
        <content type="plaintext"/>
        <content type="postagged"/>
    </work>
</root>
"""

CORPUS = [
    {
        "commentary": "gallic",
        "path": "phi0448/phi001/phi0448.phi001.perseus-lat2.xml",
        "has_books": True,
        "cts_base": "urn:cts:latinLit:phi0448.phi001.perseus-lat2",
    },
    {
        "commentary": "civil",
        "path": "phi0448/phi002/phi0448.phi002.perseus-lat2.xml",
        "has_books": True,
        "cts_base": "urn:cts:latinLit:phi0448.phi002.perseus-lat2",
    },
    {
        "commentary": "alexandrine",
        "path": "phi0428/phi001/phi0428.phi001.perseus-lat1.xml",
        "has_books": False,
        "cts_base": "urn:cts:latinLit:phi0428.phi001.perseus-lat1",
    },
    {
        "commentary": "african",
        "path": "phi0426/phi001/phi0426.phi001.perseus-lat1.xml",
        "has_books": False,
        "cts_base": "urn:cts:latinLit:phi0426.phi001.perseus-lat1",
    },
    {
        "commentary": "spanish",
        "path": "phi0430/phi001/phi0430.phi001.perseus-lat1.xml",
        "has_books": False,
        "cts_base": "urn:cts:latinLit:phi0430.phi001.perseus-lat1",
    },
]

inval_tags = [
    "note",
    "del",
    "head",
    "speaker",
    "sic",
    "bibl",
    "ex",
    "expan",
    #    "corr",
    # "choice",
    "{http://www.tei-c.org/ns/1.0}note",
    "{http://www.tei-c.org/ns/1.0}del",
    "{http://www.tei-c.org/ns/1.0}head",
    "{http://www.tei-c.org/ns/1.0}speaker",
    "{http://www.tei-c.org/ns/1.0}sic",
    "{http://www.tei-c.org/ns/1.0}bibl",
    "{http://www.tei-c.org/ns/1.0}ex",  # When an abbr / expan is given, let's go with the abbreviated form. The reason is given in a comment just under this
    #    "{http://www.tei-c.org/ns/1.0}corr",
    # "{http://www.tei-c.org/ns/1.0}choice",
]

# NOTE For abbreviations, their usage in the Perseus DL is inconsistent. Sometimes <abbr/> surrounds both the abbreviation and the exputf-8on. Other times, the abbreviation is next to the exputf-8on.
# However, the exputf-8ons are consistent, so we'll just get rid of those. I would prefer the expanded forms, but this is cleaner for now.


def is_valid_tag(element: etree._Element) -> int:
    """
    Checks whether a tag from a TEI:XML document is valid. A valid tag is one whose text we want for the purpose of processing the text. A tag like <note> has irrelevant text, so it's invalid. See the inval_tags variable above for a full list
    """
    l: list = list(element.iterancestors(tag=inval_tags))
    boolean = bool(l)
    if boolean:
        return -1
    elif element.tag in inval_tags:
        return 0
    else:
        return 1


def has_tail(element) -> bool:
    try:
        tail = element.tail
        if any(re.search("[A-Za-z0-9]", s) for s in tail):
            return True
        else:
            return False
    except TypeError:
        return False


def get_text(element) -> str:
    """
    This function takes an element and extracts only the plaintext. This is necessary to avoid including text in notes or
    emendations. This also makes sure that text in the tail of one of those invalid tags gets kept and not completely lost.
    """
    string = ""
    sTail: str = element.tail
    sText: str = element.text
    parent: etree._Element = element.getparent()
    #pText: str = parent.text
    pTail: str = parent.tail

    if pTail:
        if has_tail(parent):
            return string

    tagValid = is_valid_tag(element)
    if tagValid == 1:
        if sText:
            string += sText

    # Make sure it has a tail with alphanumeric characters in it and that it isn't inside of an invalid tag
    if (has_tail(element)) and (tagValid == 1):
        children: list = [x for x in element.iterdescendants() if (x.tail or x.text)]
        for child in children:
            if is_valid_tag(child):
                string += ("" if child.text is None else child.text) + (
                    "" if child.tail is None else child.tail
                )
        string += sTail
    elif sTail and tagValid > -1:
        string += sTail

    # DEBUG
    if string == "":
        pass

    if element.tag == "{http://www.tei-c.org/ns/1.0}add":
        pass

    return string


def get_paths() -> list[Path]:
    """
    Returns a list of paths to all Perseus DL Latin texts"""

    # path to PerseusDL
    dir: Path = Path("./../canonical-latinLit/data/")

    # paths to all the files in the corpus, identified by -lat and the .xml extension.
    return list(dir.glob("**/**-lat*.xml"))


def get_title_auth_body(tree: etree._ElementTree | etree._Element) -> dict:
    """ """

    # We need to make sure it's a real TEI file with the xml namespace.
    # Some files in the PerseusDL use TEI without the namespace

    tei: dict = {"tei": "http://www.tei-c.org/ns/1.0"}

    # First, assume no namespace
    expression: str = ".//body"

    # XPath expression for the title
    # TODO Debug this title creator; it didn't work for Pro roscio
    title: str = "./teiHeader/fileDesc/titleStmt/title"
    titleString: str = ""

    # XPath expression for the author's name
    author: str = "./teiHeader/fileDesc/titleStmt/author"
    authorString: str = ""

    # However, if there is a namespace with the TEI URI (which is given in the 'tei' variable above), we need a tei namespace declared
    nsmap: list = list(tree.nsmap.values())
    try:
        is_TEI: bool = tei["tei"] == nsmap[0]
    except IndexError:
        is_TEI: bool = False

    body = __run_xpath(expression, is_TEI, tree, tei)

    # We need to test a few things in case the title isn't in the right spot
    titleEl = __run_xpath(title, is_TEI, tree, tei)

    # if titleEl is None:
    #    titleEl = __run_xpath(".//biblStruct/monogr/title", is_TEI, tree, tei)

    authorEl = __run_xpath(author, is_TEI, tree, tei)

    # if authorEl is None:
    #    authorEl = __run_xpath(".//biblStruct//author", is_TEI, tree, tei)

    # If we still don't have a valid author or title node, we give up
    if titleEl is not None:
        titleString = titleEl.text
    else:
        titleString = ""

    if authorEl is not None:
        authorString = authorEl.text
    else:
        authorString = ""

    return {"body": body, "title": titleString, "author": authorString}


def __run_xpath(expr: str, is_tei: bool, tree, tei: dict):
    """
    NEEDSDOC"""

    if is_tei:
        expr = re.sub("/(?=[A-Za-z0-9])", f"/tei:", expr)
        # make sure no namespace is in front of 'text()'
        expr = re.sub("tei:text\\(\\)", "text()", expr)
        elem = tree.find(expr, namespaces=tei)
        return elem
    else:
        elem = tree.find(expr)
        return elem


# Store the path to the file with the results here so its globally accessible
results_file: str = "./postagged-texts.csv"


def open_results() -> etree._ElementTree:
    """
    TODO TEST!
    Returns the root element of the atticus-study-results.xml file"""
    etree.XMLParser(schema=etree.XMLSchema(file="./results-schema.xsd"))
    tree = etree.parse(results_file)
    return tree


def automatic_validation():

    path: str = str(choice(get_paths()))
    with open(path, "r", encoding="utf-8") as file:
        text = __get_body(path)
        tokenized = text.split(" ")

        source: str = str(file.read())
        source = re.sub("\t", "", source)

        source = remove_invalid_characters(source)

        save_output(path + "\n" + ("*" * 25) + "\n\n", "a")

        for i in range(0, 99):
            index = random.randrange(0, len(tokenized))
            final_string = ""
            try:
                final_string = " ".join(tokenized[index : (index + 4)])
            except IndexError:
                final_string = " ".join(tokenized[index:])
            if not final_string in source:
                save_output(final_string, "a")


##############CLASSICAL LANGUAGES TOOLKIT#########################

from cltk.nlp import NLP
import cltk.core.data_types as types
import cltk.morphosyntax.conll as conll


def process_text(text: str, nlp: NLP) -> types.Doc:
    f"""
    Docstring for process_text
    Processes the Perseus DL texts and the Letters to Atticus with the CLTK
    
    :param text: The plaintext for a work, as retrieved from the <content type="plaintext"/> element in the {results_file} file
    :type text: str 
    :param nlp: An NLP for Latin from the CLTK. Added this so it didn't have to create a new parser every time. In theory, could also work with an older version of CLTK before AI backends, although the return type annotation would no longer be valid (I don't believe the 'Doc' datatype is in cltk.core.data_types in the original).
    :type nlp: cltk.nlp.NLP
    :return: Description
    :rtype: NLP from the CLTK for a single work
    """

    doc = nlp.analyze(text)
    return doc


def __get_paths(path):  # -> list[str]:
    """
    This is a helper function to csv_postag which processes the path argument.
    If an argument isn't specified, we need to get the full list.

    :return: NEEDSDOC
    :rtype: list[str]
    """

    # Check whether the path argument was given and whether it's a valid value
    # If the pathArg is rand, that means we select a random path.
    # If the pathArg is the default value, we already got all the paths we need with the get_paths()
    # If we passed a list of paths to pathArg, we replace paths with that list
    if path not in ("", "rand") and not isinstance(path, list):
        return [str(path)]

    if path == "":
        paths: list[str] = [str(x) for x in get_paths()]
        return paths
    elif isinstance(path, list):
        return path
    else:
        raise TypeError


import csv
import shutil


def __get_body(path: str) -> str:
    """
    Helper function for automatic_validation (plan to also incorporate this into
    csv_postag()). This returns the body text for a TEI file

    :param path: A path to a TEI XML file from the Perseus DL
    :type path: str
    """
    parser: etree.XMLParser = etree.XMLParser(resolve_entities=False)
    tree: etree.ElementTree = etree.parse(path, parser)  # Use path 22 for debugging

    # Get the root of the tree. This variable will eventually hold the tei:body element
    body: etree._Element = tree.getroot()

    authority_dict = get_title_auth_body(body)

    body = authority_dict["body"]

    if len(body):
        body = body[0]

    # Now we have the <body> element, let's get the text######################3

    # Add the text for each element, using the get_text() function
    string: str = ""
    for element in body.iter():
        string += get_text(element)

    string = re.sub("\t", "", string)

    s_final_body = remove_invalid_characters(string)
    return s_final_body


def __in_file(string, s: set) -> bool:
    """
    Checks whether a given string is in a file. In this case, it's used in
    csv_postag to check whether a path is already in it.

    :param string: Description
    :param file: Description
    :return: Description
    :rtype: bool
    """

    for l in s:
        if l.find(string) > -1:
            return True

    return False


import stanza


def feats(s: str):
    """
    Helper in csv_postag for getting the stanza features

     :param s: Description
     :type s: str
    """
    l_feats = s.split("|")
    d = {}
    for f in l_feats:
        tok_f = f.split("=")
        d[tok_f[0]] = tok_f[1]
    return d


def select_random(tries=1) -> str:
    """
    Selects a random line from the results_file. This is for the purpose of QA
    Asks the user to QA it.

    :param tries: Description NEEDSDOC
    :return: Description NEEDSDOC
    :rtype: str
    """
    labs = [
        "title",
        "author",
        "cite1",
        "cite2",
        "path",
        "form",
        "lemma",
        "tag",
        "Aspect",
        "Mood",
        "Number",
        "Person",
        "Tense",
        "VerbForm",
        "Voice",
        "Case",
        "PronType",
        "Gender",
        "Polarity",
        "Degree",
        "NumType",
        "Deprel",
        "parent_form",
        "parent_lemma",
        "parent_tag",
        "parent_Aspect",
        "parent_Mood",
        "parent_Number",
        "parent_Person",
        "parent_Tense",
        "parent_VerbForm",
        "parent_Voice",
        "parent_Case",
        "parent_PronType",
        "parent_Gender",
        "parent_Polarity",
        "parent_Degree",
        "parent_NumType",
        "parent_Deprel",
    ]
    with open(results_file, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        lines = [x for x in reader]

        for i in range(0, tries):
            line = choice(lines)

            f.seek(0)
            index = lines.index(line)

            # Get the words around it
            context = ""
            for n in range(index - 8, index + 7):
                context += f"{lines[n][3]} "

            line_text = ",".join(line)
            # Start each with the path and the index in the results file
            return_line: str = f"{line[2]},{index},{context},"
            index_field = 0
            for field in line:

                print(line_text + "\n\n")
                print("Context: " + context)
                print(f"{labs[index_field]}: {field}")
                inp = input(
                    "Please type 'y' if the tag is appropriate, and 'n' if not."
                )
                if inp in ["y", "Y"]:
                    return_line += "1,"
                else:
                    return_line += "0,"

                index_field += (
                    1  # Add to the index of the field so we can get the field label
                )

            with open(
                "./postag-tests.csv", "a", encoding="utf-8", errors="ignore"
            ) as results:
                results.write(
                    return_line[:-1] + "\n"
                )  # Remove the last character, because it's a comma


def csv_postag(path: str | list = "", skip_finished=True) -> None:
    """
    Docstring for csv_postag

    This function takes a path or a list of paths (all strings) and parses all the texts.

    This function relies on the CSV being serialized with commas, not another separation character.

    :param path: An optional path of the file to write manually
    :type path: str
    :param skip_finished: NEEDSDOC
    :type skip_finished: bool
    """
    paths: list = __get_paths(path)

    """
    2026-02-15 11:46:56 INFO: Using device: cpu
    2026-02-15 11:46:56 INFO: Loading: tokenize
    2026-02-15 11:46:59 INFO: Loading: mwt
    2026-02-15 11:46:59 INFO: Loading: pos
    2026-02-15 11:47:01 INFO: Loading: lemma
    2026-02-15 11:47:02 INFO: Loading: depparse
    """
    # Add this so we can use the GPU
    # NOTE !!! USING THE GPU REQUIRED ME TO INSTALL TORCH THROUGH PIP WITH CUDA 11.8 (SEE INSTALL INSTRUCTIONS ON THEIR WEBSITE FOR MORE)
    custom_pipeline = stanza.Pipeline(
        "la", processors="tokenize,mwt,pos,lemma,depparse", use_gpu=True
    )
    # OLD CLTK: nlp = NLP(backend="stanza", custom_pipeline=custom_pipeline)

    sPathsRemoved = []

    # If we want to keep a line, we place it in the temp file.
    with open(
        results_file, "r", encoding="utf-8", errors="replace", newline=""
    ) as f_read:
        s: set = set(f_read.read().splitlines())
        with open(
            "./temp.csv", "w", encoding="utf-8", errors="replace", newline=""
        ) as f_write:
            # If we're skipping already finished ones, lets skip  paths
            # that we're not going to parse
            if skip_finished:
                for p in paths:
                    if __in_file(p, s):
                        sPathsRemoved.append(p)
                        paths.remove(p)
            else:
                wr = csv.writer(f_write)
                f_read.seek(0)  # just to be sure
                read = csv.reader(f_read)
                for l in read:
                    if l[4] not in paths:
                        wr.writerow(l)
        if not skip_finished:
            shutil.copyfile("temp.csv", results_file)
            os.remove("./temp.csv")

    # Get the csv.writer
    with open(results_file, "a", encoding="utf-8", errors="replace", newline="") as f:
        writer: Writer = csv.writer(f, escapechar="#")

        l_paths = len(paths)

        #s_docs = []

        for p in paths:
            i_paths = paths.index(p)

            print(f"Path: {p}")

            print(f"Completion of TEI text extraction: {i_paths}/{l_paths}")
            parser: etree.XMLParser = etree.XMLParser(resolve_entities=False)
            tree: etree.ElementTree = etree.parse(
                p, parser
            )  # Use path 22 for debugging

            # DEBUG
            print(f"TEI file: {etree.tostring(tree).decode('utf-8')[1:300]}")

            # Get the root of the tree. This variable will eventually hold the tei:body element
            body: etree._Element = tree.getroot()

            authority_dict = get_title_auth_body(body)

            body: etree._Element = authority_dict["body"]
            titleString = authority_dict["title"]
            authorString = authority_dict["author"]

            # Remember, when there are potentially Greek characters, we need encoding set to utf-8.
            # This debug file will store the results before the final version of the program

            """debug: io.TextIOWrapper = open(
                "C:/Users/T470s/Documents/GitHub/cltk-2025-atticus/perseus-debug.txt",
                "w",
                encoding="utf-8",
            )
            debug.write(str(p))"""

            # if len(body):
            #    body = body[0]

            # Now we have the <body> element, let's get the text######################3

            # Add the text for each element, using the get_text() function
            string: list[list[str]] = []

            divs: dict[str, str] = {}
            for element in body.iter():

                # Only update the citation if it's a div
                # Have to use find because element.tag includes the namespace
                if element.tag.find("div") > -1:
                    if element.get("subtype") is not None:
                        typ = element.get("subtype")
                    elif element.get("type") is not None:
                        typ = element.get("type")
                    else:
                        print("Error! shouldn't have gotten a citation here")
                        typ = "unk"

                    n = element.get("n")
                    divs[typ] = n

                string.append([",".join(divs.values()), get_text(element)])

            string_process_export(body_text=string, author=authorString, title=titleString, custom_pipeline=custom_pipeline, path=p, writer=writer)


def string_process_export(body_text: list[list[str]], author: str, title: str, custom_pipeline: stanza.Pipeline, path: str, writer: Writer):
    """
    This function takes a section from the Corpus Caesarianum and parses it using stanza, writing the results to postagged-texts.csv

    :

    """

    # Run the Stanza process for each section.
    for section in body_text:
        raw = section[1]
        s_final_body = re.sub("\t", "", raw)

        s_final_body = remove_invalid_characters(s_final_body)

        cite = section[0].split(",")

        # s_docs.append(s_final_body)

        # now that we have the TEI XML, let's parse the body text
        # OLD CLTK: doc = process_text(s_final_body, nlp)
        t1 = datetime.datetime.now()
        # in_docs = [stanza.Document([], text=d) for d in s_docs] # Wrap each document with a stanza.Document object
        out_docs = custom_pipeline(
            s_final_body
        )  # Call the neural pipeline on this list of documents
        print(f"Pipeline took {(datetime.datetime.now() - t1).seconds} seconds")

        for s in out_docs.sentences:
            for word in s.words:
                print(f"Word Completion: {s.words.index(word)}/{len(s.words)}")
                # Skip most punctuation that doesn't break sentences
                if word.upos != "PUNCT" or word.text in [".", "!", "?"]:
                    # Old CLTK version: s_form = word.string
                    s_form = word.text

                    s_lemma = word.lemma

                    # Get the tag
                    # OLD CLTK: tag = word.upos.tag
                    tag = word.upos

                    #dependency relation
                    deprel = word.deprel

                    #parent word
                    parent = get_parent(word)


                    try:
                        s_parent_form = parent.text

                        s_parent_lemma = parent.lemma

                        s_parent_tag = parent.upos

                        parent_deprel = parent.deprel
                    except AttributeError:
                        s_parent_form = ""

                        s_parent_lemma =""

                        s_parent_tag = ""

                        parent_deprel = ""

                    # Only get the features we're interested in

                    f_set = [
                        "Aspect",
                        "Mood",
                        "Number",
                        "Person",
                        "Tense",
                        "VerbForm",
                        "Voice",
                        "Case",
                        "PronType",
                        "Gender",
                        "Polarity",
                        "Degree",
                        "NumType",
                    ]

                    features = extract_features(word, f_set)

                    parent_features = extract_features(parent, f_set)

                    # Start putting together the line to write
                    metadata = [
                        title,
                        author,
                        cite[0],  # The outermost citation number (books, or sections for Hisp.)
                        ".".join(cite[1:]),  # The rest of the citation number
                        path,
                        s_form,
                        s_lemma,
                        tag,
                    ]  # NOTE: Not only metadata, but also includes the word and the tag

                    to_write = metadata + [
                        features[x] for x in f_set
                    ]  # This didn't need to be a dictionary, but it helps to know that I will always do this in the same order

                    to_write.append(
                        deprel
                    )  # Add the dependency relation to the end

                    #put all the info about the parent word in a list
                    parent_info: list[str] = [
                        s_parent_form,
                        s_parent_lemma,
                        s_parent_tag
                    ] + [
                        parent_features[x] for x in f_set
                    ] + [
                        parent_deprel
                    ]

                    #put the prefix "parent"
                    for i, val in enumerate(parent_info):
                        if val:
                            parent_info[i] = "parent_" + val
                        else:
                            parent_info[i] = ""

                    to_write = to_write + parent_info

                    writer.writerow(to_write)

def get_parent(word: Word) -> Word | None:
    """
    Get the parent of a target word. Returns None if there is no root.
    """
    sent = word.sent

    parent_id: int = word.head

    #find word with the correct id
    for w in sent.words:
        if w.id == parent_id:
            return w

    return None



def extract_features(word, f_set: list[Any]) -> dict[Any, Any]:
    """
    This function takes a Stanza word and a list of features and returns their values.

    :param f_set: list of features
    :param word: A Stanza word with Universal Dependencies features
    """


    features = {}
    try:
        # OLD CLTK: w_features = word.features.features
        w_features = feats(
            word.feats
        )  # added for new stanza backend
        for key in f_set:
            try:
                # OLD CLTK: features[key] = __proc_feature(
                #    [val.value for val in w_features if val.key == key]
                # )
                if w_features[key]:
                    features[key] = w_features[key]
                else:
                    features[key] = ""
            # The next two lines are superfluous, it seems, as we never get a KeyError, but I'll leave them for now
            except KeyError:
                features[key] = ""
    # Some words don't have features, so Python will throw an Attribute Error.
    except AttributeError:
        for key in f_set:
            features[key] = ""
    return features


def __proc_feature(feature):
    if not feature:
        return ""
    else:
        return str(feature[0])


def modify_titles():
    """
    This function goes back through and makes changes to titles
    Currently, it just works with Ab Urbe Condita
    DOESN'T WORK AT THE MOMENT. I should fix it to match the regex ^"Ab.*?" and replace that with "Ab urbe condita" (no quotes)
    """
    with open(results_file, "r+", encoding="utf-8", errors="ignore") as f:
        f.seek(0)  # Just to be sure...
        lines = f.readlines()

        f.truncate()

        livy = "ab urbe condita"

        for l in lines:
            if (l.casefold()).find(livy):
                # If this is Livy, replace everything before the first comma with "ab urbe condita"
                lines[lines.index(l)] = livy + l[l.find(",") :]
            f.write(f"{l}\n")


##################################################################


def get_sections(body: etree._Element) -> dict:
    """
    This function returns a dictionary of section numbers and text given a body of a TEI XML file
    """
    pass


if __name__ == "__main__":
    """
    Note: This module uses Stanza. It comes with Torch, but the default installation didn't allow my computer to use CUDA for processing. I installed Torch again manually with CUDA 11.8 and it worked. See the homepage of Torch for more info

    POTENTIAL ISSUES:
    - Works are identified by path. If you switch to a different directory or computer, the algorithm would cease to recognize any
    """

    ############################33
    # How to use:

    # If you're postagging, use the csv_postag() function. If you just want to postag the whole library and replace whatever is left, use it like this:
    #       csv_postag(path="", skip_finished=False)
    # You can also pass a list of custom paths, which can be relative or absolute paths. The paths can be strings or pathlib.Path objects

    # The get_paths() function retrieves a list of all the paths, but it does assume that the python script's parent folder is in the same directory as the canoncial-latinLit repo
    # So, you could do the following:
    #       csv_postag(path=get_paths(), skip_finished=False)

    # The param skip_finished is there for the purpose of speeding up the process.
    # If you want to postag something that hasn't bee postagged yet, you can skip the process of checking whether it's already been done. This is the default behavior.

    # For the purpose of QA, I've also added the function "select_random" which selects a random postagged word, presents it to be checked, and saves whether each field was correct or incorrect.
    # I WOULD NOT recommend using this, just because I was pretty lazy designing it. Anything other than "y" or "Y" is interpreted as the parsing being incorrect, requiring you to modify the CSV manually every time you make a mistake.

    prefix = "./../canonical-latinLit/data/"

    caesar = [
        f"{prefix}phi0448/phi001/phi0448.phi001.perseus-lat2.xml",
        f"{prefix}phi0448/phi002/phi0448.phi002.perseus-lat3.xml",  # using later edition, lat3 instead of lat2
        f"{prefix}phi0428/phi001/phi0428.phi001.perseus-lat1.xml",
        f"{prefix}phi0426/phi001/phi0426.phi001.perseus-lat1.xml",
        f"{prefix}phi0430/phi001/phi0430.phi001.perseus-lat1.xml",
    ]

    csv_postag(
        path=caesar[1:],
        skip_finished=False,
    )

