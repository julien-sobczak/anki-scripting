
import unittest
import json
from load_word import *
from os import listdir
from os.path import isdir, join
import re

class TestLoadWord(unittest.TestCase):

    def _get_word(self, rank, word):
        """ Retrieve the JSON as string from the file system. """
        definition_path = "../save"
        dirs = [d for d in listdir(definition_path) \
            if re.match(r'\d+-\d+', d) and isdir(join(definition_path, d))]
        for d in dirs:
            (start, end) = d.split("-")
            if rank >= int(start) and rank < int(end):
                filename = "%s-%s.json" % (rank, word)
                filepath = join(definition_path, d, filename)
                with open(filepath) as f:
                    return json.load(f)
        raise Exception("Missing word %s (%s)" % (word, rank))

    def test_has_image_when_picture_present(self):
        doc = self._get_word(548, "accident")
        word = Word(doc)
        self.assertTrue(word.has_image_card())
        self.assertEqual(word.image(), "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT0GbB3_4-cAK7g3eHr82MDhhU9BT7aNeT2jOwLVITMHirlt0SXutFPl4E")

    def test_has_image_when_checked_by_error(self):
        doc = self._get_word(725, "board")
        word = Word(doc)
        self.assertFalse(word.has_image_card())

    def test_translation_could_contains_brackets(self):
        doc = self._get_word(1735, "healthy")
        word = Word(doc)
        self.assertEqual(word.translation(), "en bonne santé, sain")

if __name__ == "__main__":
    unittest.main()
