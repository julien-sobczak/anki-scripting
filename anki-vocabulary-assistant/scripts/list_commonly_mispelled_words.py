#!/usr/bin/env python

"""
List the english words having a french translation that differs
from a single letter.

$ python list_commonly_mispelled_words.py
human,humain
dinner,dîner
"""


if __name__ == '__main__':

    import json
    import Levenshtein
    from unidecode import unidecode

    with open('../../anki-usecase-enfrequency/resources/mywiktionary.json') as data_file:
        data = json.load(data_file)
        for word in data:

            if not "translations" in word:
                continue

            title = word["title"]
            if len(title) < 4:
                # We ignore short word to avoid being polluated
                continue

            for translation in word["translations"]:
                escaped_translation = unidecode(translation)
                escaped_translation.encode("ascii")

                title = unidecode(title)
                title.encode("ascii")

                if word['rank'] > 30000:
                    continue

                if Levenshtein.distance(escaped_translation, title) == 1:
                    # Remove simple difference

                    # Ex: "just" => "juste"
                    if title + "e" == escaped_translation:
                        break

                    # Ex: "suppose" => "supposer"
                    if title + "r" == escaped_translation:
                        break

                    # Ex: "tone" => "ton"
                    if title == escaped_translation + "e":
                        break

                    # Ex: "society" => "societé"
                    if title[:-1] == escaped_translation[:-1]:
                        break

                    # Ex: "project" => "projet"
                    if title.endswith("ct") and escaped_translation.endswith("t"):
                        break

                    # Ex: "responsible" => "responsable"
                    if title.endswith("ible") and escaped_translation.endswith("able"):
                        break

                    # Ex: "original" => "originel"
                    if title.endswith("al") and escaped_translation.endswith("el"):
                        break

                    # Ex: "persistent" => "persistant"
                    if title.endswith("ent") and escaped_translation.endswith("ant"):
                        break

                    # Ex: "title" => "titre"
                    if title.endswith("le") and escaped_translation.endswith("re"):
                        break

                    print("%s,%s,%s" % (title, translation,escaped_translation))
