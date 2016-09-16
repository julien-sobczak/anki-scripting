#!/usr/bin/env python

"""
Parse the custom XML dictionary using a SAX parser.
"""


import xml.sax
import codecs
import io
import json
import re
import hashlib


def read_frequency_list():
    """
    Read the my_english_frequency_list.csv file and return a dictionary word => rank.
    """
    result = {}
    for line in codecs.open('resources/my_english_frequency_list.csv', 'r'):
        (rank, word) = line.strip().split(',')
        result[word] = int(rank)
    return result


# Global variable to contains the unordered parsed words
words = []

# Global ranking used to assign the rank to each parsed word
ranking = read_frequency_list()


def _hashname(filename):
    filename = filename[0].capitalize() + filename[1:]
    filename = filename.replace(' ', '_')

    return filename

def _wikimedia_hashpath(filename):
    filename = _hashname(filename)
    filename = filename.encode('utf-8')
    m = hashlib.md5()
    m.update(filename)
    hash = m.hexdigest()
    hash1 = hash[0:1]
    hash2 = hash[0:2]
    return hash1 + "/" + hash2


def to_wikimedia_url(filename):
    """
    Convert a simple filename as present in wikipedia pages to a valid URL for downloading.
    @see http://stackoverflow.com/questions/13638579/how-to-construct-full-url-from-wikipedia-file-tag-in-wikimedia-markup
    """
    url = "http://upload.wikimedia.org/wikipedia/commons/" + _wikimedia_hashpath(filename) + "/" + _hashname(filename)
    return url


def to_wikimedia_thumb_url(filename, width):
    """
    Same as #to_wikimedia_url but adapted to images.

    :param filename: the filename as present in the Wikipedia page
    :param width: the requested width (in pixels) for the thumbnail
    :return: a valid URL to download the image at the requested size
    """
    url = "http://upload.wikimedia.org/wikipedia/commons/thumb/" + _wikimedia_hashpath(filename) \
          + "/" + _hashname(filename) + "/" + str(width) + "px-" + _hashname(filename)
    return url


