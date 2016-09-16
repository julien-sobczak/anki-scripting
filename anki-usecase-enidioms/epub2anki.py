"""
Convert an Epub to Flashcards.

By default, read from myepub/ inside the same folder.
This folder is the unzipped version of the file myepub.epub.
"""

from bs4 import BeautifulSoup
import codecs
import sys
import re
import os

# Add Anki source to path
sys.path.append("../anki")
from anki.storage import Collection


# Constants
PROFILE_HOME = os.path.expanduser("~/Documents/Anki/User 1")
EPUB_UNZIPPED_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "myepub")

##################
# Global variables
##################

# Current chapter
chapter = None

# Current category
category = None

# Current idiom
idiom = None

# List of all idioms
idioms = []


# One of the 4000 idioms :)
class Idiom:

    def __init__(self, chapter, category):
        self.category = category
        self.chapter = chapter
        self.en = ''
        self.fr = ''
        self.examples = []
        self.warnings = []

    def set_category(self, category):
        self.category = category

    def set_en(self, expression):
        self.en = expression

    def set_fr(self, expression):
        self.fr = expression

    def add_example(self, example):
        self.examples.append(example)

    def add_warning(self, text):
        self.warnings.append(text)

    def display(self):
        print("%s / %s (%s)" % (self.en, self.fr, self.category))
        for example in self.examples:
            print( "  - %s / %s" % (example['fr'], example['en']))
        for warning in self.warnings:
            print("  !! %s" % warning)


def process_bloc(soup, bloc_element):
    global chapter
    global category
    global idiom

    for p in bloc_element.find_all('p'):

        classes = p.get('class')

        found = False
        for classe in classes:
            if u'Chapter-Heading_Toc' in classe or u'chaper-headibg-2-chiffres' in classe:
                found = True
                category = p.get_text()
                index = category.index('. ')
                if index:
                    chapter = category[:index]
                    category = category[index+2:]
                print("Beginning category %s" % category)

        if found:
            continue

        if u'_1_IDIOM' in classes: # New idiom
            #if idiom:
            #    idiom.display()
            #    print "\n\n"
            idiom = Idiom(chapter, category)
            idioms.append(idiom)
            text = p.get_text()

            if '●' in text:
                index = text.index('●')
                idiom.set_en(text[:index])
                idiom.set_fr(text[index+1:])
            else:
                idiom.set_en(p.get_text())
        elif u'_2_EXEMPLE-IDIOM' in classes: # Example for previous idiom
            text = p.get_text()
            if '. ' in text:
                index = text.index('. ')
                idiom.add_example({ 'en': text[:index + 1], 'fr': text[index +2:] })
            elif '? ' in text:
                index = text.index('? ')
                idiom.add_example({ 'en': text[:index + 1], 'fr': text[index +2:] })
            elif '! ' in text:
                index = text.index('! ')
                idiom.add_example({ 'en': text[:index + 1], 'fr': text[index +2:] })
            elif '.”' in text:
                index = text.index('.”')
                idiom.add_example({ 'en': text[:index + 2], 'fr': text[index +2:] })
            else:
                print("[ERROR] Unable to find translation in example '%s'" % text)
        elif u'WARNING' in classes: # WARNING
            idiom.add_warning(p.get_text())
        else:
            print("[ERROR] Unknown class %s" % (classes))


def highlight_qualifier(text):
    return re.sub(r'[(](.*?)[)]', r'<span class="qualifier">(\1)</span>', text)


def read_idioms(page_start, page_end):
    for i in range(page_start, page_end):

        # Read the page content
        epub_pagefile = os.path.join(EPUB_UNZIPPED_ROOT, "OEBPS/Page_%s.html" % i)
        f = codecs.open(epub_pagefile, "r", "utf-8")
        page_html = f.read()
        f.close()

        # Parse the HTML
        soup = BeautifulSoup(page_html, 'html.parser')

        for bloc in soup.find_all('div', { 'class': 'Bloc-de-texte-standard'}):

            if bloc.get('id') and bloc.get('id').startswith('_idContainer'):
                print("(Page_%s) Found %s" % (i, bloc.get('id')))
                process_bloc(soup, bloc)


def bulk_loading_anki(idioms):

    # Load the anki collection
    cpath = os.path.join(PROFILE_HOME, "collection.anki2")
    col = Collection(cpath, log=True)

    # Set the model
    modelBasic = col.models.byName('Idiom')
    col.decks.current()['mid'] = modelBasic['id']

    # Get the deck
    deck = col.decks.byName("English")

    # Iterate over idioms
    for idiom in idioms:

        # Instantiate the new note
        note = col.newNote()
        note.model()['did'] = deck['id']

        # Set the content
        english_field = highlight_qualifier(idiom.en)
        french_field = highlight_qualifier(idiom.fr)
        examples_field = "" # fill below
        note_field =  "" # fill below

        if not idiom.en:
            # Should not happen
            continue
        if not idiom.fr and idiom.examples:
            # Sometimes, there is not translation in french, we used the first example phrase instead
            english_field = idiom.examples[0]['en']
            french_field = idiom.examples[0]['fr']
        if "(familier)" in idiom.en:
            french_field += " " + highlight_qualifier('(familier)')

        for example in idiom.examples:
            examples_field += '<p class="example"><span class="english">%s</span> <span class="french">%s</span></p>' \
                % (example['en'], example['fr'])

        for warning in idiom.warnings:
            note_field += '<p class="warning">%s<p>' % warning

        note.fields[0] = english_field
        note.fields[1] = french_field
        note.fields[2] = examples_field
        note.fields[3] = note_field

        print("{\nEnglish: %s,\nFrench: %s,\nExamples: %s,\nNotes: %s}" % (
            note.fields[0], note.fields[1], note.fields[2], note.fields[3]))

        # Set the tags (and add the new ones to the deck configuration
        tags = "idiom"
        note.tags = col.tags.canonify(col.tags.split(tags))
        m = note.model()
        m['tags'] = note.tags
        col.models.save(m)

        # Add the note
        col.addNote(note)

    # Save the changes to DB
    col.save()

if __name__ == '__main__':

    read_idioms(2, 2) # Only the second page of our demo ebook contains idioms
    #bulk_loading_anki(idioms)
