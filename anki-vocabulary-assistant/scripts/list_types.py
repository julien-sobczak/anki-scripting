#!/usr/bin/env python

"""
List all the types present in the wiktionary such as Noun, Verb, Preposition.

To get a list of unique types, use the common Bash commands like this:

$ python list_types.py | sort | uniq
Adjective
Adverb
Article
Conjunction
Determiner
Interjection
Noun
Particle
Prefix
Preposition
Pronoun
Verb

"""


if __name__ == '__main__':

  import json    
  
  with open('../../anki-usecase-enfrequency/resources/mywiktionary.json') as data_file:    
    data = json.load(data_file)
    for word in data:
      if "types" in word:
        for t in word["types"]:
          print t["type"]
