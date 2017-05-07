#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert and load the file "false-friends-FR-EN.xwiki to Anki.
"""

class Word:
    """
    One entry in the input document.
    """

    def __init__(self, en_line):
        """
        Initialize a new word from the first line of its definition.
        The line should not contains the xWiki prefix "* ".
        Ex: "''vest'' (n) : 1/ maillot de corps ; 2/ (amér.) gilet"
        """
        self._parse_en_line(en_line)
        self.fr_words = []

    def _parse_en_line(self, en_line):
        # ''vessel'' (n) : 1/ vaisseau ; 2/ bouteille (d’air comprimé)
        #print(">" + en_line)

        # The word is always present
        index_start_name = en_line.index("''")
        index_end_name = en_line.index("''", index_start_name + 1)
        index_colon = en_line.index(" : ")
        self.name = en_line[index_start_name + 2:index_end_name].strip()

        # The type could be missing
        self.type = None
        if "(" in en_line[0:index_colon]:
            index_start_parenthesis = en_line.index("(")
            index_end_parenthesis = en_line.index(")")
            self.type = en_line[index_start_parenthesis + 1:\
                                index_end_parenthesis].strip()

        # Could be a simple translation "méchant, malveillant" or
        # a list of definitions "1/ vaisseau ; 2/ bouteille (d’air comprimé)"
        definition = en_line[index_colon + 2:].strip()
        self.definitions = []
        if "1/" in definition:  # Case 2
            i = 1
            found = True
            index_definition_i = definition.index(str(i) + "/")
            index_definition_i_plus_1 = definition.index(str(i + 1) + "/")
            while found:

                # Extract definition i
                if not index_definition_i_plus_1:  # We are at the end
                    index_definition_i_plus_1 = len(definition)
                    found = False
                definition_i = definition[index_definition_i + 2:index_definition_i_plus_1].strip()
                if definition_i.endswith(" ;"):
                    definition_i = definition_i[:-2]
                self.definitions.append(definition_i)

                # Determine indices of definition i+1
                i = i + 1
                index_definition_i = index_definition_i_plus_1
                if str(i + 1) + "/" in definition:
                    index_definition_i_plus_1 = definition.index(str(i + 1) + "/")
                else:
                    index_definition_i_plus_1 = None

        else:  # Case 1
            self.definitions.append(definition)

        # FR translation are included in the following line. For now, we just
        # initialized the variable
        self.fr_translations = []

    def new_fr_line(self, fr_line):
        """
        Add a new (optional) french word.
        The line should not contains the xWiki prefix "** ".
        Ex: "veste (n f) : ''jacket''"
        """
        self._parse_fr_line(fr_line)

    def _parse_fr_line(self, fr_line):
        # veste (n f) : ''jacket''
        print(">" + fr_line)


    def __str__(self):
        result = "name: %s %s" % (self.name, self.type)
        if self.definitions:
            result += "\n"
            for d in self.definitions:
                result += "\t- %s\n" % d
        return result


def generate_flashcard(word):
    """
    Unsafe method to load the word into Anki.
    """
    #print(word)
    pass


if __name__ == "__main__":

    current_word = None

    # Parse input file
    with open('false-friends-FR-EN.xwiki', 'r') as f:
        for line in f.readlines():
            line = line.strip()

            # We are only interested by two types of line
            if line.startswith("* "):  # New word
                if current_word:  # Save previous word
                    generate_flashcard(current_word)

                line = line[2:]
                current_word = Word(line)

            elif line.startswith("** fr : "):  # New definition
                line = line[8:]
                current_word.new_fr_line(line)


    # Add the last word
    if current_word:
        generate_flashcard(current_word)
