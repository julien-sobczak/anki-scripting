"""
Update generate_site_lite.py to display Front/Back fields.
"""

import sys, os, codecs, re, shutil
sys.path.append("../anki")
from anki.storage import Collection


# Constants
PROFILE_HOME = os.path.expanduser("~/Documents/Anki/User 1")
OUTPUT_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target")


def rawText(text):
    """ Clean question text to display a list of all questions. """
    raw_text = re.sub('<[^<]+?>', '', text)
    raw_text = re.sub('"', "'", raw_text)
    raw_text = raw_text.strip()
    if raw_text:
        return raw_text
    else:
        return "Untitled"

def extractMedia(text):
    """
    Search in card text references to medias (ex: <img>).
    Another solution is to copy the whole media folder (shared by all decks).
    """
    regex = r'<img src="(.*?)"\s?/?>'
    pattern = re.compile(regex)

    src_media_folder = os.path.join(PROFILE_HOME, "collection.media/")
    dest_media_folder = os.path.join(OUTPUT_DIRECTORY, "medias")

    # Create target directory if not exists
    if not os.path.exists(dest_media_folder):
        os.makedirs(dest_media_folder)

    for (media) in re.findall(pattern, text):
        src = os.path.join(src_media_folder, media)
        dest = os.path.join(dest_media_folder, media)
        shutil.copyfile(src, dest)

    text_with_prefix_folder = re.sub(regex, r'<img src="medias/\1" />', text)

    return text_with_prefix_folder


if __name__ == '__main__':

    # Load the anki collection
    cpath = os.path.join(PROFILE_HOME, "collection.anki2")
    col = Collection(cpath, log=True)

    # Iterate over all cards
    cards = {}
    for cid in col.findCards("deck:Programming"):

        card = col.getCard(cid)

        # Retrieve the node to determine the card type model
        note = col.getNote(card.nid)
        model = col.models.get(note.mid)
        tags = note.tags

        # Card contains the index of the template to use
        template = model['tmpls'][card.ord]

        # We retrieve the question and answer templates
        question_template = template['qfmt']
        answer_template = template['afmt']

        # We could use a convenient method exposed by Anki to evaluate the templates
        rendering = col.renderQA([cid], "card")[0] # Only one element when coming from a given card
                                                   # Could be more when passing a note of type "Basic (with reversed card)"
        question = rendering['q']
        answer = rendering['a']

        question = extractMedia(question)
        answer = extractMedia(answer)

        css = model['css']

        question_html = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Card Question</title>
  <style>
  %s
  </style>
</head>
<body>
  <div class="card">
  %s
  </div>
</body>
</html>""" % (css, question)

        answer_html = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Card Answer</title>
  <style>
  %s
  </style>
</head>
<body>
  <div class="card">
  %s
  </div>
</body>
</html>""" % (css, answer)

        question_filename = "card-%s-question.html" % cid
        question_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, question_filename), "w", "utf-8")
        question_file.write(question_html)
        question_file.close()

        answer_filename = "card-%s-answer.html" % cid
        answer_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, answer_filename), "w", "utf-8")
        answer_file.write(answer_html)
        answer_file.close()

        cards[cid] = {
            'name': rawText(question),
            'question_file': question_filename,
            'answer_file': answer_filename,
            'tags': tags
        }


    # Generate a list of all cards
    card_list = '['
    for cid, props in cards.items():
        card_list += "{ 'name': \"%s\", 'question_file': '%s', 'answer_file': '%s', 'tags': [ %s ] },\n" % (
            props['name'], props['question_file'], props['answer_file'], "\"" + "\",\"".join(props['tags']) + "\"")
    card_list += ']'

    html = """<!doctype html>
<html lang="fr" ng-app="ankiApp">
<head>
  <meta charset="utf-8">
  <title>Anki Export</title>
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.5.7/angular.min.js"></script>
  <link href="https://fonts.googleapis.com/css?family=Handlee" rel="stylesheet">
  <link rel="stylesheet" type="text/css" href="stylesheet.css">
  <script>
angular.module('ankiApp', [])
  .controller('AnkiController', function() {
    var anki = this;
    anki.cardList = %s;
    anki.selectedCard = anki.cardList[0];

    anki.select = function(card) {
      anki.selectedCard = card;
    }
  });
  </script>
</head>
<body>
  <div ng-controller="AnkiController as anki">
      <div id="search">
        <input type="text" ng-model="anki.search" placeholder="Search...">
      </div>
      <nav id="list">
        <ul>
          <li ng-repeat="card in anki.cardList | filter:anki.search | orderBy:'name'"" ng-click="anki.select(card)">
            {{card.name}}
            <span class="tag" ng-repeat="tag in card.tags">{{tag}}</span>
          </li>
        </ul>
      </nav>
      <div id="question">
        <iframe ng-src="{{anki.selectedCard.question_file}}" width="80%%" height="80%%">
        </iframe>
      </div>
      <div id="answer">
        <iframe ng-src="{{anki.selectedCard.answer_file}}" width="80%%" height="90%%">
        </iframe>
      </div>
  </div>
</body>
</html>""" % (card_list)


    index_filename = "index.html"
    index_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, index_filename), "w", "utf-8")
    index_file.write(html)
    index_file.close()

    stylesheet = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stylesheet.css")
    shutil.copyfile(stylesheet, os.path.join(OUTPUT_DIRECTORY, "stylesheet.css"))