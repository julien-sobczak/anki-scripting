#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert and load the file "false-friends-FR-EN.xwiki to Anki.

To run: (we consider a deck named "EnglishFF" already exists)

$ python load_false_friends.py -d EnglishFF \
    $PWD/false-friends-FR-EN.xwiki \
    AnkiTest/User\ 1/
"""

import os, sys, re

# Add Anki source to path
sys.path.append("../../anki")
from anki.storage import Collection


class Word:
    """
    One entry in the input document.
    """

    TYPES = ["n", "v", "adj.", "adv.", "abr.", "interj."]

    def __init__(self, en_line):
        """
        Initialize a new word from the first line of its definition.
        The line should not contains the xWiki prefix "* ".
        Ex: "''vest'' (n) : 1/ maillot de corps ; 2/ (amér.) gilet"
        """
        self._parse_en_line(en_line)
        self.fr_words = []
        self.raw = en_line + "\n"

    def _parse_en_line(self, en_line):
        # ''vessel'' (n) : 1/ vaisseau ; 2/ bouteille (d’air comprimé)
        #print(">" + en_line)

        if "(fa p)" in en_line:
            self.partial = True
            en_line = en_line.replace(" (fa p)", "")
        else:
            self.partial = False

        # The type could be missing
        self.type = None
        for type in self.TYPES:
            expr = " (" + type + ")"
            if expr in en_line:
                self.type = type
                en_line = en_line.replace(expr, "")
                break

        # The word is always present
        index_start_name = en_line.index("''")
        index_end_name = en_line.index("''", index_start_name + 1)
        index_colon = en_line.index(" : ")
        self.name = en_line[index_start_name + 2:index_end_name].strip()

        definition = en_line[index_colon + 2:].strip()
        self.definitions = self._extract_definitions(definition)

        # FR translation are included in the following line. For now, we just
        # initialized the variable
        self.fr = []

    def _extract_definitions(self, raw_definition):
        # Could be a simple translation "méchant, malveillant" or
        # a list of definitions "1/ vaisseau ; 2/ bouteille (d’air comprimé)".
        # Numerals and letters are supported for the ordered list prefix
        # (1/, 2/, ..., or a/, b/, ...)

        definition = " " + raw_definition  # Add a leading space to search for " a/"
        if " a/" in definition:  # Replace to convert all list to numerals
            for i, letter in enumerate(["a", "b", "c", "d", "e"]):
                definition = definition.replace(" " + letter + "/", " " + str(i + 1) + "/")
            definition = definition.strip()

        if "1/" in definition:  # Case 2
            result = []
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
                result.append(definition_i)

                # Determine indices of definition i+1
                i = i + 1
                index_definition_i = index_definition_i_plus_1
                if str(i + 1) + "/" in definition:
                    index_definition_i_plus_1 = definition.index(str(i + 1) + "/")
                else:
                    index_definition_i_plus_1 = None

            return result

        else:  # Case 1
            return [raw_definition]

    def new_fr_line(self, fr_line):
        """
        Add a new (optional) french word.
        The line should not contains the xWiki prefix "** ".
        Ex: "veste (n f) : ''jacket''"
        """
        self._parse_fr_line(fr_line)
        self.raw += fr_line + "\n"

    def _parse_fr_line(self, fr_line):
        # veste (n f) : ''jacket''
        #print(">" + fr_line)
        index_colon = fr_line.index(" : ")
        prefix = fr_line[:index_colon]
        definition = fr_line[index_colon + 3:].strip()

        type = None
        for t in self.TYPES:
            expr = " (" + t + ")"
            if expr in prefix:
                type = t
                prefix = prefix.replace(expr, "")
                break

        name = prefix.strip()

        self.fr.append({
            "name": name,
            "type": type,
            "definition": definition
        })

    def __str__(self):
        #print(self.raw)

        # Add a suffix if it's a partial false friend
        is_partial = ""
        if self.partial:
            is_partial = " (partial)"

        result = "name: %s (%s)%s\n" % (self.name, self.type, is_partial)
        if self.definitions:
            result += "\t- Definitions:\n"
            for d in self.definitions:
                result += "\t\t- %s\n" % d

        if self.fr:
            result += "\t- FR:\n"
            for french_word in self.fr:
                result += "\t\t- %s (%s) : %s\n" % \
                    (french_word['name'], french_word['type'], french_word['definition'])

        return result


def escape_em(text):
    """
    Replace quotes around english word by HTML tags.
    
    Ex: ennui ''tiresome'' > ennui <em><font>tiresome</font></em>
    """
    return re.sub(r"''(.*?)''",
        r'<em><font color="#39499b">\1</font></em>',
        text)



def add_flashcard(col, deck, front, back):
    """
    We hide the Anki API details inside this model.
    Each call create a new note of type Basic in the given deck.
    """

    # Instantiate the new note
    note = col.newNote()
    note.model()['did'] = deck['id']

    # Set the ordered fields as defined in Anki note type
    fields = {}
    fields["Front"] = front
    fields["Back"] = back
    anki_fields = ["Front", "Back"]
    for field, value in fields.items():
        note.fields[anki_fields.index(field)] = value


    # Set the tags (and add the new ones to the deck configuration
    tags = "Grammar FalseFriends"
    note.tags = col.tags.canonify(col.tags.split(tags))
    m = note.model()
    m['tags'] = note.tags
    col.models.save(m)

    # Add the note
    col.addNote(note)


def generate_flashcard(col, deck, word):
    """
    Unsafe method to load the word into Anki.
    """

    # Create a flashcard for the english word
    en_name = word.name
    partial = ""
    color = "red"
    if word.partial:
        partial = "PARTIAL "
        color = "#FF8C00" # DarkOrange
    en_type = ""
    if word.type:
        en_type = " (%s)" % word.type

    # Front (English->French)
    front = """
