#/usr/bin/python

from bs4 import BeautifulSoup
import sys

if len(sys.argv) != 2:
  print("Usage: python $0 <file.html>")
  sys.exit(1)


html_file = sys.argv[1]
with open(html_file, 'r') as input_file:
    html_doc = input_file.read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    for tr in soup.select('tbody tr'):
      cells = tr.find_all('td')
      print(','.join(c.get_text() for c in cells))
