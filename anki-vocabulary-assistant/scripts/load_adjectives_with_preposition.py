#!/bin/python

"""
Create flashcards for common adjectives requiring a preposition.

# Input

This program accepts a JSON file containing the list of adjectives in this format:

    {
        "adjective_with_preposition": "afraid of",
        "adjective": "afraid",
        "preposition": "of",
        "example_annotated": "She is <b>afraid of</b> speaking in public.",
        "example_clozed": "She is <b>afraid</b> ___ speaking in public."
    }

The program creates a flashcard for each line like this:

===========================================================
<b>Complete</b> (Grammar)

<i lang="en">She is <b>afraid</b> ___ speaking in public.</i>
-----------------------------------------------------------
<i>She is <b>afraid of</b> speaking in public.</i>
===========================================================

Note: all created flashcards have the tag "AdjectivePreposition"


# Running

$ python load_adjectives_with_preposition.py \
    -d English \
    $PWD/adjectives_with_preposition.json \
    AnkiTest/User\ 1/

Or
$ python load_adjectives_with_preposition.py -d EnglishGrammar /home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/adjectives_with_preposition.json AnkiTest/User\ 1/

"""

import json
import re
import os
import sys


def load_adjectives_with_preposition(input_file, col, deck):

    # We read the input file
    with open(input_file) as f:
        data = json.load(f)
        for word in data:

            # Create HTML content
            card_front = """<b>Complete</b> (Grammar)<br><br><i lang="en">%s</i>""" % word["example_clozed"]
            card_back = """<i lang="en">%s</i>""" % word["example_annotated"]
            add_flashcard(col, deck, card_front, card_back)

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
    tags = "Grammar AdjectivePreposition"
    note.tags = col.tags.canonify(col.tags.split(tags))
    m = note.model()
    m['tags'] = note.tags
    col.models.save(m)

    # Add the note
    col.addNote(note)



if __name__ == "__main__":

    # Add Anki source to path
    sys.path.append("../../anki")
    from anki.storage import Collection

    import argparse, glob

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="JSON file containing the phrasal verbs")
    parser.add_argument("anki_home", help="Home of your Anki installation")
    parser.add_argument("-d", "--deck", help="Name of the deck in which to create the flashcards", default="English")
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action='store_true')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()

    print("----------------------------------------------")
    print("Adjectives with Preposition Loader -----------")
    print("----------------------------------------------")
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
    load_adjectives_with_preposition(args.input_file, col, deck)

    # Save the changes to DB
    col.save()
