import spacy
from stanza.pipeline.processor import ProcessorVariant, register_processor_variant
from stanza.pipeline.lemma_processor import LemmaProcessor

class LatincyError(Exception):
    pass

# MOVE THE FOLLOWING TO A SEPARATE FILE, AND ADD LEMMATIZATION FUNCTIONALITY
@register_processor_variant("lemma", "latincy")
class LatincyLemmatizer(ProcessorVariant):
    """ An alternative lemmatizer that lemmatizes every word to "cool". """

    OVERRIDE = True

    def __init__(self, lang):
        import spacy

        # Load spaCy with all processors but the relevant ones disabled
        self.nlp = spacy.load("la_core_web_lg")  # , enable=["lemmatizer",])

    def process(self, document):
        from spacy.tokens import Doc

        # get document text
        text = [i.text for i in document.iter_tokens()]

        # use latinCy model for morph tagging, making sure I don't need to use more latinCy processes with it.
        # NOTE: The original example used `nlp = spacy.blank('<lang>'), so that might have to change
        spacy_doc: Doc = Doc(self.nlp.vocab,
                             words=text)  # Not including spaces, as the original doesn't account for that

        # add the correct features to the correct member variables of the word
        # Note that spacy.tokens.Doc can be passed directly to nlp again
        if len(spacy_doc) != document.num_tokens:
            raise LatincyError(
                f"Spacy doc of length {len(spacy_doc)} is not equal to original Stanza document of length {document.num_tokens}")

        # process the document
        spacy_doc = self.nlp(spacy_doc)

        for index, word in enumerate(document.iter_words()):
            word.lemma = spacy_doc[index].lemma_

        return document


@register_processor_variant("pos", "latincy")
class LatincyPOS(ProcessorVariant):
    """ Alternative Latincy lemmatizer for Stanza. """

    OVERRIDE = True

    def __init__(self, lang):
        import spacy

        # Load spaCy with all processors but the relevant ones disabled
        self.nlp = spacy.load("la_core_web_lg")#, enable=["tagger", "parser", "morphologizer",])

    def process(self, document):
        from spacy.tokens import Doc

        # get document text
        text = [i.text for i in document.iter_tokens()]

        # use latinCy model for morph tagging, making sure I don't need to use more latinCy processes with it.
        # NOTE: The original example used `nlp = spacy.blank('<lang>'), so that might have to change
        spacy_doc: Doc = Doc(self.nlp.vocab, words=text) # Not including spaces, as the original doesn't account for that

        # add the correct features to the correct member variables of the word
        # Note that spacy.tokens.Doc can be passed directly to nlp again
        if len(spacy_doc) != document.num_tokens:
            raise LatincyError(f"Spacy doc of length {len(spacy_doc)} is not equal to original Stanza document of length {document.num_tokens}")

        # process the document
        spacy_doc = self.nlp(spacy_doc)

        # Add `xpos` and `feats` to the original document
        for index, word in enumerate(document.iter_words()):
            word.upos = spacy_doc[index].pos_
            word.feats = str(spacy_doc[index].morph.to_json())

            print(word.feats)

            # CompositeVocab in stanza.models.common requires this format if it's empty
            if word.feats == '':
                word.feats = '_'

        return document