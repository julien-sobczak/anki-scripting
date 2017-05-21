#/bin/python

"""
Convert the file adjectives_with_preposition.txt to json.

Input format:
  afraid of,She is afraid of speaking in public.

Output format:
  {
    "adjective_with_preposition": "afraid of",
    "adjective": "afraid",
    "preposition": "of",
    "example_annotated": "She is <b>afraid of</b> speaking in public.",
    "example_clozed": "She is <b>afraid</b> ___ speaking in public."
  }

"""

import json

with open('adjectives_with_preposition.txt') as f:
    data = []
    for line in f.readlines():
        words = line.strip().split(",")

        adjective_preposition = words[0]
        parts = adjective_preposition.split(" ")
        if len(parts) != 2:
            print("Error: Adjective with multiple prepositions are not supported: %s" % adjective_preposition)
        adjective = parts[0]
        preposition = parts[1]
        example = ",".join(words[1:])
        example_annotated = example.replace(adjective_preposition, "<b>" + adjective_preposition + "</b>")
        example_clozed = example.replace(adjective_preposition, "<b>" + adjective + "</b> " + "___")

        data.append({
            "adjective_with_preposition": adjective_preposition,
            "adjective": adjective,
            "preposition": preposition,
            "example_annotated": example_annotated,
            "example_clozed": example_clozed,
        });

        if adjective_preposition not in example:
            print("Error: %s not in %s" % (adjective_preposition, example))

    with open('adjectives_with_preposition.json', 'w') as fo:
        json.dump(data, fo, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
