    #!/usr/bin/env python

"""
Demo script to demonstrate how to scrap www.linguee.fr
"""

import requests                 # to call Linguee
from bs4 import BeautifulSoup   # to parse response

starts_after="earlier"
started=False

# We read the input file
with open("connectors.txt") as fi:
    # We open the output file
    with open("connectors-with-sentences.txt", "a") as fo:

        for line in fi.readlines():
            line = line.strip()
            if line.startswith("#"):  # New category
                print(line)
                fo.write("%s\n" % line)
                continue

            if line == "":
                fo.write("\n")
                continue

            fields = line.strip().split(",")
            connector = fields[0]

            if connector == starts_after:
                started = True
                continue

            if not started:
                continue

            # Get Linguee dictionary content
            url = 'http://www.linguee.com/english-french/search?source=auto&query=%s' % connector
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'http://www.linguee.fr/',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
            }

            r = requests.get(url, headers=headers)

            # Check response

            if r.status_code != 200:
                raise ValueError("Invalid status code '%s'" % r.status_code)
            html_doc = r.text
            soup = BeautifulSoup(html_doc, 'html.parser')

            # List the dictionary's examples
            print("\n[%s]. Sentence(s):" % connector)
            sentences = []
            examples = soup.select("#dictionary .isMainTerm .example.line .tag_s")
            selected_sentence = ""

            if len(examples):
                for i, example in enumerate(examples):
                    if i > 8:
                        break
                    s = example.get_text()
                    print("[%s] %s" % ((i + 1), s))
                    sentences.append(s)
                answer = input("Choose: ")
                answer = int(answer)
                if answer > 0:
                    selected_sentence = sentences[answer - 1].strip()

            fo.write("%s,%s\n" % (connector, selected_sentence))
