#!/bin/python

"""
Create flashcards for phrasal verbs.

# Input

This program accepts a JSON file containing the list of verbs in this format:

 {
   "example": "His evidence just doesn't add up.",
   "example_annotated": "His evidence just doesn't [add] [up].",
   "meaning": "make sense",
   "verb": "add up"
 },

The program creates multiple flashcards like this:

(for each example)
===========================================================
<b>Phrasal verb</b> (Grammar)

<i>His evidence just doesn't <b>add</b> ___.</i>

<em>Hint</em>: make sense
-----------------------------------------------------------
<i>His evidence just doesn't <b>add</b> <b>up</b>.</i>
===========================================================


===========================================================
What means <b>add up</b> (context) (Grammar)
-----------------------------------------------------------
<b>make sense</b> context? (usage)

Ex: <i>His evidence just doesn't <b>add</b> </b>up</b></i>.
===========================================================

Note: all created flashcards have the tag "PhrasalVerb"


# Running

$ python load_phrasal_verbs.py \
    -d English \
    $PWD/phrasal_verbs.json \
    AnkiTest/User\ 1/

Or
$ python load_phrasal_verbs.py -d EnglishGrammar /home/julien/workshop/anki-scripting/anki-vocabulary-assistant/scripts/phrasal_verbs.json AnkiTest/User\ 1/

"""

import json
import re
import os
import sys


def load_phrasal_verbs(input_file, col, deck):

    # We read the input file
    with open(input_file) as f:
        data = json.load(f)

        for word in data:

            # Collect fields
            examples = []
            examples_annotated = []
            if "examples" in word:
                examples.extend(word["examples"])
                examples_annotated.extend(word["examples_annotated"])
            if "example" in word:
                examples.append(word["example"])
                examples_annotated.append(word["example_annotated"])

            examples_highlighted = ""
            for ex in examples_annotated:
                ex_highlight = ex.replace('[', '<b>').replace(']', '</b>')
                examples_highlighted += '<i lang="en">%s</i><br>' % ex_highlight

            phrasal_verb = word["verb"]
            meaning = word["meaning"]

            context = ""
            if "context" in word:
                context = word["context"] + " "

            usage = ""
            if "usage" in word:
                usage = "(" + word["usage"] + ") "

            if "processed" not in word:  # Caution: this verb could have been included in a previous card with the same name
                word["processed"] = True

                # Create HTML content
                card_front = """What means the <b>phrasal verb <i>%s</i></b> %s%s(Grammar)""" % \
                    (phrasal_verb, context, usage)

                # Is unique?
                duplicates = []  # Some phrasal verb have the same definition. We group them to avoid an error in Anki Browser
                for other_word in data:
                    if "processed" in other_word:
                        continue
                    if other_word["verb"] != word["verb"]:
                        continue
                    if "context" in word and "context" not in other_word:
                        continue
                    if "context" not in word and "context" in other_word:
                        continue
                    if "context" in word and "context" in other_word and other_word["context"] != word["context"]:
                        continue
                    if "usage" in word and "usage" not in other_word:
                        continue
                    if "usage" not in word and "usage" in other_word:
                        continue
                    if "usage" in word and "usage" in other_word and other_word["usage"] != word["usage"]:
                        continue
                    duplicates.append(other_word)
                    other_word["processed"] = True

                if duplicates:
                    # We marge all the verb on the same card (but not for examples)
                    duplicates.append(word)
                    card_back = ""
                    for i, dup in enumerate(duplicates):
                        if "example_annotated" in dup:
                            dup_example_highlighted = dup["example_annotated"]
                        if "examples_annotated" in dup:
                            dup_example_highlighted = dup["examples_annotated"][0]
                        dup_example_highlighted = ex.replace('[', '<b>').replace(']', '</b>')
                        dup_example_highlighted = '<i lang="en">%s</i><br>' % dup_example_highlighted

                        dup_meaning = dup["meaning"]

                        card_back += """
<div lang="en">%d. %s</div>
<div>Ex: %s</div><br/>
""" % ((i+1), dup_meaning, dup_example_highlighted)
                    add_flashcard(col, deck, card_front, card_back)
                else:
                    card_back = """
            <div>%s</div>
            <br/>
            <div>Ex:<br>%s</div>
            """ % (meaning, examples_highlighted)
                    add_flashcard(col, deck, card_front, card_back)

            for ex in examples_annotated:
                example_clozed = ex
                i_start = example_clozed.index("[")
                i_end = example_clozed.index("]")
                example_clozed = ex[:i_start] + "<b>" + ex[i_start+1:i_end] + "</b>" + ex[i_end+1:]
                example_clozed = re.sub(r'\[.*?\]', '___', example_clozed)
                example_highlight = ex.replace('[', '<b>').replace(']', '</b>')

                card_front = """<b>Phrasal verb</b> (Grammar)
    <br/><br/>
    <i lang="en">%s</i>
    <br/><br/>
    <small class="notice" style="color: gray; font-style: italic">Hint</small>: %s
    """ % (example_clozed, meaning)

                card_back = """<div><i>%s</i></div>
    <br/>
    <div>(<b>%s %s</b>: %s)</div>
    """ % (example_highlight, phrasal_verb, context, meaning)

                #print("=======================")
                #print(card_front)
                #print("-----------------------")
                #print(card_back)
                #print("=======================")
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
    tags = "Grammar PhrasalVerb"
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

    print("----------------------------------")
    print("Phrasal Verbs Loader -------------")
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
    load_phrasal_verbs(args.input_file, col, deck)

    # Save the changes to DB
    col.save()
