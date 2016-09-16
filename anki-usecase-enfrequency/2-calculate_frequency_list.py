"""
Parse CSV frequency lists to produce a unique list of ordered word.
Input list should respect the following format:
15,orange,14574545
Where '15' is the rank, 'orange' is the word, and '14574545' is the frequency (not used by this script)

To run the program:
$ python 2-calculate_frequency_list.py > resources/my_english_frequency_list.csv

Note: input files are hardcoded in this script
"""

import codecs
import operator
import functools


def fill_words(*filenames):
    frequencies = {}

    for filename in filenames:
        for line in codecs.open(filename, "r", "utf-8"):
            (rank, word, frequency) = line.split(",")

            if word not in frequencies:
                frequencies[word] = []
            frequencies[word].append(int(rank))

    return frequencies


def filter(word):
    # Remove Proper name (ex: Mickey)
    if word[0].isupper():
        return True
    # Remove single length word (ex: I)
    if len(word) == 1:
        return True
    # Remove abbreviation (ex: can't)
    if "'" in word:
        return True
    # Remove word containing a digit (ex: 8th)
    if any(char.isdigit() for char in word):
        return True
    # Remove abbreviation ending with . (ex: Mr.)
    if "." in word:
        return True
    return False


def filter_words(frequencies):
    """ Remove all unwanted entries """
    result = {}
    for word, ranks in frequencies.items():
        if filter(word):
            continue
        result[word] = ranks
    return result


def flat_ranks(frequencies):
    """ Calculate the average rank among collected rank."""
    result = {}
    for word, ranks in frequencies.items():
        rank = int(functools.reduce(lambda x, y: x + y, ranks) / len(ranks))
        result[word] = rank
    return result


def filter_advanced_words(frequencies):
    """ Remove plurals, conjugations, etc """
    result = frequencies.copy()
    for word, rank in frequencies.items():  # Work on copy to delete during iteration

        if word.endswith("ing"):
            adverb_word = word
            verb = word[:len(word) - 3]
            if adverb_word in result and verb in result:
                # Caution: a word could be remove on the origin list but still be present in the copy
                # print("Adverb detected %s/%s" % (verb, adverb_word))
                del result[adverb_word]

        if word.endswith("ies"):
            third_person_verb = word
            verb = word[:len(word) - 3] + "y"
            if third_person_verb in result and verb in result:
                # print("Conjugation detected %s/%s" % (verb, third_person_verb))
                del result[third_person_verb]

        if word.endswith("ed") and len(word) > 4:  # Exclude red for example
            adjective_word = word

            word1 = word[:len(word) - 2]  # fill => filled
            if adjective_word in result and word1 in result:
                # print("Adjective1 detected %s/%s" % (word1, adjective_word))
                del result[adjective_word]

            word2 = word[:len(word) - 1]  # displease => displeased
            if adjective_word in result and word2 in result:
                # print("Adjective2 detected %s/%s" % (word2, adjective_word))
                del result[adjective_word]

        if word.endswith("s"):
            plural_word = word
            singular_word = word[:len(word) - 1]
            if plural_word in result and singular_word in result:
                # print("Plural detected %s/%s" % (singular_word, plural_word))
                del result[plural_word]

    return result


def sort_by_rank(frequencies):
    return sorted(frequencies.items(), key=operator.itemgetter(1))


def display_to_csv(frequencies):
    # We need another counter because previous average ranking could produce words with the same rank
    i = 0
    for word, rank in frequencies:
        i += 1
        print("%s,%s" % (i, word))


if __name__ == '__main__':

    # Read the file to parse
    frequencies = fill_words("resources/40000_frequency_list_gutenberg.csv", "resources/40000_frequency_list_tv.csv")

    # Remove unwanted basic words (ex: TV)
    frequencies = filter_words(frequencies)

    # Average the rank when words was present in multiple frequency lists
    frequencies = flat_ranks(frequencies)

    # Remove unwanted advanced words (ex: walking).
    # Unlike basic words, advanced words need full frequency list to determine if a word should be filtered.
    # Ex: remove walking if walk is already present.
    frequencies = filter_advanced_words(frequencies)

    # Sort the words by rank
    frequencies = sort_by_rank(frequencies)

    # Output a new CSV with incrementing rank
    display_to_csv(frequencies)