<small class="notice" style="color: gray; font-style: italic">
    What means
</small> <font color="#39499b">%s</font>%s? """ % (en_name.replace("'",""), en_type)

    # Back (English->French)
    en_definitions = ""
    for definition in word.definitions:
        en_definitions += "    <li>%s</li>\n" % escape_em(definition)
    fr_definitions = ""
    for definition in word.fr:
        fr_name = definition['name']
        fr_definition = definition['definition']
        fr_type = ""
        if definition['type']:
            fr_type = " (%s)" % definition['type']
        fr_definitions += "    <dt><strong>%s</strong>%s</dt>\n" % (fr_name, fr_type)
        fr_definitions += "    <dd>%s</dd>" % escape_em(fr_definition)
    back = """
<ul style="text-align: left">
%s</ul>
<div class="falseFriends partial" style="color: %s; font-weight: bold; margin: 1em 0">
  **%sFALSE FRIENDS**
</div>
""" % (en_definitions, color, partial)
    if len(word.fr):
        back += """
<div class="notice">
    <small style="color: gray; font-style: italic;">Do not confuse with:</small>
</div>
<dl style="text-align: left">
%s
</dl>""" % fr_definitions

    add_flashcard(col, deck, front, back)

    # Iterate over French expressions
    for definition in word.fr:
        fr_name = definition['name']
        fr_definition = definition['definition']
        fr_type = ""
        if definition['type']:
            fr_type = " (%s)" % definition['type']
        front = """
<small class="notice" style="color: gray; font-style: italic">
    Translate
</small> %s%s? """ % (fr_name, fr_type)

        back = """
%s

<div class="falseFriends partial" style="color: %s; font-weight: bold; margin: 1em 0">
  **%sFALSE FRIENDS**
</div>
<div class="notice">
    <small style="color: gray; font-style: italic;">Do not confuse with</small>
    <font color="#39499b">%s</font>
</div>
<ul style="text-align: left">
%s</ul>
        """ % (escape_em(fr_definition), color, partial, en_name, en_definitions)

        add_flashcard(col, deck, front, back)



if __name__ == "__main__":

    import argparse, glob

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Text file containing the list of false friends in xwiki syntax")
    parser.add_argument("anki_home", help="Home of your Anki installation")
    parser.add_argument("-d", "--deck", help="Name of the deck in which to create the flashcards", default="English")
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action='store_true')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()

    print("----------------------------------")
    print("False Friends Loader -------------")
    print("----------------------------------")
    print("Anki home: %s\n" % args.anki_home)



    # Load the anki collection
    cpath = os.path.join(args.anki_home, "collection.anki2")
    col = Collection(cpath, log=True)

    # Set the model
    modelBasic = col.models.byName('Basic')
    deck = col.decks.byName(args.deck)
    col.decks.select(deck['id'])
    col.decks.current()['mid'] = modelBasic['id']

    # Iterate over false friends
    current_word = None

    # Parse input file
    with open('/home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/false-friends-FR-EN.xwiki', 'r') as f:
        for line in f.readlines():
            line = line.strip()

            # We are only interested by two types of line
            if line.startswith("* "):  # New word
                if current_word:  # Save previous word
                    generate_flashcard(col, deck, current_word)

                line = line[2:]
                current_word = Word(line)

            elif line.startswith("** fr : "):  # New definition
                line = line[8:]
                current_word.new_fr_line(line)


    # Add the last word
    if current_word:
        generate_flashcard(col, deck, current_word)


    # Save the changes to DB
    col.save()
