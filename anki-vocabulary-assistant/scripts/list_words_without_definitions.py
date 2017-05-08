#!/usr/bin/env python

"""
List all the types present in the wiktionary such as Noun, Verb, Preposition.

To get a list of unique types, use the common Bash commands like this:

$ python list_words_without_definitions.py

"""


if __name__ == '__main__':

    import json

    with open('../../anki-usecase-enfrequency/resources/mywiktionary.json') as data_file:
        data = json.load(data_file)
        for word in data:
            if not "types" in word or len(word["types"]) == 0:
                print("%s,%s" % (word["title"], word["rank"]))
