"""
Parse a XML wiktionary dump using a SAX parser (humongous file!).
Produces another smaller XML files containing only the english words with their id and the full text. (4 GB => 400 MB)
By default, only words present in the previous frequency list (resource/my_english_frequency_list.csv) are included.
@see https://dumps.wikimedia.org/backup-index.html
"""

import xml.sax
import codecs


duplicates = {}


class ABContentHandler(xml.sax.ContentHandler):

    def __init__(self, frequency_list=None):
        xml.sax.ContentHandler.__init__(self)
        self.frequency_list = frequency_list

        # Flag to determine our current position inside the XML file
        self.in_page = False
        self.in_id = False
        self.in_title = False
        self.in_text = False

        # Variables to hold informations about the currently processed element
        self.id = None
        self.title = None
        self.text = None

        # Counter to count the number of english word found
        self.filtered_words = 0
        self.all_words = 0

    def startElement(self, name, attrs):
        if name == "page":
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
            self.title = content
            # Give feedback to user
            print("%s... [%s/%s]" % (self.title, self.filtered_words, self.all_words))
        elif self.in_id:
            self.id = content
        elif self.in_text:
            self.text += content

    def _append_word(self):
        global output_file
        self.filtered_words += 1
        if self.frequency_list:
            self.frequency_list[self.title] = True
        output_file.write("  <entry>\n")
        output_file.write("    <id>%s</id>\n" % self.id)
        output_file.write("    <title>%s</title>\n" % self.title)
        output_file.write("    <text xml:space=\"preserve\"><![CDATA[\n")
        output_file.write("%s\n" % self.text)
        output_file.write("    ]]></text>\n")
        output_file.write("  </entry>\n")

    def _mark_as_duplicate(self):
        global duplicates
        if self.title not in duplicates:
            duplicates[self.title] = []
        duplicates[self.title].append(self.id)

    def endElement(self, name):
        if name == "page":
            self.in_page = False
            self.all_words += 1

            # Remove non-english words
            # Remove category title (ex: Index:Spanish)
            # Remove words beginning by an Uppercase BUG
            # Remove uncommon words
            if "==English==" in self.text[:200] \
                    and ":" not in self.title \
                    and self.title != self.title.title():

                if not self.frequency_list:
                    self._append_word()
                elif self.title in self.frequency_list:
                    if self.frequency_list[self.title]:  # Previously found?
                        self._mark_as_duplicate()
                    else:
                        self._append_word()

        if self.in_page and name == "title":
            self.in_title = False
        if self.in_page and name == "id":
            self.in_id = False
        if self.in_page and name == "text":
            self.in_text = False


def main(source_filename, frequency_list):
    """ Entry point. """
    source = open(source_filename)
    xml.sax.parse(source, ABContentHandler(frequency_list))


if __name__ == "__main__":

    # (Optional) Read the frequency to filter the words
    frequency_list = {}
    for line in codecs.open("my_english_frequency_list.csv", "r", "utf-8"):
        (rank, word) = line.strip().split(',')
        frequency_list[word] = False

    output_file = codecs.open("resources/mywiktionary.xml", "w", "utf-8")
    output_file.write("<dictionary>\n")
    main("resources/enwiktionary.xml", frequency_list)
    output_file.write("</dictionary>\n")
    output_file.close()

    # (Optional) Check that we found all the words present in our frequency list
    print("-------------------")
    missing_words = []
    for word, found in frequency_list.items():
        if not found:
            missing_words.append(word)
    print("%s Missing words:\n%s" % (len(missing_words), ', '.join(missing_words)))

    # (Optional) List the duplicate entries
    print("-------------------")
    print("Found %s duplicate(s):" % len(duplicates))
    for duplicate, ids in duplicates.items():
        print("\t- %s (%s)" % (duplicate, ', '.join(ids)))

# Results:
# - 34 307 common words extracted from 615 209 english words among a total of 5 113 338 words.
# - 7445 Missing words
