#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert and load the file "connectors.json" to Anki.

To run: (we consider a deck named "English" already exists)

$ python load_connectors.py -d English \
    $PWD/connectors.json \
    AnkiTest/User\ 1/
"""

import os, sys, re

# Add Anki source to path
sys.path.append("../../anki")
from anki.storage import Collection



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

    import json

    with open('/home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/connectors-with-sentences.txt', 'r') as fi:
        words = []

        for line in fi.readlines():
            line = line.strip()

            if line == "" or line.startswith("#"):
                continue

            i_comma = line.index(",")
            i_pipe = line.index("|")

            connector = line[:i_comma]
            example_en = line[i_comma + 1:i_pipe]
            example_fr = line[i_pipe + 1:]

            words.append({
                "connector_en": connector,
                "connector_fr": "",
                "example_en": example_en,
                "example_en_question": example_en,
                "example_en_answer": example_en,
                "example_fr": example_fr,
                "example_fr_annotated": example_fr,
                "example_en_annotated": example_en,
            })

            # Card type 1: Place the connector (Grammar)
            # Front: This (1) is the first (2)
            # Back: This <b>connector</b> is the first.

            # Card type 2:
            # Front: <b>De fait</b>, ce projet est un échect
            # Back: <b>In fact</b>, this project is a total failure.



        with open('/home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/connectors.json', 'w') as fo:
            json.dump(words, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))

    sys.exit(0)

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
