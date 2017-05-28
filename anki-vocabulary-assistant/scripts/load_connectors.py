#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert and load the file "connectors.json" to Anki.

# Input

This program accepts a JSON file containing the list of verbs in this format:

 {
   "connector_en": "afterward",
   "connector_fr": "Par la suite",
   "example_en": "Afterward, she got a promotion.",
   "example_en_annotated": "[Afterward], she got a promotion.",
   "example_fr": "Par la suite, elle a obtenu une promotion.",
   "example_fr_annotated": "[Par la suite], elle a obtenu une promotion."
 }

# Output

The program creates multiple flashcards like this:

===========================================================
<div>
  <small class="notice" style="color: gray; font-style: italic">
    Translate
  </small>
   (Grammar)
</div>
<br/>
<div lang="fr">
  <i><b>Par la suite</b>, elle a obtenu une promotion.</i>
</div>
-----------------------------------------------------------
<div lang="en">
  <i><b>Afterward</b>, she got a promotion.</i>
</div>
===========================================================

The input could contains additional properties "example_en_question" and "example_en_answer":

 {
   "connector_en": "again",
   "connector_fr": "à nouveau",
   "example_en": "We are back together again.",
   "example_en_annotated": "We are back together [again].",
   "example_en_answer": 3,
   "example_en_question": "We are (1) back (2) together (3).",
   "example_fr": "Nous revenons à nouveau ensemble.",
   "example_fr_annotated": "Nous revenons [à nouveau] ensemble."
}

An additional flashcard will be created like this:

===========================================================
<div>
  <small class="notice" style="color: gray; font-style: italic">
    Place
  </small>
  <b>again</b>
  (Grammar)
</div>
<br/>
<div lang="en">
  <i>
    We are <span class="placeholder" style="border-radius: 50px; background-color: gray; color: white">1</span>
    back <span class="placeholder" style="border-radius: 50px; background-color: gray; color: white">2</span>
    together <span class="placeholder" style="border-radius: 50px; background-color: gray; color: white">3</span>.
  </i>
</div>
-----------------------------------------------------------
<div lang="en">
  <span class="placeholder" style="border-radius: 50px; background-color: gray; color: white">1</span>
  <i>We are back together <b>again</b>.</i>
</div>
===========================================================

Note: all created flashcards have the tag "PhrasalVerb"


# Running

Note: We consider a deck named "English" already exists.

$ python load_connectors.py -d English \
    $PWD/connectors.json \
    AnkiTest/User\ 1/

Or
$ python load_connectors.py -d EnglishGrammar /home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/connectors.json AnkiTest/User\ 1/

"""

import os, sys, json, re


def load_connectors(input_file, col, deck):

    # We read the input file
    with open(input_file) as f:
        data = json.load(f)

        for word in data:

            connector_en = word["connector_en"]
            example_en_annotated = word["example_en_annotated"]
            example_fr_annotated = word["example_fr_annotated"]
            example_en_highlight = example_en_annotated.replace('[', '<b>').replace(']', '</b>')
            example_fr_highlight = example_fr_annotated.replace('[', '<b>').replace(']', '</b>')

            # Card 1: French -> English
            card_front = """
<div>
  <small class="notice" style="color: gray; font-style: italic">
    Translate
  </small>
   (Grammar)
</div>
<br/>
<div lang="fr">
  <i>%s</i>
</div>
""" % example_fr_highlight

            card_back = """
<div lang="en">
  <i>%s</i>
</div>
""" % example_en_highlight

            add_flashcard(col, deck, card_front, card_back)

            # Card 2: Place the connector
            if "example_en_question" in word and "example_en_answer" in word:

                question = word["example_en_question"]
                answer = word["example_en_answer"]

                question = question\
                    .replace('(1)', '<span class="placeholder" style="display: inline-block; padding: 5px; border-radius: 50px; background-color: gray; color: white">1</span>')\
                    .replace('(2)', '<span class="placeholder" style="display: inline-block; padding: 5px; border-radius: 50px; background-color: gray; color: white">2</span>')\
                    .replace('(3)', '<span class="placeholder" style="display: inline-block; padding: 5px; border-radius: 50px; background-color: gray; color: white">3</span>')\
                    .replace('(4)', '<span class="placeholder" style="display: inline-block; padding: 5px; border-radius: 50px; background-color: gray; color: white">4</span>')

                card_front = """
<div>
  <small class="notice" style="color: gray; font-style: italic">
    Place
  </small>
  <b>%s</b>
  (Grammar)
</div>
<br/>
<div lang="en">
  <i>
    %s
  </i>
</div>
 """ % (connector_en, question)

                card_back = """
<span class="placeholder" style="display: inline-block; padding: 5px; border-radius: 50px; background-color: gray; color: white">%s</span><br/><br/>
<div lang="en">
  <i>%s</i>
</div>
 """ % (answer, example_en_highlight)

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
    tags = "Grammar Connector"
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
    parser.add_argument("input_file", help="JSON file containing the connectors")
    parser.add_argument("anki_home", help="Home of your Anki installation")
    parser.add_argument("-d", "--deck", help="Name of the deck in which to create the flashcards", default="English")
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action='store_true')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()

    print("-------------------------------")
    print("Connectors Loader -------------")
    print("-------------------------------")
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
    load_connectors(args.input_file, col, deck)

    # Save the changes to DB
    col.save()
