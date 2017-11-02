#!/usr/bin/env python
"""
Use Google Translate API to complete missing translations from Wikdictionary.

See http://py-googletrans.readthedocs.io/en/latest/#googletrans.models.Translated

To launch the program:

$ python complete-with-google-translate.py

"""

import json
import codecs
from googletrans import Translator
import time
import random

# How many words in a single API call?
BATCH_SIZE = 200

# Limit the numbers of call per day to avoid being banned
MAX_API_CALLS = 30

# Ignore words having rank lower than START_RANK
START_RANK = 1

# Directory local filepath 
dictionary = '/home/julien/workshop/anki-scripting/anki-usecase-enfrequency/resources/mywiktionary.json'

# Wrapper around the Google Translate API
translator = Translator()


with open(dictionary) as f:
    words = json.load(f)

    api_calls = 0

    try:
        current_words = []
        for word in words:
            has_translation = 'translations' in word and len(word['translations']) > 0
            if has_translation:
                continue

            if word['rank'] < START_RANK:
                continue

            current_words.append(word)
            
            if len(current_words) == BATCH_SIZE:  # Batch processing to limit API calls
                titles = [w['title'] for w in current_words]
                first_rank = current_words[0]['rank']
                last_rank = current_words[-1]['rank']
                titles_str = ','.join(titles)
                print('Send words from rank %s to rank %s...\n[%s]' % (first_rank, last_rank, titles_str))
                translations = translator.translate(titles, src='en', dest='fr')
                api_calls += 1
                print('\t... OK')
                for j, t in enumerate(translations):
                    current_words[j]['translations'] = [t.text]
                    current_words[j]['google_translate'] = True
                
                if api_calls >= MAX_API_CALLS:
                    print("Reach max API calls. Exiting...")
                    break
                else:
                    time.sleep(random.randint(90, 180))
                current_words = []

    except:
        pass
    
    # We always write the output (to support resume)
    output = dictionary + '.new'
    print('Dumping results into %s ...' % output)
    out = codecs.open(output, 'w', 'utf-8')
    json.dump(words, out, sort_keys=True, indent=4, separators=(',',':'), ensure_ascii=False)

