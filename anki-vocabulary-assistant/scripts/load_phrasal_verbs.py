#!/bin/python

import json
from bs4 import BeautifulSoup

data = []

# We read the input file
with open("phrasal_verbs.html") as fi:
    html_doc = fi.read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    for tr in soup.select("table tr"):
        cols = tr.find_all('td')
        if len(cols) != 3:
            print("WARN: different column count:" % tr)
        data.append({
            "verb": cols[0].get_text().strip(),
            "meaning": cols[1].get_text().strip(),
            "example": cols[2].get_text().strip(),
        })

    with open("phrasal_verbs.json", "w") as fo:
        json.dump(data, fo, indent=4, separators=(',', ': '))
