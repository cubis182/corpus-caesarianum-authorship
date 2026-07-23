from stanza.pipeline.processor import ProcessorVariant, register_processor_variant

# MOVE THE FOLLOWING TO A SEPARATE FILE, AND ADD LEMMATIZATION FUNCTIONALITY
@register_processor_variant("lemma", "latincy")
class latincyLemmatizer(ProcessorVariant):
    """ An alternative lemmatizer that lemmatizes every word to "cool". """

    OVERRIDE = False

    def __init__(self, lang):
        pass

    def process(self, document):
        for sentence in document.sentences:
            for word in sentence.words:
                word.lemma = "cool"

        return document

@register_processor_variant("pos", "latincy")
class latincyPOS(ProcessorVariant):
    """ An alternative lemmatizer that lemmatizes every word to "cool". """

    OVERRIDE = False

    def __init__(self, lang):
        pass

    def process(self, document):
        # get document text
        # use latinCy model for morph tagging, making sure I don't need to use more latinCy processes with it.
        # add the correct features to the correct member variables of the word
        #

        return document