"""
SAX Handler used to extract information from the large input XML file.
Most of the processing happen in the method endElement() after each new word.
"""
class ABContentHandler(xml.sax.ContentHandler):

    def __init__(self):
        xml.sax.ContentHandler.__init__(self)

        # Flag to determine our current position inside the XML file
        self.in_page = False
        self.in_id = False
        self.in_title = False
        self.in_text = False

        # Variables to hold information about the current element
        self.id = None
        self.title = None
        self.text = None

    def startElement(self, name, attrs):
        if name == "entry":
            self.in_page = True
        if self.in_page and name == "id":
            self.in_id = True
        if self.in_page and name == "title":
            self.in_title = True
        if self.in_page and name == "text":
            self.in_text = True
            self.text = ""

    def characters(self, content):
        if self.in_title:
            # The method characters could be called multiple times for the same <title> element
            # So, we need to concatenate the values
            if self.title is None:
                self.title = ""
            self.title += content
        elif self.in_id:
            if self.id is None:
                self.id = ""
            self.id += content
        elif self.in_text:
            if self.text is None:
                self.text = ""
            self.text += content

    def endElement(self, name):
        """
        Hook called after each end tag </title>, </text>, </entry>.
        :param name: the name of the closing tag
        """

        if name == "entry":  # Finish reading the word!
            self.in_page = False

            # Process a new word as soon as the word is read
            self._parseWord()
            #import sys
            #sys.exit(1)

            self.title = None
            self.id = None
            self.text = None

        if self.in_page and name == "title":
            self.in_title = False
        if self.in_page and name == "id":
            self.in_id = False
        if self.in_page and name == "text":
            self.in_text = False

    def _parseWord(self):
        # We parse the new word and store the result inside the global variable
        global words

        print("%s: %s" % (self.id, self.title))

        # Parse the wiki
        properties = self._parseWiki(self.text)

        # Add common properties
        properties['id'] = self.id
        properties['rank'] = ranking[self.title]
        properties['title'] = self.title

        # Post-processing
        images = self._parseImages(self.text)
        if images:
            properties['images'] = images
        if 'translations' in properties:
            properties['translations'] = list(set(properties['translations']))
        if 'audio' in properties:
            audio_url = to_wikimedia_url(properties['audio'])
            properties['audio_url'] = audio_url

        # Add the new word
        words.append(properties)

    def _parseWiki(self, text):
        """
        Parse the content of the tag <text> and delegate to the previously defined methods.
        :param text: the character text inside the tag
        :return a dictionary containing all the extract information about the word
        """
        buf = io.StringIO(text) # to read line by line

        section_paths = [] # Answer the question: Where are we inside the doc?
        sections = []      # All identified relevant sections will be added inside this list

        # Many section are not relevant for us (ex: ===Number===).
        keep_text_for_section = [
            "===Pronunciation===",
            "===Noun===",
            "====Noun====",
            "===Verb===",
            "====Verb====",
            "===Pronunciation===",
            "====Pronunciation====",
            "===Pronoun===",
            "====Pronoun====",
            "===Preposition===",
            "====Preposition====",
            "===Prefix===",
            "====Prefix====",
            "===Particle===",
            "====Particle====",
            "===Noun===",
            "====Noun====",
            "===Interjection===",
            "====Interjection====",
            "===Determiner===",
            "====Determiner====",
            "===Conjunction===",
            "====Conjunction====",
            "===Adverb===",
            "====Adverb====",
            "===Adjective===",
            "====Adjective===="
            "===Article===",
            "====Article====",
            "====Synonyms====",
            "=====Synonyms=====",
            "====Translations====",
            "=====Translations=====",
        ]

        # Buffer containing the text of the current section
        current_section_text = ""
        # Name of the current section that will be the previous section as soon as a new one is found
        last_section = None
        # Should we ignore the text of the current section
        skip = False

        while True:
            line = buf.readline()
            if not line: # EOF
                break
            line = line.strip()

            if line.startswith("=="):  # New section found
                current_section = line

                last_section = None
                if section_paths:
                    last_section = section_paths[-1]

                # Previous section should be kept?
                if not skip and last_section in keep_text_for_section:
                    sections.append({"type": last_section.strip(' ='), "text": current_section_text})
                    current_section_text = ""

                # Is the section more high-level than the previous one?
                while section_paths and section_paths[-1].count('=') >= current_section.count('='):
                    section_paths.pop()  # Go up one level

                if not line.startswith("===="):  # Reset skip flag when encounter a new top level (ex: ===Verb===)
                    skip = False

                # Register the current section
                section_paths.append(current_section)

                # Stop when we encounter a top level section concerning another language
                if not section_paths[0].startswith("==English=="):
                    # Optimization
                    break

                # Stop when we encounter a new etymology
                # (the first one is often the only one pertinent when learning a new language)
                m = re.search('===Etymology (\d+)===', current_section)
                if m:
                    number = int(m.group(1))
                    if number > 1:
                        skip = True

            elif not skip:  # Inside a section => collect the text
                # Should we save the text of the current section?
                if section_paths and section_paths[-1] in keep_text_for_section:
                    current_section_text += line + "\n"

        # All relevant section text is now extracted. We will parse them individually and store the information
        # inside this variable
        result = {"types": []}

        for section in sections:

            if section['type'] == "Pronunciation":
                self._parsePronunciationBlock(section, result)

            if section['type'] == "Noun":
                self._parseDefinitionBlock(section, result, 'Noun')

            if section['type'] == "Verb":
                self._parseDefinitionBlock(section, result, 'Verb')

            if section['type'] == "Pronoun":
                self._parseDefinitionBlock(section, result, 'Pronoun')

            if section['type'] == "Preposition":
                self._parseDefinitionBlock(section, result, 'Preposition')

            if section['type'] == "Prefix":
                self._parseDefinitionBlock(section, result, 'Prefix')

            if section['type'] == "Particle":
                self._parseDefinitionBlock(section, result, 'Particle')

            if section['type'] == "Interjection":
                self._parseDefinitionBlock(section, result, 'Interjection')

            if section['type'] == "Determiner":
                self._parseDefinitionBlock(section, result, 'Determiner')

            if section['type'] == "Conjunction":
                self._parseDefinitionBlock(section, result, 'Conjunction')

            if section['type'] == "Adverb":
                self._parseDefinitionBlock(section, result, 'Adverb')

            if section['type'] == "Article":
                self._parseDefinitionBlock(section, result, 'Article')

            if section['type'] == "Adjective":
                self._parseDefinitionBlock(section, result, 'Adjective')

            if section['type'] == "Translations":
                self._parseTranslationsBlock(section, result)

            if section['type'] == "Synonyms":
                self._parseSynonymsBlock(section, result)

        return result

    @staticmethod
    def _xwiki2html(text):
        """
        Basic XWiki syntax converter to HTML.
        Example of conversion:
        - Remove link [[octothorpe]]
        - Remove label {{unsupported|#}}
        - Remove comment <!--isn't this \"pound sign\" rather than \"pound\"?-->

        :param text: the raw text (a definition line, a quote, etc)
        :return: the cleaned text.
        """
        text = re.sub(r'<\w*?>.*?</\w*?>', r'', text)            # <ref>url text</ref>
        text = re.sub(r'\[\[([^]]*?\|)+(.*?)\]\]', r'\2', text)  # [[troy weight|troy ounce]]
        text = re.sub(r'\[\[(.*?)\]\]', r'\1', text)             # [[mass]]
        text = re.sub(r'<!--(.*?)-->', r'', text)

        # Some labels are very common (almost all word have the "transitive" or "intransitive" label).
        # To avoid pollute the flashcard, we stripped these labels away.
        common_labels = ["countable", "uncountable", "transitive", "intransitive"]
        # Some labels are not easy to display correctly (ex: {{en|familiar|_|or|_new}}
        # For simplicity, we ignore all labels in one of the following words is included among them
        forbidden_strings = ["with", "or", "the", "of", "_", "and", "outside"]
        # Try these substrings too
        forbidden_substrings = ["'''", "AAVE", "by ", "in "]

        # Labels, act I: {{label|en|sland}}
        for matching_label in re.findall("\{\{label[|]en[|].*?\}\}", text):
            index_open = matching_label.find("{{")
            index_close = matching_label.find("}}", index_open)
            labels = matching_label[index_open + 2:index_close].split('|')[2:]

            filtered_labels = []
            filtered = False

            for label in labels:
                if label in forbidden_strings:
                    filtered = True

                for substring in forbidden_substrings:
                    if substring in label:
                        filtered = True

            if not filtered:
                filtered_labels = [item for item in labels if item not in common_labels]

            if filtered_labels: # Maybe all filtered labels are common?
                text = text.replace(matching_label, '(' + ', '.join(filtered_labels) + ')')
            else:
                text = text.replace(matching_label, '')

        # Labels act II: the remaining labels {{...}}, {{ux|Value to preserve}}, ...
        for matching_label in re.findall("\{\{.*?\}\}", text):
            if '|' not in matching_label: # Ex: {{...}}, {{,}}
                text = text.replace(matching_label, matching_label[2:-2])
                continue
            lindex = matching_label.find('|')
            rindex = matching_label.rfind('|')
            name = matching_label[2:lindex]
            value = matching_label[rindex + 1:-2]
            if name in ["l", "ux", "non-gloss definition"]:
                # No need to enclose the label value (follow Wiktionary semantic)
                pass
            else: # Surrounds with parenthesis (follow Wiktionary semantic)
                value = '(' + value + ')'
            text = text.replace(matching_label, value)

        return text.strip()

    @staticmethod
    def _highlight_term(text):
        """
        Search the word inside the text (already enclosed with ''' in wiki syntax) and surround it with <em> tag.
        """
        return re.sub(r"'''(.*?)'''", r'<em>\1</em>', text)

    def _parseDefinitionBlock(self, section, result, type):
        """
        Parse a definition block containing multiple heterogeneous line types:
        - definition when the line starts with #
        - quotation source when the line starts with #* (ignore this line)
        - quote when the line starts with #:
        - quote label when the line starts with #: {{label
        :param section: the section dictionary created when parsing the <text> tag
        :param result: the word's dictionary to group all extracted information
        :param type: the type of word for this block definition (Article, Noun, Verb, etc)
        """

        # We are parsing the i-th definition inside this block
        i = -1
        definitions = {"type": type, "definitions": []} # will contains all extracted definitions

        adding = True  # Set False to ignore a definition
        for line in section['text'].split('\n'):
            line = line.strip()

            if line == "#":  # Empty definition line. (Ex: word 'subsistence')
                # Just ignore it
                continue

            if line.startswith('# '):  # A new definition (nominal case)
                raw_text = self._xwiki2html(line[2:])

                if raw_text.startswith('(') and raw_text.endswith(')') and raw_text.count(')') == 1: # {{misspelling of|too|lang=en}}
                    adding = False
                elif '(rare)' in raw_text or '(obsolete)' in raw_text:
                    adding = False
                else:
                    adding = True
                    i += 1
                    raw_text = self._highlight_term(raw_text)
                    definitions['definitions'].append({ 'text': raw_text, 'quotations': []})

            elif line.startswith('#') and (line[1] == '(' or line[1].isalpha()):
                # A new definition (with the leading space missing)

                # TODO refactor to avoid duplicate code with above conditional
                raw_text = self._xwiki2html(line[1:])

                if '(rare)' in raw_text or '(obsolete)' in raw_text:
                    adding = False
                else:
                    adding = True
                    i += 1
                    raw_text = self._highlight_term(raw_text)
                    definitions['definitions'].append({ 'text': raw_text, 'quotations': []})

            elif line.startswith('#* ') and adding:  # A quotation source
                # 2 possibilities:
                # - Label (quote present in the 'passage' attribute). Ex:
                #     {{quote-book|author=Jon Galloway|title=Professional ASP|passage=User...}}
                # - Plain-text (quote present in the next line prefixed by '#*:'). Ex:
                #     '''2004''', Paul Baker, ''Fanatabulosa: A Dictionary of Polari and Gay Slang'', page 1
                quote_book = self._getQuoteBook(line)
                if quote_book:  # First case
                    definitions['definitions'][i]['quotations'].append(self._highlight_term(quote_book))
                else:  # Second case: ignore the source information and wait for the quote text on the next line
                    pass
            elif line.startswith('#*: ') and adding:  # Quotation text (see second case above)
                quote = self._highlight_term(self._xwiki2html(line[4:]))
                definitions['definitions'][i]['quotations'].append(quote)
            elif line.startswith('#: ') and adding:  # Quotation text (happens when there is no line with the quotation source)
                # Line follows the format (#: ''quote'')
                # Could not use strip() because quote could begin with '''''word''' is a ..''
                line = line[3:]
                if line.startswith("''"):
                    line = line[2:]
                if line.endswith("''"):
                    line = line[:-2]
                quote = self._highlight_term(self._xwiki2html(line))
                definitions['definitions'][i]['quotations'].append(quote)

        result['types'].append(definitions)  # Add the definition to the main object

    def _getQuoteBook(self, line):
        """
        Extract the quotation for line beginning with "{{quote-".
        Ex: {{quote-book|passage=...}}, {{quote-magazine|passage=...}}
        :param line: the raw line contennt (without the #: prefix)
        :return: the content of the attribute 'passage' (the quote)
        """
        if "{{quote-" in line:
            content = line[line.find("{{") + 2:line.find("}}")]
            for key_value in content.split('|'):
                if key_value.startswith("passage="):
                    return key_value[len("passage="):]
        else:
            return None

    def _parseTranslationsBlock(self, section, result):
        """
        Parse a "===Translations===" block text to extract only the french translations.
        :param section: the raw section text
        :param result: the word's dictionary to complete
        """
        if 'translations' in result:  # Probably another etymology
            return

        translations = []

        # Translations are split into different meaning
        # That could represent a lot of translations, so we week only the first meaning translation
        first_translation_block = None
        for line in section['text'].split('\n'):
            if line.startswith("{{trans"):  # New meaning
                if first_translation_block == False:
                    break
                else:
                    first_translation_block = False

            if line.startswith("* French: "):  # Yes, we want french :)
                line_content = line[len("* French: "):]
                # Translations are presented as a succession of label containing the translation in the 3rd part
                for label in re.findall("\{\{.*?\}\}", line_content):
                    parts = label[2:-2].split('|')
                    if len(parts) >= 3:
                        translation = parts[2]
                        translations.append(translation)

        if translations: # Not all word have french translation
            result['translations'] = translations

    def _parseSynonymsBlock(self, section, result):
        """
        Parse a "===Synonyms===" block text to extract only the french translations.
        :param section: the raw section text
        :param result: the word's dictionary to complete
        """
        if 'synonyms' in result:  # Probably another etymology. (ex: ===Etymology 2===)
            return

        synonyms = []
        for line in section['text'].split('\n'):
            if line.startswith("* "):
                line_content = self._xwiki2html(line[2:])

                # Ignore simple reference
                # Ex: (bound paper sheets containing writing) ''See'' '''Wikisaurus:book'''
                if "''See''" in line_content:
                    continue

                # Ignore reference to Wikisaurus
                # Ex: See also Wikisaurus:automobile
                if "Wikisaurus" in line_content:
                    continue

                synonyms.append(line_content)

        if synonyms: # Not all word have synonyms
            result['synonyms'] = synonyms

    def _parsePronunciationBlock(self, section, result):
        """
        Parse a "===Pronunciation===" block text to extract the IPA and audio file.
        :param section: the raw section text
        :param result: the word's dictionary to complete
        """
        for line in section['text'].split('\n'):
            # Ex: {{IPA|/ˈdɪkʃ(ə)n(ə)ɹɪ/|lang=en}}
            if "IPA|" in line and 'ipa' not in result:
                result['ipa'] = line[line.find('/'):line.rfind('/') + 1]

            # Ex: {{audio|en-us-dictionary.ogg|Audio (US)|lang=en}}
            if "{{audio|" in line and 'audio' not in result:
                first_pipe = line.find('|')
                second_pipe = line.find('|', first_pipe + 1)
                result['audio'] = line[first_pipe + 1:second_pipe]

    def _parseImages(self, text):
        """
        Search the whole <text> content to search image links.
        :param text: the full x-wiki text
        :return: the list of images
        """
        images = []

        # Pictures could be present inline through a label
        # Ex: [[Image:Pieni2.jpg|thumb|A hard-cover book]]
        for match in re.findall('\[\[Image:.*?\]\]', text):
            parts = match[len("[[Image:"):-2].split('|')
            filename = parts[0]
            description = parts[-1]
            images.append({
                "filename": filename,
                "description": description,
                "url": to_wikimedia_url(filename),
                "thumb_url": to_wikimedia_thumb_url(filename, 600),
            })

        # Pictures could be present on dedicated line inside a <gallery>  tag
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith("Image:"):

                parts = line[len("Image:"):].split('|')
                filename = parts[0]
                description = parts[-1]
                images.append({
                    "filename": filename,
                    "description": description,
                    "url": to_wikimedia_url(filename),
                    "thumb_url": to_wikimedia_thumb_url(filename, 600),
                })

        return images

if __name__ == "__main__":

    # Parse the input file
    xml.sax.parse(
            open("resources/mywiktionary.xml"),
            ABContentHandler())

    # Sort words by frequency rank
    sorted_words = sorted(words, key=lambda k: k['rank'])

    # Dump result to a JSON file
    print("Dumping results...")
    out = codecs.open('resources/mywiktionary.json', 'w', 'utf-8')
    json.dump(sorted_words, out, sort_keys=True, indent=4, separators=(',',':'))
