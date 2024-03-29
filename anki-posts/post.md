Anki, the most popular SRS (Spaced Repetition System)
=====================================================

= A look inside the Anki model

This is the first post in a series of in-depth articles on Anki. We will begin by understanding the model of Anki, how the different classes interact and when the database is updated when using the application. In the next post, we will discuss the SRS algorithm at the heart of Anki whose main task is to reschedule the cards after each review. We will also cover how to script Anki to bulk load many cards, useful for example when you need to learn the 5000 most common words in a new language.


== Anki Reverse Engineering


Project organization
--------------------

anki/ -> Main Anki logic. Contains the model and the SRS algorithm
  | importing/ -> Logic to import various file formats including Anki1, Anki2, Supermemo (a paid Anki-like tool)
  | template/ -> Anki uses a modified version of Pystache to provide Mustache-like syntax. The templating is using to render flashcards' content.
aqt/ -> Contains Python scripts using PyQT to build the widgets, dialogs and other graphical components that composed the Anki Desktop Application.
designer/ -> contains [PyQT] 4 UI files created using Qt Designer. These files are generated using the command pyuic4.
oldanki/ -> This is libanki 1.2.11, for the purposes of fixing problems when upgrading. This directory could be ignored.
tests/ ->
  | support/ -> Fixtures (anki and anki2 files, PNG media file, ...)
thirdparty/ -> Unit tests based on the framework [Nose]
tools/ -> Simple shell scripts to launch the tests or the UI generation
Makefile -> Basic build script to install or uninstall Anki (simply create folders and move files using mkdir and mv Unix commands)

Anki use QT as graphical framework. The entry point is the script runanki.py:

{{
import aqt
aqt.run()
}}



# Where is stored my cards?

Anki stores your decks in the folder associated to your profile. This folder stores all of your Anki data in a single location, to make backups easy. By default, Anki uses the folder ~/Documents/Anki under your home directory:

{{
def _defaultBase(self):
    if isWin:
        if False: #qtmajor >= 5:
            loc = QStandardPaths.writeableLocation(QStandardPaths.DocumentsLocation)
        else:
            loc = QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
        return os.path.join(loc, "Anki")
    elif isMac:
        return os.path.expanduser("~/Documents/Anki")
    else:
        # use Documents/Anki on new installs, ~/Anki on existing ones
        p = os.path.expanduser("~/Anki")
        if os.path.exists(p):
            return p
        else:
            loc = QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
            if loc[:-1] == QDesktopServices.storageLocation(
                    QDesktopServices.HomeLocation):
                # occasionally "documentsLocation" will return the home
                # folder because the Documents folder isn't configured
                # properly; fall back to an English path
                return os.path.expanduser("~/Documents/Anki")
            else:
                return os.path.join(loc, "Anki")
}}

To tell Anki to use a different location, please see:
http://ankisrs.net/docs/manual.html#startupopts

Let's inspect the different files present under this directory.

~/Documents/Anki
 |- addons: a list of third-party add-ons that you can install directly from Anki > Tools > Add-ons > ... My folder is empty as I have no add-ons installed.
 |- User 1: A folder named after your profile name.
 |   |- backups: The most recent backups automatically created by Anki (30 backups by default maximum)
 |   |   |- backup-88.apkg
 |   |   | ...
 |   |   \- backup-117.apkg
 |   |- collection.media: The list of media included in the cards
 |   |   |- hello.png
 |   |   \- ... (hundreds of images, sounds for my personal folder)
 |   |- collection.anki2 A SQLite database containing all of your decks, cards, ...
 |   |- collection.anki2-journal a binary file
 |   |- collection.log: a log file containing the list of actions (method calls) with their timestamp
 |   |- collection.media.db2 A SQLite database listing all of the media
 |   \- deleted.txt: a log of card deletions acting as the trash bin. The file is always appended and never used directly by Anki.
 \- prefs.db: A SQLite database to contains your preferences.


============================
What is SQLite?

SQLite is a self-contained, serverless, zero-configuration, transactional SQL database engine. SQLite is not directly comparable to client/server SQL database engines such as MySQL, Oracle, PostgreSQL, or SQL Server since SQLite is trying to solve a different problem.

Client/server SQL database engines strive to implement a shared repository of enterprise data. They emphasis scalability, concurrency, centralization, and control. SQLite strives to provide local data storage for individual applications and devices. SQLite emphasizes economy, efficiency, reliability, independence, and simplicity.

So, SQLite does not compete with client/server databases. SQLite competes with fopen() and is particularly well adapted in these situations: as the datastore for an embedded devices, as an application file format (such as Anki), or as the main storage for a medium website or just as a file archive.

Refer to the [official documentation](https://www.sqlite.org/) for more information.
=============================



apkg, anki2, whare are these file extensions?

A anki2* file is DB2


A *apkg file* is just an archive (you could use 7zip or your favorite decompression utility to see its content) containing the anki2 file that we just described and a file media. This media file is a simple text file containing an empty JSON object. As mentioned inside the Preferences dialog, Media is not backed up. We need the create a periodic backup of our Anki folder to be safe. If you use AnkiWeb, our media are already synchronized in the cloud but be careful, decks stored in your account may be archived and eventually deleted if they are not accessed in 3 months or longer. If you are not planning to study for a few months, the manual backup of the content on your own computer is required.




### Misc

#### Interface creation

* Design the dialog with Qt Designer. This create a XML file inside the folder designer/
* Launch the script tools/build_ui.sh from the root of the project

{{
for i in designer/*.ui
do
    base=$(basename $i .ui)
    py="aqt/forms/${base}.py"
    pyuic4 $i -o $py
done
}}

* Use the generated file in your Python application:

In anki/aqt/addcards.py:
{{
form = aqt.forms.addcards.Ui_Dialog()
}}





# Anki Database Schema

The best online description of the database schema is available on GitHub under the Android application source:
https://github.com/ankidroid/Anki-Android/wiki/Database-Structure

Tip: How to inspect the Anki database!

- Download the SQLite DB Browser: http://sqlitebrowser.org/
- Unzip the .apkg file that has been generated
- Open the collection.anki2 with SQLiteBrowser (launch the executable on Windows) (be sure to consider all file extensions)
- You should see dialog like this:

[[include sqlitebrowser-anki2-collection.png]]


-- Cards are what you review.
-- There can be multiple cards for each note, as determined by the Template.
CREATE TABLE cards (
    id              integer primary key,   -- The card id, could be generated randomly
                                           -- Anki uses the epoch milliseconds of when the card was created
    nid             integer not null,      -- nodes.id
    did             integer not null,      -- deck id (available in col table)
    ord             integer not null,      -- ordinal : identifies which of the card templates it corresponds to
                                           -- valid values are from 0 to num templates - 1
                                           -- see the model JSON representation (field tmpls)
    mod             integer not null,      -- modificaton time as epoch seconds
    usn             integer not null,      -- update sequence number: used to figure out diffs when syncing with AnkiWeb.
                                           -- value of -1 indicates changes that need to be pushed to server.
                                           --  usn < server usn indicates changes that need to be pulled from server.
    type            integer not null,      -- 0=new, 1=learning, 2=due
    queue           integer not null,      -- Same as type, but -1=suspended, -2=user buried, -3=sched buried
    due             integer not null,      -- Due is used differently for different card types:
                                           --   new queue: note id or random int
                                           --   due/rev queue: integer day, relative to the collection's creation time
                                           --   learning queue: integer timestamp
    ivl             integer not null,      -- interval (used in SRS algorithm). Negative = seconds, possitive = days
    factor          integer not null,      -- factor (used in SRS algorithm)
    reps            integer not null,      -- The number of reviews (used in SRS algorithm)
    lapses          integer not null,      -- The number of times the card went from a "was answered correctly"
                                           -- to "was answered incorrectly" state (used in SRS algorithm)
    left            integer not null,      -- reps left till graduation (used in SRS algorithm)
    odue            integer not null,      -- original due: only used when the card is currently in filtered deck
                                           -- (used in SRS algorithm)
    odid            integer not null,      -- original did: only used when the card is currently in filtered deck
                                           -- (used in SRS algorithm)
    flags           integer not null,      -- currently unused (always 0)
    data            text not null          -- currently unused (always empty string)
)

-- The collection (contains one or many decks)
-- col contains a single row that holds various information about the collection
CREATE TABLE col (
    id              integer primary key,   -- An integer identifier (1, 2, 3,...)
                                           -- arbitrary number since there is only one row
    crt             integer not null,      -- Creation date, timestamp in seconds (1415070000 for the 2014, 4th November)
    mod             integer not null,      -- Modification date, timestamp in milliseconds.
                                           -- Last time you create a new card or study our flashcards. (
                                           -- 1466770067192 for the 2016, 24th June at 14:07)
    scm             integer not null,      -- Last schema modification date, timestamp in milliseconds
                                           -- If server scm is different from the client scm a full-sync is required
    ver             integer not null,      -- Schema version number of the record.
                                           -- Should be the same as constant SCHEMA_VERSION defined in anki/consts.py
    dty             integer not null,      -- No longer used. Use 0.
    usn             integer not null,      -- The update sequence number: used for finding diffs when syncingwith AnkiWeb
    ls              integer not null,      -- Last sync timestamp in ms.
    conf            text not null,         -- json object containing configuration options that are synced
                                           -- see below
    models          text not null,         -- json array of json objects containing the models (aka Note types)
                                           -- see below
    decks           text not null,         -- json array of json objects containing the deck
                                           -- see below
    dconf           text not null,         -- json array of json objects containing the deck options
                                           -- see below
    tags            text not null          -- a cache of tags used in the collection (probably for autocomplete etc)
                                           -- see below
)

Where:

- Field {{conf}} contains:
/* Various Deck configuration options used by the SRS algorithm */
{
    # review options
    'activeDecks': [1],                -- List of active decks
    'curDeck': 1,                      -- decks.id of the deck to highlight when opening Anki
    'newSpread': NEW_CARDS_DISTRIBUTE, -- whether new cards should be mixed with reviews, or shown first or last
                                       --   NEW_CARDS_DISTRIBUTE = 0
                                       --   NEW_CARDS_LAST = 1
                                       --   NEW_CARDS_FIRST = 2
    'collapseTime': 1200,              -- Used in SRS algorithm
    'timeLim': 0,                      -- Timeboxing limit when reviewing cards (0 => disabed)
    'estTimes': True,                  -- Unused
    'dueCounts': True,                 -- Unused
    # other config
    'curModel': None,                  -- Default model for new cards
    'nextPos': 1,                      -- "select max(due)+1 from cards where type = 0"
    'sortType': "noteFld",             -- On which columns to sort when retrieving cards? (Many options)
    'sortBackwards': False,            -- Should the order be reversed?
    'addToCur': True,                  -- add new to currently selected deck?
}

- Field {{models}} contains:
/* JSON representation of a ModelManager (anki/models.py) */
{
   ...
   "1355577990691":{
      "vers":[],
      "name":"1. Minimal Pairs",
      "tags":[],
      "did":1382740944947,
      "usn":336,
      "req":[
         [0,"any",[0,1,2,3,4,6,7]],
         [1,"any",[0,2,3,4,5,6,7]],
         [2,"all",[8]],
         [3,"all",[8]],
         [4,"all",[8,12]],
         [5,"all",[8,12]]
      ],
      "flds":[
         {"name":"Word 1",                    "media":[], "sticky":false, "rtl":false, "ord":0,  "font":"Arial", "size":20},
         {"name":"Recording 1",               "media":[], "sticky":false, "rtl":false, "ord":1,  "font":"Arial", "size":20},
         {"name":"Word 1 IPA",                "media":[], "sticky":false, "rtl":false, "ord":2,  "font":"Arial", "size":20},
         {"name":"Word 1 English",            "media":[], "sticky":false, "rtl":false, "ord":3,  "font":"Arial", "size":20},
         {"name":"Word 2",                    "media":[], "sticky":false, "rtl":false, "ord":4,  "font":"Arial", "size":20},
         {"name":"Recording 2",               "media":[], "sticky":false, "rtl":false, "ord":5,  "font":"Arial", "size":20},
         {"name":"Word 2 IPA",                "media":[], "sticky":false, "rtl":false, "ord":6,  "font":"Arial", "size":20},
         {"name":"Word 2 English",            "media":[], "sticky":false, "rtl":false, "ord":7,  "font":"Arial", "size":20},
         {"name":"Word 3",                    "media":[], "sticky":false, "rtl":false, "ord":8,  "font":"Arial", "size":20},
         {"name":"Recording 3",               "media":[], "sticky":false, "rtl":false, "ord":9,  "font":"Arial", "size":20},
         {"name":"Word 3 IPA",                "media":[], "sticky":false, "rtl":false, "ord":10, "font":"Arial", "size":20},
         {"name":"Word 3 English",            "media":[], "sticky":false, "rtl":false, "ord":11, "font":"Arial", "size":20},
         {"name":"Compare Word 2 to Word 3?", "media":[], "sticky":false, "rtl":false, "ord":12, "font":"Arial", "size":20}
      ],
      "sortf":0,
      "tmpls":[
         {
            "name":"Card 1",
            "qfmt":"<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 1}}\n<span class=ipa>[{{Word 1 IPA}}]</span>\n<span class=translation>{{Word 1 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 2}}\n<span class=ipa>[{{Word 2 IPA}}]</span>\n<span class=translation>{{Word 2 English}}</span>\n</div>\n</div>\n<br>{{Recording 1}} ",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 1}}</div></b><br><br>\n\n{{Recording 1}}",
            "ord":0,
            "bqfmt":""
         },
         {
            "name":"Card 2",
            "qfmt":"<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 1}}\n<span class=ipa>[{{Word 1 IPA}}]</span>\n<span class=translation>{{Word 1 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 2}}\n<span class=ipa>[{{Word 2 IPA}}]</span>\n<span class=translation>{{Word 2 English}}</span>\n</div>\n</div>\n<br>{{Recording 2}} \n\n",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 2}}</div></b><br><br>\n{{Recording 2}}\n  \n",
            "ord":1,
            "bqfmt":""
         },
         {
            "name":"Card 3",
            "qfmt":"{{#Word 3}}\n<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 1}}\n<span class=ipa>[{{Word 1 IPA}}]</span>\n<span class=translation>{{Word 1 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 3}}\n<span class=ipa>[{{Word 3 IPA}}]</span>\n<span class=translation>{{Word 3 English}}</span>\n</div>\n</div>\n<br>{{Recording 3}} \n{{/Word 3}}",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 3}}</div></b><br><br>\n\n{{Recording 3}}",
            "ord":2,
            "bqfmt":""
         },
         {
            "name":"Card 4",
            "qfmt":"{{#Word 3}}\n<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 1}}\n<span class=ipa>[{{Word 1 IPA}}]</span>\n<span class=translation>{{Word 1 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 3}}\n<span class=ipa>[{{Word 3 IPA}}]</span>\n<span class=translation>{{Word 3 English}}</span>\n</div>\n</div>\n<br>{{Recording 1}} \n{{/Word 3}}",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 1}}</div></b><br><br>\n\n{{Recording 1}}",
            "ord":3,
            "bqfmt":""
         },
         {
            "name":"Card 5",
            "qfmt":"{{#Compare Word 2 to Word 3?}}\n{{#Word 3}}\n<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 2}}\n<span class=ipa>[{{Word 2 IPA}}]</span>\n<span class=translation>{{Word 2 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 3}}\n<span class=ipa>[{{Word 3 IPA}}]</span>\n<span class=translation>{{Word 3 English}}</span>\n</div>\n</div>\n<br>{{Recording 2}} \n{{/Word 3}}\n{{/Compare Word 2 to Word 3?}}",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 2}}</div></b><br><br>\n\n{{Recording 2}}",
            "ord":4,
            "bqfmt":""
         },
         {
            "name":"Card 6",
            "qfmt":"{{#Compare Word 2 to Word 3?}}\n{{#Word 3}}\n<i>Do you hear</i><br><br>\n<div class=container>\n<div class=box>{{Word 2}}\n<span class=ipa>[{{Word 2 IPA}}]</span>\n<span class=translation>{{Word 2 English}}</span>\n</div>\n\n<div class=or><i> or </i></div>\n\n<div class=box>{{Word 3}}\n<span class=ipa>[{{Word 3 IPA}}]</span>\n<span class=translation>{{Word 3 English}}</span>\n</div>\n</div>\n<br>{{Recording 3}} \n{{/Word 3}}\n{{/Compare Word 2 to Word 3?}}",
            "did":null,
            "bafmt":"",
            "afmt":"{{FrontSide}}\n\n<hr id=answer>\n\nYou heard: <div class=box>{{Word 3}}</div></b><br><br>\n\n{{Recording 3}}",
            "ord":5,
            "bqfmt":""
         }
      ],
      "mod":1466769421,
      "latexPost":"\\end{document}",
      "type":0,
      "id":1355577990691,
      "css":".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n.box {\n display:inline-block;\nborder:2px solid black;\npadding:5px;\nfont-size:1.4em\n}\n\n.ipa {\nfont-size:0.7em;\ndisplay:block;\ncolor:blue;\npadding:0 0 5px 0px;\n}\n\n.container {\nborder:0px solid;\ndisplay:table;\nmargin:auto;\n}\n\n.or {\ndisplay:table-cell;\nvertical-align:middle;\npadding:0 10px\n}\n.translation {\nfont-size:0.6em;\ndisplay:block;\ncolor:gray;\n}\n",
      "latexPre":"\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n"
   }
}

{
    css : "CSS, shared for all templates",
    did :
        "Long specifying the id of the deck that cards are added to by default",
    flds : [
             "JSONArray containing object for each field in the model as follows:",
             {
               font : "display font",
               media : "array of media. appears to be unused",
               name : "field name",
               ord : "ordinal of the field - goes from 0 to num fields -1",
               rtl : "boolean, right-to-left script",
               size : "font size",
               sticky : "sticky fields retain the value that was last added
                           when adding new notes"
             }
           ],
    id : "model ID, matches cards.mid",
    latexPost : "String added to end of LaTeX expressions (usually \\end{document})",
    latexPre : "preamble for LaTeX expressions",
    mod : "modification time in milliseconds",
    name : "model name",
    req : [
            "Array of arrays describing which fields are required
                for each card to be generated",
            [
              "array index, 0, 1, ...",
              '? string, "all"',
              "another array",
              ["appears to be the array index again"]
            ]
          ],
    sortf : "Integer specifying which field is used for sorting in the browser",
    tags : "Anki saves the tags of the last added note to the current model",
    tmpls : [
              "JSONArray containing object of CardTemplate for each card in model",
              {
                afmt : "answer template string",
                bafmt : "browser answer format:
                          used for displaying answer in browser",
                bqfmt : "browser question format:
                          used for displaying question in browser",
                did : "deck override (null by default)",
                name : "template name",
                ord : "template number, see flds",
                qfmt : "question format string"
              }
            ],
    type : "Integer specifying what type of model. 0 for standard, 1 for cloze",
    usn : "usn: Update sequence number: used in same way as other usn vales in db",
    vers : "Legacy version number (unused)"
}




- Field {{decks}} contains:
/* JSON representation of a DeckManager (anki/decks.py). One key-value for each deck present in this collection */
{
   "1":{
      "desc":"",
      "name":"Default",
      "extendRev":50,
      "usn":0,
      "collapsed":false,
      "browserCollapsed":true,
      "newToday":[598,0],
      "timeToday":[598,0],
      "dyn":0,
      "extendNew":10,
      "conf":1,
      "revToday":[598,0],
      "lrnToday":[598,0],
      "id":1,
      "mod":1417423954
   }
}

{
    name: "name of deck",
    extendRev: "extended review card limit (for custom study)",
    usn: "usn: Update sequence number: used in same way as other usn vales in db",
    collapsed: "true when deck is collapsed",
    browserCollapsed: "true when deck collapsed in browser",
    newToday: "two number array used somehow for custom study",
    timeToday: "two number array used somehow for custom study",
    dyn: "1 if dynamic (AKA filtered) deck",
    extendNew: "extended new card limit (for custom study)",
    conf: "id of option group from dconf in `col` table",
    revToday: "two number array used somehow for custom study",
    lrnToday: "two number array used somehow for custom study",
    id: "deck ID (automatically generated long)",
    mod: "last modification time",
    desc: "deck description"
}

- Field {{dconf}} contains:
/* JSON representation of a Deck Configuration */


[[include deck-configuration.png]]

{
   "1":{

      "id":1,
      "name":"Default",
      "maxTaken":60,
      "timer":0,
      "autoplay":true,
      "replayq":true,
      "dyn":false,
      "usn":47,
      "mod":1419273593,

      "new":{
         "delays":[1,10],
         "order":0,
         "perDay":1000,
         "ints":[1,4,7],
         "initialFactor":2500,
         "bury":true,
         "separate":true
      },

      "rev":{
         "perDay":100,
         "ease4":1.3,
         "ivlFct":1,
         "maxIvl":36500,
         "bury":true,
         "minSpace":1,
         "fuzz":0.05
      },

      "lapse":{
         "delays":[10],
         "mult":0,
         "minInt":1,
         "leechFails":8,
         "leechAction":0
      }

   }
}

- Field {{tags}} contains:
/* JSON representation of TagManager (anki/tags.py). Contains all tags in the collection with the usn number. (see above) */
{
   "Web":336,
   "Git":336,
   "Java":336,
   "vi":336,
   "Hadoop":336,
   "Productivity":336,
   "Python":336,
   "Refactoring":336,
   "ElasticSearch":336,
   "Bash":336,
   "Training":336,
   "Eclipse":336,
   "Gradle":336,
   "Craftsmanship":336,
   "Patterns":336,
   "Spring":336,
   "Memory":336,
   "Concurrency":336,
   "Algorithms":336,
}


-- Deletion log (content of the file deleted.txt in your Anki home directory)
-- Contains deleted cards, notes, and decks that need to be synced.
-- usn ,
-- oid is the original id.
-- type: 0 for a card, 1 for a note and 2 for a deck
CREATE TABLE graves (
    usn             integer not null,   -- should be set to -1
    oid             integer not null,   -- original id of the Card/Note/Deck
    type            integer not null    -- type: 0 for a card, 1 for a note and 2 for a deck
)

-- Notes contain the raw information that is formatted into a number of cards
-- according to the models
CREATE TABLE notes (
    id              integer primary key,   -- The note id, epoch seconds of when the note was created
    guid            text not null,         -- A globally unique identifier (G8c7ZUgMvt) generated randomly,
                                           -- almost certainly used for syncing
    mid             integer not null,      -- The model id
    mod             integer not null,      -- Modification timestamp, epoch seconds
    usn             integer not null,      -- update sequence number: for finding diffs when syncing with AnkiWeb.
                                           -- See the description in the cards table for more info
    tags            text not null,         -- A space-separated list of tags
                                           -- includes space at the beginning and end, for LIKE "% tag %" queries
    flds            text not null,         -- the values of the fields in this note. separated by 0x1f (31) character.
                                           -- For example, contains: <question>\x1f<answer>.
    sfld            integer not null,      -- sort field: used for quick sorting and duplicate check
                                           -- The value of the field having the index 'sortf' as defined by the model
    csum            integer not null,      -- Field checksum used for duplicate check.
                                           -- 32 bits unsigned integer of the first 8 digits of sha1 hash of the first field of the note
    flags           integer not null,      -- unused. Always 0
    data            text not null          -- unused. Always an empty string
)

-- revlog is a review history; it has a row for every review you've ever done!
CREATE TABLE revlog (
    id              integer primary key,   -- Epoch-seconds timestamp of when you did the review. Initialized to "int(time.time()*1000)"
    cid             integer not null,      -- cards.id
    usn             integer not null,      -- The update sequence number of the collection: for finding diffs when syncing
                                           -- See the description in the cards table for more info
    ease            integer not null,      -- Which button you pushed to score your recall. 1(wrong), 2(hard), 3(ok), 4(easy)
    ivl             integer not null,      -- Interval. Used by SRS algorithm
    lastIvl         integer not null,      -- Last Interval. Used by SRS algorithm
    factor          integer not null,      -- Factor. Used by SRS algorithm
    time            integer not null,      -- How many milliseconds your review took, up to 60000 (60s)
    type            integer not null       -- 0=lrn, 1=rev, 2=relrn, 3=cram
)




# Anki Media Database Schema

CREATE TABLE media (
 fname text not null primary key, -- The filename relative (no path, filename is always relative to media directory)
 csum text,                       -- SHA1 hash on the media file content (null indicates deleted file)
 mtime int not null,              -- mtime of media file. Zero if deleted
 dirty int not null               -- 0 if file up-to-date
)

-- Only one row present
CREATE TABLE meta (
 dirMod int,   -- _mtime of the folder containing the media
 lastUsn int   -- Last synch update timestamp concerning the media folder only (different from Cards USN)
)








= Step by Step

In this part, we will create a new deck and add a new card from scratch using a fresh anki installation.

How to inspect database changes when using Anki?

We could use the sqlite CLI to generate dump before and after each operation executed through the Anki Desktop application.
Download the executable : https://www.sqlite.org/download.html (check the mention "including the command-line shell program" is present on the binary description).

Place the sqlite3.exe along your collection.anki2 file.
Open a interpreter prompt (cmd on Windows)
$ sqlite3 collection.anki2
sqlite>.databases
seq name  file
--- ----- --------------------
0   main  C:\collection.anki2
sqlite>.once dump.sql
sqlite>.dump

By default, sqlite3 sends query results to standard output. So, we use the ".once" command to redirect query results to a file.
(Use the ".output" option to redirect all commands and not just the next one).
Check the official documentation for help about the CLI options: https://www.sqlite.org/cli.html

With the generated dumps, we just have to compare the table data to determine what what exactly update by Anki. So, let's go!




To force Anki to use a fresh installation, we will override the folder location to point to an empty directory (see http://ankisrs.net/docs/manual.html#startupopts for more information about the option -b)

On Windows, just click right on the icon and update the target field to add the option. Ex:
"C:\Program Files (x86)\Anki\anki.exe" -b "D:\AnkiTmp"

Relaunch Anki, select your language, and the home screen should appear, containing only the deck "Default":


[[include anki-home.png ]]
> dump_1_clean.sql

By default, Anki creates the default collection. This is the only row present in database at first:

INSERT INTO "col"(id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)
  VALUES(1,1468375200,1468406322822,1468406322821,11,0,0,0,'{"nextPos": 1, "estTimes": true, "activeDecks": [1], "sortType": "noteFld", "timeLim": 0, "sortBackwards": false, "addToCur": true, "curDeck": 1, "newBury": true, "newSpread": 0, "dueCounts": true, "curModel": "1468406322821", "collapseTime": 1200}','{"1468406322818": {"vers": [], "name": "Cloze", "tags": [], "did": 1, "usn": -1, "flds": [{"size": 20, "name": "Text", "media": [], "rtl": false, "ord": 0, "font": "Arial", "sticky": false}, {"size": 20, "name": "Extra", "media": [], "rtl": false, "ord": 1, "font": "Arial", "sticky": false}], "sortf": 0, "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n", "tmpls": [{"afmt": "{{cloze:Text}}<br>\n{{Extra}}", "name": "Cloze", "qfmt": "{{cloze:Text}}", "did": null, "ord": 0, "bafmt": "", "bqfmt": ""}], "latexPost": "\\end{document}", "type": 1, "id": "1468406322818", "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n\n.cloze {\n font-weight: bold;\n color: blue;\n}", "mod": 1468406322}, "1468406322819": {"vers": [], "name": "Basic (optional reversed card)", "tags": [], "did": 1, "usn": -1, "req": [[0, "all", [0]], [1, "all", [1, 2]]], "flds": [{"size": 20, "name": "Front", "media": [], "rtl": false, "ord": 0, "font": "Arial", "sticky": false}, {"size": 20, "name": "Back", "media": [], "rtl": false, "ord": 1, "font": "Arial", "sticky": false}, {"size": 20, "name": "Add Reverse", "media": [], "rtl": false, "ord": 2, "font": "Arial", "sticky": false}], "sortf": 0, "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n", "tmpls": [{"afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}", "name": "Card 1", "qfmt": "{{Front}}", "did": null, "ord": 0, "bafmt": "", "bqfmt": ""}, {"afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Front}}", "name": "Card 2", "qfmt": "{{#Add Reverse}}{{Back}}{{/Add Reverse}}", "did": null, "ord": 1, "bafmt": "", "bqfmt": ""}], "latexPost": "\\end{document}", "type": 0, "id": "1468406322819", "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n", "mod": 1468406322}, "1468406322821": {"vers": [], "name": "Basic", "tags": [], "did": 1, "usn": -1, "req": [[0, "all", [0]]], "flds": [{"size": 20, "name": "Front", "media": [], "rtl": false, "ord": 0, "font": "Arial", "sticky": false}, {"size": 20, "name": "Back", "media": [], "rtl": false, "ord": 1, "font": "Arial", "sticky": false}], "sortf": 0, "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n", "tmpls": [{"afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}", "name": "Card 1", "qfmt": "{{Front}}", "did": null, "ord": 0, "bafmt": "", "bqfmt": ""}], "latexPost": "\\end{document}", "type": 0, "id": "1468406322821", "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n", "mod": 1468406322}, "1468406322820": {"vers": [], "name": "Basic (and reversed card)", "tags": [], "did": 1, "usn": -1, "req": [[0, "all", [0]], [1, "all", [1]]], "flds": [{"size": 20, "name": "Front", "media": [], "rtl": false, "ord": 0, "font": "Arial", "sticky": false}, {"size": 20, "name": "Back", "media": [], "rtl": false, "ord": 1, "font": "Arial", "sticky": false}], "sortf": 0, "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n", "tmpls": [{"afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}", "name": "Card 1", "qfmt": "{{Front}}", "did": null, "ord": 0, "bafmt": "", "bqfmt": ""}, {"afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Front}}", "name": "Card 2", "qfmt": "{{Back}}", "did": null, "ord": 1, "bafmt": "", "bqfmt": ""}], "latexPost": "\\end{document}", "type": 0, "id": "1468406322820", "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n", "mod": 1468406322}}','{"1": {"name": "Default", "extendRev": 50, "usn": 0, "collapsed": false, "newToday": [0, 0], "timeToday": [0, 0], "dyn": 0, "extendNew": 10, "conf": 1, "revToday": [0, 0], "lrnToday": [0, 0], "id": 1, "mod": 1468406321, "desc": ""}}','{"1": {"name": "Default", "replayq": true, "lapse": {"leechFails": 8, "minInt": 1, "delays": [10], "leechAction": 0, "mult": 0}, "rev": {"perDay": 100, "ivlFct": 1, "maxIvl": 36500, "minSpace": 1, "ease4": 1.3, "bury": true, "fuzz": 0.05}, "timer": 0, "maxTaken": 60, "usn": 0, "new": {"separate": true, "delays": [1, 10], "perDay": 20, "ints": [1, 4, 7], "initialFactor": 2500, "bury": true, "order": 1}, "autoplay": true, "id": 1, "mod": 0}}','{}');

Let's try to create a new deck.

=== Deck creation

[[include anki-new_deck.png]]
> dump_2_new_deck.sql

Internally Anki just update the default collection to add the new deck in the `dconf` field:

{
  "1":             { "name": "Default" ... }
  "1468406431488": {"name": "French",  ... }
}

The code: (aqt/deckbrowser.py#53)

deck = getOnlyText(_("Name for deck:"))
if deck:
    self.mw.col.decks.id(deck)

And in anki/decks.py#125

def id(self, name, create=True, type=defaultDeck):
    "Add a deck with NAME. Reuse deck if already exists. Return id as int."


=== Card creation

[[include anki-new_card.png]]
> dump_3_new_card.sql

Anki update the collection to add the new tag (field `tags`) :
UPDATE col SET tags = '{"vocabulary": -1}' WHERE id = 1
-1 is used to tell Anki to synchronize this tag with the server on the next synchronization with AnkiWeb.

Anki inserts a new row in the table `notes`:

INSERT INTO "notes" VALUES(1468406595423,'c}s`dBG4e-',1468406557944,1468406609,-1,' vocabulary ','PainBread','Pain',2687916407,0,'');

And a new single row in the table `cards` as it is a Basic card:

INSERT INTO "cards" VALUES(1468406609380,1468406595423,1468406570134,0,1468406609,-1,0,0,1,0,0,0,0,0,0,0,0,'');



The code: (aqt/addcards.py)

On dialog opening:

def __init__(self, mw):
    f = self.mw.col.newNote()
    self.editor.setNote(f, focus=True)

When clicking on the Add button:

def addCards(self):
    self.editor.saveTags()
    self.editor.saveAddModeVars()
    note = self.editor.note
    note = self.addNote(note)

def saveTags(self):
    self.note.tags = self.mw.col.tags.canonify(
        self.mw.col.tags.split(self.tags.text()))
    self.tags.setText(self.mw.col.tags.join(self.note.tags).strip())

def saveAddModeVars(self):
    # save tags to model
    m = self.note.model()
    m['tags'] = self.note.tags
    self.mw.col.models.save(m)

def addNote(self, note):
    note.model()['did'] = self.deckChooser.selectedId()
    cards = self.mw.col.addNote(note)


In anki/collection.py

def addNote(self, note):
    "Add a note to the collection. Return number of new cards."



[[include anki-new_reversed_card.png]]
> dump_4_new_reversed_card.sql

Adding a reversed card does not change anything in the UI code. The only difference is the previous method addNode defined in collection.py will returned two cards instead of one in our first card example. In database, two rows will be added in the table `cards`:

INSERT INTO "notes" VALUES(1468406642317,'OfSY=ipt]-',1468406557940,1468406643,-1,' vocabulary ','CarVoiture','Car',3158811612,0,'');
INSERT INTO "cards" VALUES(1468406643702,1468406642317,1468406570134,0,1468406643,-1,0,0,2,0,0,0,0,0,0,0,0,'');
INSERT INTO "cards" VALUES(1468406643703,1468406642317,1468406570134,1,1468406643,-1,0,0,2,0,0,0,0,0,0,0,0,'');


=== Studying

Studying is the act of reviewing our previously created card. After each review, the SRS algorithm runs to reschedule the card. The metadata required by the algorithm are updated to reflect the new due date.

[[include anki-study.png]]

[[include anki-study_card.png]]

For this card, we choose the second button, to check the card in 10 minutes from now.

> dump_5_study_card.sql
> dump_6_study_card_answer.sql (10 min)
> dump_7_finish_study.sql


UPDATE cards
SET type   = 1          -- new => learning
    queue  = 1          -- new queue => learning queue
    due    = 1468407304 -- now + 10 minutes
    ivl    = 0          -- 1 day
    reps   = 1          -- We just did the first review!
    lapses = 0          -- We don't have forgot the answer
    left   = 1001       -- 1001 repetitions left till graduation
WHERE id = 1468406609380

We register the review in the table `revlog`:

INSERT INTO "revlog" (id, cid, usn, ease, ivl, lastIvl, factor, time, type)
    VALUES(
        1468406665035,
        1468406609380, -- card id
        -1,            -- to send on next synchronization
        2,             --
        -600,          -- negative = second (10 minutes)
        -60,           -- last ivl was 1 minutes
        0,
        2016,          -- 2 seconds to answer
        0              -- learning
    );

In the code: (aqt/reviewer.py#259)

def _answerCard(self, ease):
    "Reschedule card and show next."
    self.mw.col.sched.answerCard(self.card, ease)
    self.mw.autosave()
    self.nextCard()

Where answerCard is defined in anki/sched.py#58:

def answerCard(self, card, ease):
    "Entry point to the SRS algorithm"


In anki/collection.py#136:

def autosave(self):
    "Save if 5 minutes has passed since last save."
    if time.time() - self._lastSave > 300:
        self.save()

This method `autosave` explain why Anki need to save when we quit the application. Anki does not save systematically after each command but wait 5 minutes between two saves to minimize the interaction with the database.


We have seen how Anki works under the hood when we add a new deck or a new card and what happens when we practice. We understand the database schema and the main API of Anki. In the next post, we are going to use this knowledge to create programmatically thousands of cards in less than one second without interacting with the Anki application!


[PyQT][https://wiki.python.org/moin/PyQt]
[Nose][https://github.com/nose-devs/nose]


[Anki APKG format unofficial documentation](http://decks.wikia.com/wiki/Anki_APKG_format_documentation)




= Anki Scripting: how to create a collection of flashcards programmatically

This post is the second post in a series of articles on Anki. If the Anki model is new to you, please take 5 minutes and read the previous post.

Adding a new flashcard is the starting point to learn something new. You could customize the content of your flashcard: add a sound with the prununciation of a new word, add a new funny picture to make it more memorable, choose the right word according to your current level on the subject, and so one. But creating flashcards through the UI is time-consuming. What if we need to create thousands of flashcards to learn the 5000 most common words in a particular language?

Anki is an open-source solution, published on GitHub. Code source is accessible to anyone going on the repository. With minimal programming skills, it is easy to script Anki to add new flashcards. Several options are possible:
- insert data directly in the SQLite database used by Anki to store the data permanently
- write a Python program to use the internal API of Anki

This post will concentrate on the second option. The first option could be implemented based on the information published in the first post of this serie but is not the optimal solution (high coupling, necessity to specify all fields when most of them are useless for us). This solution was already partially [documented online](http://decks.wikia.com/wiki/Anki_APKG_format_documentation). The Python solution is more powerful. You could use a Python module to read a PDF or an Epub and generate the associated flashcards or you could use the Google Images API to retrieve funny pictures to integrate in our flashcards. The only limit is our imagination.

Before tackling of problem of bulk loading, let's get started with a more basic use case to help us familiarize with the Anki API. We will export all our flashcards to HTML, probably the most universal format today. If one day, we choose an alternative solution, it would be easy to import our cards to this other tool (most modern tool like Evernote, Google Drive, and many others offers a REST API).



== Case Study: Exporting our collection in raw HTML

Let's begin with a basic version to dump each card answer in its own HTML file.

First, we create a new file `generate_site.py` inside a new folder `userscripts` at the root of the Anki project. The folder hierarchy should be:

anki/
  anki/
  aqt/
  ..
  userscripts/
    generate_site.py

We need to include the anki source in our path to be able to exploit Anki API:

sys.path.append("../anki")
from anki.storage import Collection # OK

We define constants to configure our environment:

PROFILE_HOME = "~/Documents/Anki/User 1"
OUTPUT_DIRECTORY = "/tmp/out"


We start by loading the existing anki collection:

cpath = os.path.join(PROFILE_HOME, "collection.anki2")
col = Collection(cpath, log=True) # Entry point to the API

The class Collection contains a long list of methods and attributes to access the nodes, the cards, and the models.
We use the method `findCards` to restrict the cards to export:



for cid in col.findCards("tag:Git"):

    card = col.getCard(cid)

    # Retrieve the node to determine the card type model
    note = col.getNote(card.nid)
    model = col.models.get(note.mid)

    # Card contains the index of the template to use
    template = model['tmpls'][card.ord]

    # We use a convenient method to evaluate the templates (question/answer)
    rendering = col.renderQA([cid], "card")[0] # Only one element when coming from a given card (cid)
                                               # Could be more when passing a note of type "Basic (with reversed card)"
    question = rendering['q']
    answer = rendering['a']

    css = model['css']

    html = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Card</title>
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

    card_filename = "card-%s.html" % cid
    card_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, card_filename), "w", "utf-8")
    card_file.write(html)
    card_file.close()

The code iterate over the card identifiers and begin by collecting required informations about the card (template, css, ...).
Once this is done, we create the HTML content by injecting the model CSS and the rendered card content (fields are replaced by values with the method `renderQA`).

When running, the program generate a list of files inside the folder defined by the constant `OUTPUT_DIRECTORY`. Here is the content of the file `card-1429876617511.html`:

[[include card-export-html.png]]

To generate an index page listing all the exported cards, we need to update the previous code to store the list of processed card:

cards = {} # Keep a log of processed cards
for cid in col.findCards("tag:Git"):
    # ...
    cards[cid] = {
        'file': card_filename,
        'question': question
    }

Next, we iterate over this list to generate an HTML list before injecting it in an HTML document:

card_list = ''
for cid, props in cards.iteritems():
    card_list += "<li><a href=\"%s\">%s</a></li>" % (props['file'], props['question'])

html = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Anki Export</title>
</head>
<body>
  <ul>
  %s
  </ul>
</body>
</html>""" % (card_list)

index_filename = "index.html"
index_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, index_filename), "w", "utf-8")
index_file.write(html)
index_file.close()

When running the program, a new file index.html is generated inside the target directory:

[[include cards-export-HTML.png]]

The code works but there remains a concern to address: the medias.
Indeed, cards could references external resources like images or sounds all stored in a single folder `collection.media` under your profile directory. So, we need to extract there resources too and update the links inside the card text to reflect the new location.

A basic strategy could be to duplicate the whole folder. To avoid copying resources from cards that we don't want to export, we will instead copy each file independantly while processing the card. So, we have to update the card processing code again:

for cid in col.findCards("tag:Git"):
    # ...
    rendering = col.renderQA([cid], "card")[0]
    question = extractMedia(rendering['q'])
    answer = extractMedia(rendering['a'])


def extractMedia(text):
    regex = r'<img src="(.*?)"\s?/?>'
    pattern = re.compile(regex)

    src_media_folder = os.path.join(PROFILE_HOME, "collection.media/")
    dest_media_folder = os.path.join(OUTPUT_DIRECTORY, "medias")

    # Create target directory if not exists
    if not os.path.exists(dest_media_folder):
        os.makedirs(dest_media_folder)

    # Copy each images referenced by this card
    for (media) in re.findall(pattern, text):
        src = os.path.join(src_media_folder, media)
        dest = os.path.join(dest_media_folder, media)
        shutil.copyfile(src, dest)

    # And don't forget to change the href attribute to reflect the new location
    text_with_prefix_folder = re.sub(regex, r'<img src="medias/\1" />', text)

    return text_with_prefix_folder

When running the program again, you should now see a new folder medias:

out/
  medias/
    paste-2911987826689.jpg

If we open the associated card in our browser, we should see this picture displayed correctly:

[[include card-export-img.png]]


Great! We have successfully exported our anki collection in a standard format but the result does not look good. Let's add a little bit of JavaScript and CSS to make the application more delightful.

What we want is a basic single-page application (SPA) to quickly display our flashcards. A search field will be available at the top of the page to help us filter the cards. Flashcard content will only be displayed when selecting the flashcard title in the list. The following is a draft of this demonstration application:

[[include dessin]]

To add dynamic behaviour to our SPA, we will use AngularJS. AngularJS keep our code clean by separating our model from the view and controller (Pattern MVC). To do that, we are going to convert the static HTML list of cards to JSON format:


card_list = '['
for cid, props in cards.iteritems():
    card_list += "{ 'name': \"%s\", 'file': '%s', 'tags': [ %s ] },\n" % (
        props['name'], props['question_file'], props['answer_file'], "\"" + "\",\"".join(props['tags']) + "\"")
card_list += ']'

We now exploit the card's tags, easily retrieved from the note object:

cards[cid] = {
    'name': rawText(question), # rawText remove HTML tags from front-side content
    'file': card_filename,
    'tags': note.tags
}

We could now redesign our HTML template to integrate the new layout:

html = """<!doctype html>
<html lang="fr" ng-app="ankiApp">
<head>
  <meta charset="utf-8">
  <title>Anki Export</title>
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.5.7/angular.min.js"></script>
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
      <div id="card">
        <iframe ng-src="{{anki.selectedCard.file}}" width="80%%">
        </iframe>
      </div>
  </div>
</body>
</html>""" % (card_list)

We iterate over the JSON array containing the cards we just created. When the user clicks on a card title, the method `select` defined in the controller is called. This method stores the selected card in the model. AngularJS refresh our page and the iframe is updated with the content of the selected flashcard. Last thing to notice, we only displayed the flashcards matching the query entered by the user in the search field.

Let's add the final touch - the CSS:

<style>
 body {
     background-color: #0079bf;
 }
 #search {
     position: fixed;
     height: 70px;
     width: 100%;
     padding-top: 20px;
     text-align: center;
 }
 #search input {
     width: 80%;
     height: 30px;
     border-radius: 15px;
     text-align: center;
     border: none;
     box-shadow: 2px 2px #222;
 }
 #list {
     position: fixed;
     width: 50%;
     top: 70px;
     bottom: 0;
     left: 0;
 }
 #list ul {
     list-style-type: none;
 }
 #list li {
     background-color: white;
     border: 1px solid silver;
     border-radius: 2px;
     font-family: 'Handlee', cursive;
     width: 90%;
     padding: 5px 10px;
     margin-top: 10px;
     margin-bottom: 10px;
     cursor: pointer;
 }
 #card {
     position: fixed;
     width: 50%;
     right: 0;
     top: 270px;
     bottom: 0;
 }
 iframe {
     background-color: white;
     border: none;
     box-shadow: 5px 5px 3px #333;
 }

 .tag {
     float: right;
     margin-right: 10px;
     padding: 2px 5px;
     background-color: orangered;
     color: white;
     font-size: 12px;
     font-family: Arial;
 }
</style>

The layout is divided in three section: the search bar at the top, the list of flashcards on the left and the currently selected flashcard on the right. We use fixed positionning to keep all sections always present on the screen. The results now looks like:


[[include generated-styled-site.png]]


This closes our first case study. We have seen how to exploit the Anki API to consume our data by a program and export them to another format. In the next case study, we are going to use the Anki API to load a batch of cards, created from a book.

Here is the full listing of the code:

==================================
import sys, os, codecs, re, shutil
sys.path.append("..")
from anki.storage import Collection

# Constants
PROFILE_HOME = "C:/Users/Julien/Anki/User 1"
OUTPUT_DIRECTORY = "C:/out"

# Utility methods

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


# Load the anki collection
cpath = os.path.join(PROFILE_HOME, "collection.anki2")
col = Collection(cpath, log=True)

# Iterate over all cards
cards = {}
for cid in col.findCards("tag:Git"):

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

    html = """<!doctype html>
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

    card_filename = "card-%s.html" % cid
    card_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, card_filename), "w", "utf-8")
    card_file.write(html)
    card_file.close()

    cards[cid] = {
        'name': rawText(question),
        'file': card_filename,
        'tags': tags
    }


# Generate a list of all cards
card_list = '['
for cid, props in cards.iteritems():
    card_list += "{ 'name': \"%s\", 'file': '%s', 'tags': [ %s ] },\n" % (
        props['name'], props['file'], "\"" + "\",\"".join(props['tags']) + "\"")
card_list += ']'

html = """<!doctype html>
<html lang="fr" ng-app="ankiApp">
<head>
  <meta charset="utf-8">
  <title>Anki Export</title>
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.5.7/angular.min.js"></script>
  <style>
  body {
    background-color: #0079bf;
}
#search {
    position: fixed;
    height: 70px;
    width: 100%%;
    padding-top: 20px;
    text-align: center;
}
#search input {
    width: 80%%;
    height: 30px;
    border-radius: 15px;
    text-align: center;
    border: none;
    box-shadow: 2px 2px #222;
}
#list {
    position: fixed;
    width: 50%%;
    top: 70px;
    bottom: 0;
    left: 0;
}
#list ul {
    list-style-type: none;
}
#list li {
    background-color: white;
    border: 1px solid silver;
    border-radius: 2px;
    width: 90%%;
    padding: 5px 10px;
    margin-top: 10px;
    margin-bottom: 10px;
    cursor: pointer;
}
#card {
    position: fixed;
    width: 50%%;
    right: 0;
    top: 85px;
    bottom: 0;
}
iframe {
    background-color: white;
    border: none;
    box-shadow: 5px 5px 3px #333;
}
.tag {
    float: right;
    margin-right: 10px;
    padding: 2px 5px;
    background-color: orangered;
    color: white;
    font-size: 12px;
    font-family: Arial;
}
  </style>
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
          <li ng-repeat="card in anki.cardList | filter:anki.search | orderBy:'name'""
              ng-click="anki.select(card)">
            {{card.name}}
            <span class="tag" ng-repeat="tag in card.tags">{{tag}}</span>
          </li>
        </ul>
      </nav>
      <div id="card">
        <iframe ng-src="{{anki.selectedCard.file}}" width="80%%">
        </iframe>
      </div>
  </div>
</body>
</html>""" % (card_list)


index_filename = "index.html"
index_file = codecs.open(os.path.join(OUTPUT_DIRECTORY, index_filename), "w", "utf-8")
index_file.write(html)
index_file.close()
===========================================




= Anki Case Study: Script the creation of our flashcards

Let's me present you the context. We just bought a new [book to learn the common english expressions](https://www.amazon.fr/Harraps-Expressions-anglaises-Collectif/dp/2818704480). This book contains around 4000 expressions. If we consider it takes one minute to create a flashcard, more than 50 hours will be required to overcome this daunting task. So, what can we do?

The solution is to script the creation of the flashcards. If you have never use the Anki API before, please read [my previous post](FIXME) that explain how to extract the information from the Anki database using this API. This post will be divided in two sections. In the first part of this post, we are going to create a small program to read an Epub file in Python. In the second part, we will extend this program to insert the content directly inside our Anki collection.

But does it not preferable to manually create the flashcards in order to retain more easily?

Of course! Creating manually a flashcard is better than automating its creation. When you enter the words on the keyboard, or when you search on Google Images a memorable picture, then you create interactions inside your memory and this considerably help to start fixing the new information. The manual creation is perfectly fine when learning your first words in a new language because it is easy to find a great picture or a personal story about it. But here, we are interested in common expressions, phrases that often does not mean what common sense would say. Relevant memorable pictures are difficult to find, so creating the flashcards manually does not help that much to fix the information in your brain. It is better to spend the 50 or more hours on studying the flashcards than to creating them.



== Part I: Reading the Ebook (Epub)

The book is available in ePub format. The term is short for *electronic publication*. EPUB 3 is currently the most portable ebook format (Amazon has its own proprietary format for its Kindle but every other software readers (Kobo, Bookeen, etc) supports this format.

For our task, we only need to know that an Epub is just a ZIP archive containing a website written in HTML5, including HTML files, images, CSS stylesheets, and other assets like video.

The ebook is subject to a copyright, so to avoid any violation, I rewrite a short version by customizing the text. This demonstration ebook is available in the [repository associated to this post](FIXME). To inspect its content, just unzip the archive:

[[include epub-unzipped.png]]

The first file in the archive must be the `mimetype` file. It must be uncompressed so that non-ZIP utilities can read the mimetype. The `mimetype` file must be an ASCII file that contains the string `application/epub+zip`.

There must be a META-INF directory containing container.xml. This file points to the file defining the contents of the book:

<?xml version="1.0"?>
<container version="1.0"
           xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles>
  <rootfile full-path="OEBPS/volume.opf" media-type="application/oebps-package+xml" />
</rootfiles>
</container>

Apart from mimetype and META-INF/container.xml, the other files (HTML, CSS and images files) are traditionally put in a directory named OEBPS. This directory contains the volume.opf file referenced in the previous file. Here is an example of this file:

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<package xmlns="http://www.idpf.org/2007/opf"
         prefix="cc: http://creativecommons.org/ns"
         version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>Julien's Mes Expressions anglaises</dc:title>
    <dc:language>fr</dc:language>
    <meta content="cover" name="cover"/>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">landscape</meta>
  </metadata>
  <manifest>
    <item href="images/cover.jpg" id="cover" media-type="image/jpeg" properties="cover-image"/>
    <item href="images/Page_1.jpg" id="jpg296" media-type="image/jpeg"/>
    <item href="Page_1.html" id="Page_1" media-type="application/xhtml+xml"/>
    <item href="Page_2.html" id="Page_2" media-type="application/xhtml+xml"/>
    <item href="toc.html" id="toc" media-type="application/xhtml+xml" properties="nav"/>
    <item href="css/ENE.css" id="css288" media-type="text/css"/>
    <item href="_page_map_.xml" id="_page_map_" media-type="application/oebps-page-map+xml"/>
  </manifest>
  <spine page-map="_page_map_">
    <itemref idref="Page_1" linear="yes" properties="page-spread-right"/>
    <itemref idref="Page_2" linear="yes" properties="page-spread-right"/>
  <spine>
</package>

In the manifest section, we can see all web resources included in this epub. This is these files that interested us, in particular the HTML files. If you open the book with an ebook reader (your device or an application like Calibre), you could see the book content:

[[include ebook-preview]]

If you want to know more about the Epub format, O'Reilly devotes whole [books](http://shop.oreilly.com/product/0636920024897.do) on the subject.

Let's see how the HTML looks like. The Page_1.html page contains only a picture with the cover of the book. We could ignore it. The next page Page_2.html is an example of page to parse to extract the english expressions. Here is an extract of this file:


=============================
<?xml version="1.0" encoding="UTF-8" standalone="no"?><html xmlns="http://www.w3.org/1999/xhtml"><head>
<meta charset="utf-8"/>
<meta content="width=1277,height=2048" name="viewport"/>
<title>Page 2</title>
<link href="css/ENE.css" rel="stylesheet" type="text/css"/>
</head>
<body id="Mes-Expressions" lang="fr-FR" style="width: 1277px; height: 2048px;" xml:lang="fr-FR">
<article id="Layout" style="-webkit-transform-origin: 0% 0%; -webkit-transform: scale(4.05545); transform-origin: 0% 0%; transform: scale(4.05545);">
<div class="Bloc-de-texte-standard" id="_idContainer009">
  <div style="width: 5046px; height: 8589px; position: absolute; top: 6.11px; left: 0px; -webkit-transform-origin: 0% 0%; -webkit-transform: scale(0.05); transform-origin: 0% 0%; transform: scale(0.05);">

    <p class="_1_Chapter-Heading_Toc_1 ParaOverride-1" lang="en-GB" xml:lang="en-GB">
      <span class="CharOverride-2" style="position: absolute; top: 0px; left: 793.7px; letter-spacing: -18px;">
        1. Mes mots
      </span>
    </p>

    <p class="_1_IDIOM ParaOverride-1" style="position: absolute; top: 1250.55px; left: 170.08px; letter-spacing: -1px;">
      <span class="Examples1 CharOverride-4">
        Spaced repetition ● Répétition espacée
      </span>
    </p>
    <p class="_2_EXEMPLE-IDIOM ParaOverride-1" style="position: absolute; top: 1546.89px; left: 170.08px; letter-spacing: -3px;">
      <span class="EXEMPLE-IDIO CharOverride-5">
        Spaced repetition is a learning technique.
      </span>
      <span class="TRADUCTION-EXEMPLE-IDIOM CharOverride-7">
        La répétition espacée est une technique d'apprentissage.
      </span>
    </p>
    <p class="WARNING ParaOverride-1"  style="position: absolute; top: 1950.29px; left: 170.08px; letter-spacing: -1px;">
      <span class="CharOverride-10">
        Note: Un logiciel facilitation la répétition espacée est appelé SRS (Spaced Repetition System).
      </span>
    </p>
    <!-- ... --->

  </div>
</div>
</body>
</html>
=============================


If we simplify the HTML definition, we get something like this:

.Bloc-de-texte-standard#_idContainer* -----> New page containing expressions
  .*Chapter-Heading_Toc* ------------------> New category found

  ._1_IDIOM -------------------------------> New idiom found
  .EXEMPLE-IDIO ---------------------------> An example of the idiom examples
  .WARNING --------------------------------> A warning note to complement the idiom

(Where * matches one or many characters)


We now have all the necessary information to begin our program. As our main objective is to create flashcards with Anki API, we will write our program in Python, the same language behind Anki.

First, we need to open each html page and check if this page contains idioms or not:

import codecs

for i in range(2, 3): # Only one page 2 exists in our demo ebook

    # Read the page content
    f = codecs.open("myepub/OEBPS/Page_%s.html" % i, "r", "utf-8")
    page_html = f.read()
    f.close()

    # Parse the HTML
    soup = BeautifulSoup(page_html, 'html.parser')

    # Search the page content
    for bloc in soup.find_all('div', { 'class': 'Bloc-de-texte-standard'}):

        # Only page with id beginning by _idContainer contains idioms
        if bloc.get('id') and bloc.get('id').startswith('_idContainer'):
            process_block(soup, bloc)

Then, for each bloc of idioms, the function `process_block` is called. This method takes two parameters:
- the BeautifulSoup HTML parser,
- the working HTML element

As some idioms cross two pages, we need to keep the chapter number (idioms are group by general subjects), the category (each subject is divided into many related categories) and the current idiom to complete it when we will parsed the next page. To do so, we will use global variables (not good OO-design but a adequate choice for such a simple program). The code consists of a loop to iterate over paragraphs and uses the CSS classes to determine the type of the paragraph (idiom, example or warning). Here is the code:

def process_block(soup, bloc_element):
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
                print "Beginning category %s" % category

        if found:
            continue

        if u'_1_IDIOM' in classes: # New idiom
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
                print "[ERROR] Unable to find translation in example '%s'" % text
        elif u'WARNING' in classes: # WARNING
            idiom.add_warning(p.get_text())
        else:
            print "[ERROR] Unknown class %s" % (classes)

To avoid being polluted with all the `span` tag present in the source (the original epub contains a lot more span!), we use the method `get_text()` of the Soup parser to only extract the raw text. If the paragraph is an idiom, we know the english and french translations are separated by the special character ●. If the paragraph is an example, we search after a phrase separator (dot, question mark, exclamation point, etc). If the paragraph is a warning, we just have the keep the whole text.

For each idiom, we create a new object of type Idiom to group all the information about a given idiom. The collection of idioms is defined globally and will be reused in the second section of this blog post. Here is the definition of the class `Idiom`:


====================================
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

# List of all idioms
idioms = []
====================================

This ends the first section of this post. We have extracted all the relevant text from the ebook. The next big task is to load all of these idioms directly inside Anki.


== Part II: Bulk loading the flashcards

We before the flashcards, we need to design the card template. By default, Anki includes only simple card types: Basic, Basic (with reversed card). These card types have only two fields: the front text, and the back text. We need something more evolved to be able to includes examples and/or note information. We want our cards to look like the following picture:

[[include english-card-type.png]]

We have two solutions: either we create the card type manually using the Anki API directly in Python, or we create the card type through the GUI to benefit the direct feedback when defining the CSS declarations. We will choose the second solution but implementing the first one is relatively easy using code similar to the code we already wrote.

So, run the Anki program, and go to "Tools > Manage Note Types...", click on "Add", and choose "Clone: Basic (with reversed card)" as the model to clone. Name our note type "Idiom".

Comeback to the "Manage Note Types" screen and click on "Fields...". Remove the `Front` and `Back` fields and add four new fields:

[[include note-type-fields.png]]

Close the dialog and click on "Cards...". Again, we need the update the content to match the following screenshot:

[[include note-type-card1.png]]

Here is the full CSS code:

{{{
.card {
 font-family: arial, sans-serif;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}

.qualifier {
  color: black;
  font-style: italic;
  font-weight: normal;
  font-size: 80%;
  letter-spacing: -1px;
}

.idiom .english {
  font-weight: bold;
  font-size: 110%;
}

.example {
  font-size: 18px;
  font-style: italic;
  letter-spacing: -1px;
  line-height: 130%;
}

.english {
  color: #39499b
}
.french {
  color: black;
}

.note {
  color: #333;
  font-size: 16px;
}
}}}

The back card is really close. You only need to invert the `French` and `English` fields as shown in the following screenshot:

[[include note-type-card2.png]]

Then, close Anki to force it to write the changes to disk. Let's go back to our program to add a new line at the end of the source code:

{{{
bulk_loading_anki(idioms)
}}}

The function `bulk_loading_anki` is responsible to iterate over the idioms, and create a new note for each of them. Before that, we need to retrieve our new note type `Idiom` to define it as the default (like we do when we use Anki through the UI). We also need to retrieve the deck in which to create the notes (`English` in our example for any deck would works). Here is the code.

{{{
def bulk_loading_anki(idioms):

    # Load the anki collection
    cpath = os.path.join(PROFILE_HOME, "collection.anki2") (1)
    col = Collection(cpath, log=True) (2)

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
                % (example['en'], example['fr']) (3)

        for warning in idiom.warnings:
            note_field += '<p class="warning">%s<p>' % warning

        note.fields[0] = english_field (4)
        note.fields[1] = french_field
        note.fields[2] = examples_field
        note.fields[3] = note_field

        print "{\nEnglish: %s,\nFrench: %s,\nExamples: %s,\nNotes: %s}" % (
            note.fields[0], note.fields[1], note.fields[2], note.fields[3])

        # Set the tags (and add the new ones to the deck configuration
        tags = "idiom"
        note.tags = col.tags.canonify(col.tags.split(tags))
        m = note.model()
        m['tags'] = note.tags
        col.models.save(m)

        # Add the note
        col.addNote(note)

    # Save the changes to DB
    col.save() (5)
}}}


(1) Load the collection from the local disk
(2) The code reflects the Anki terminology (note, card, field, deck, tag, etc). If some term are unclear to you, check the official documentation.
(3) CSS classes defined in the note type could be used to stylize our cards. Unlike the desktop application, HTML is not escaped.
(4) The order of the fields should follow the same order as defined in the GUI
(5) Without the explicit call to the `save` method, the flashcards would not be saved to disk. Indeed, the Anki application schedules a task every 5 minutes to call this method.

The function `highlight_qualifier` used in the previous code is defined like this:

{{{
def highlight_qualifier(text):
    """ Surround text in parenthesis with a stylized HTML tag. """
    return re.sub(r'[(](.*?)[)]', r'<span class="qualifier">(\1)</span>', text)
}}}

Rerun the program and open Anki again. You should see thousands of new card to study! (Go to "Browse" and select the "idiom" tag  to see them all).

Our case study is over. We have converted an ebook purchased online to thousands of flashcards to learn with just one hundred line of Python code. In the case study, we are going to create flashcards for the most common words in a language (the first step before learning idioms but more complex to automate).



= Anki Scripting: Case Study II: Learn the 5000 most frequent words

Learning the vocabulary of a new language is good use case for Anki. You can found frequency books for your target language on Amazon or you can use resources like Wikipedia: [https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists](https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists).

In this post, we are targeting the english language.


== The frequency list

Wikipedia currently offers multiple frequency lists based on different sources: films, project Gutenberg containg thousand of freely available classic romans, and even the integral of the Simpsons episodes. The lists are splitted in many pages (1-999, 1000-1999, and so on). By using the browser developer tool (Google Developer Tool on Chrome and Firebug on Firefox), we could easily extract the HTML to create a single HTML file contaning the entire list. Here is a sample of the list based on the project Gutenberg:

40000_frequency_list_gutenberg.txt
====
<table>
<tbody><tr>
<td><b>Rank</b></td>
<td><b>Word</b></td>
<td><b>Count (per billion)</b></td>
</tr>
<tr>
<td>1</td>
<td><a href="/wiki/the" title="the">the</a></td>
<td>56271872</td>
</tr>
<tr>
<td>2</td>
<td><a href="/wiki/of" title="of">of</a></td>
<td>33950064</td>
</tr>
<tr>
<td>3</td>
<td><a href="/wiki/and" title="and">and</a></td>
<td>29944184</td>
</tr>
... <!-- 39 997 other entries -->
</table>
====

Note: Like your browser, most HTML parsers are very tolerant concerning HTML syntax. We do not even have to create a perfectly valid HTML document to be able to parse it. We will continue to use the Python language in this post, and the most popular HTML parser is [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

Here is a basic program to parse this HTML file and generate a csv file:

===
TODO
===

We now have a frequency list based on old books. To avoid missing common usual words nowadays, we do the same thing with the TV frequency list. This results in two files `40000_frequency_list_gutenberg.csv` and `40000_frequency_list_tv.csv` having most of the words in common but with different rankings. We need to merge the two list. Here is a program to merge the two list and produces a CSV file containing two fields: the rank and the word.


====
import sys
import codecs
import operator


# Contains the merge of the two lists.
frequencies = {}
# word: [rank_1, rank_2] if present in both files


def fill_words(filename):
    global frequencies

    for line in codecs.open(filename, "r", "utf-8"):
        (rank, word, frequency) = line.split(",")
        if not word in frequencies:
            frequencies[word] = []
        frequencies[word].append(int(rank))


# Read the files to parse
fill_words("40000_frequency_list_gutenberg.csv")
fill_words("40000_frequency_list_tv.csv")


# Calculate the average rank (ex: TV 30250, Gutenberg 27500 => 28875)
frequencies_avg = {}
for word, ranks in frequencies.iteritems():
    rank = int(reduce(lambda x, y: x + y, ranks) / len(ranks))
    frequencies_avg[word] = rank


# Sort the dictionary by value (rank)
frequencies_sorted = sorted(frequencies_avg.items(), key=operator.itemgetter(1))


# Output a new CSV with incrementing rank
# (previous ranking calculation produces words with the same rank)
i = 0
for word, rank in frequencies_sorted:
    i += 1
    print("%s,%s" % (i, word))
===

To generate the new list:

$ python calculate_frequency_list.py > my_english_frequency_list.csv


If we inspect the resulting file, we notice numerous unwanted words such as "Mickey". Let's remove them by updating our program:


===
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

frequencies_avg = {}
for word, ranks in frequencies.iteritems():
    if filter(word): # New
        continue     # New
    rank = int(reduce(lambda x, y: x + y, ranks) / len(ranks))
    frequencies_avg[word] = rank
===

We have not finished. If we look again at the output, we notice words sharing the same radical (ex: bill/bills, displease/displeased). These words could not be filtered as before but could only be removed at the end of the program (when we are sure we have found the verb or noun). So, let's update our program to add the following code just before printing the result:

===
frequencies_avg_copy = frequencies_avg.copy() # Work on copy to delete during iteration
for word, rank in frequencies_avg_copy.iteritems():

    if word.endswith("ing"): # eat/eating
        adverb_word = word
        verb = word[:len(word) - 3]
        if adverb_word in frequencies_avg and verb in frequencies_avg:
            del frequencies_avg[adverb_word]

    if word.endswith("ies"): # lady/ladies
        third_person_verb = word
        verb = word[:len(word) - 3] + "y"
        if third_person_verb in frequencies_avg and verb in frequencies_avg:
            del frequencies_avg[third_person_verb]

    if word.endswith("ed"):
        adjective_word = word

        word1 = word[:len(word) - 2] # fill => filled
        if adjective_word in frequencies_avg and word1 in frequencies_avg:
            del frequencies_avg[adjective_word]

        word2 = word[:len(word) - 1] # displease => displeased
        if adjective_word in frequencies_avg and word2 in frequencies_avg:
            del frequencies_avg[adjective_word]

    if word.endswith("s"): # bill/bills
        plural_word = word
        singular_word = word[:len(word) - 1]
        if plural_word in frequencies_avg and singular_word in frequencies_avg:
            del frequencies_avg[plural_word]
====



== The definitions

When learning a new language, it is better to left out completely your tongue language of our flashcards. Popular flashcard application Memrise does exactly that. Instead, we will include the definition written in the same language as the word. To do so, we will use Wiktionary. Like its sister project Wikipedia, Wiktionary is run by the Wikimedia Foundation, and is written collaboratively by volunteers. This dictionary is available in 172 languages and probably contains the most exhaustive list of words (500 000 words for the english dictionary!).


=== Reading the data

Wiktionary, like other Wikimedia projects, offers a [REST API](https://en.wiktionary.org/w/api.php) to retrieve a single page. The API is still in active development. Another option is to exploit the [generated dumps](https://dumps.wikimedia.org/). Indeed, Wikimedia hosts numerous dumps of its database (useful for example in natural language processing tasks or for reseach project). The one that interest us is the [enwiktionary dump](https://dumps.wikimedia.org/enwiktionary/), in particular the first archive described as "Articles, templates, media/file descriptions, and primary meta-pages".

Once downloaded, we extract the tar.gz archive to find a single XML file with a size of 4,5 GB!


=== Parsing the Wiktionary dump

====
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://w
ww.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mediawiki.org/
xml/export-0.10/ http://www.mediawiki.org/xml/export-0.10.xsd" version="0.10" xm
l:lang="en">
  <page>
    <title>free</title>
    <ns>0</ns>
    <id>19</id>
    <revision>
      <id>38832709</id>
      <parentid>38719386</parentid>
      <timestamp>2016-06-17T20:55:44Z</timestamp>
      <contributor>
        <username>DTLHS</username>
        <id>794618</id>
      </contributor>
      <comment>/* English */</comment>
      <model>wikitext</model>
      <format>text/x-wiki</format>
      <text xml:space="preserve">{{also|-free}}
==English==
{{wikipedia|dab=free}}

===Etymology===
From {{etyl|enm|en}} {{m|enm|free}}, {{m|enm|fre}}, {{m|enm|freo}}, from {{etyl|ang|en}} {{m|ang|frēo||free}}, from {{etyl|gem-pro|en}} {{m|gem-pro|*frijaz||free}}, from {{etyl|ine-pro|en}} {{m|ine-pro|*preyH-||to be fond of}}. Cognate with West Frisian {{m|fy|frij||free}}, Dutch {{m|nl|vrij||free}}, Low German {{m|nds|free||free}}, German {{m|de|frei||free}}, Danish {{m|da|fri||free}}.

The verb comes from {{etyl|enm|en}} {{m|enm|freen}}, {{m|enm|freoȝen}}, from {{etyl|ang|en}} {{m|ang|frēon}}, {{m|ang|frēoġan||to free; make free}}.

===Pronunciation===
* {{IPA|/fɹiː/|lang=en}}
* {{audio|en-us-free.ogg|Audio (US)|lang=en}}
* {{audio|En-uk-free.ogg|Audio (UK)|lang=en}}
* {{rhymes|iː|lang=en}}

[[File:Free Beer.jpg|thumb|A sign advertising '''free''' beer (obtainable without payment)]]
[[File:Buy one, get one free ^ - geograph.org.uk - 153952.jpg|thumb|A &quot;buy one get one '''free'''&quot; sign at a flower stand (obtainable without additional payment)]]
[[File:Berkeley Farms Fat-Free Half &amp; Half.jpg|thumb|This food product is labelled &quot;fat '''free'''&quot;, meaning it contains no fat]]

===Adjective===
{{en-adj|er}}

# {{label|en|social}} [[unconstrained|Unconstrained]].
#: {{ux|en|He was given '''free''' rein to do whatever he wanted.}}
#* {{quote-book|year=1899|author={{w|Stephen Crane}}
|title=[[s:Twelve O'Clock|Twelve O'Clock]]|chapter=1
|passage=There was some laughter, and Roddle was left '''free''' to expand his ideas on the periodic visits of cowboys to the town. “Mason Rickets, he had ten big punkins a-sittin' in front of his store, an' them fellers from the Upside-down-F ranch shot 'em up […].”}}
#* {{quote-magazine|date=2013-08-10|volume=408|issue=8848|magazine={{w|The Economist}}|author=Schumpeter
|title=[http://www.economist.com/news/business/21583242-businesspeople-have-become-too-influential-government-cronies-and-capitols Cronies and capitols]
...
   <sha1>sbauh4n08a6ktob42jxeoye85e0w9tb</sha1>
    </revision>
  </page>
  <!-- Million of pages... -->
</mediawiki>
===

Note: only the title and text tag are interesing for our use case.

To parse such a large file, we need a XML parser that do not load the full file in memory. So, we will use a SAX Parser. Unlike a DOM parser, it is not possible to simply traverse the XML document to extract the relevant information. SAX Parsers are event-driven. We need to listen to each new tag, each character text, and so on. We also need to memorise our position inside the file to answer question like "Does the text correspond to the title tag?". Here is the program to extract the id, title, and text and generate another XML file containing only the english word (the dictionary contains all dictionary written in english, such as the French -> English dictionary). The result is a file less than 300 Mb, that does not take 45 minutes to be parsed.

parse_wiktionary.py
{{{
"""
Parse a XML wiktionary dump using a SAX parser (humongous file!).
Produces another XML files containing only the english words with their id and the full text.
"""

import xml.sax
import codecs
import sys


class ABContentHandler(xml.sax.ContentHandler):

    def __init__(self, frequency_list = None):
        xml.sax.ContentHandler.__init__(self)
        self.frequency_list = frequency_list

        # Flag to determine our current position inside the XML file
        self.in_page = False
        self.in_id = False
        self.in_title = False
        self.in_text = False

        # Variables to hold informations about the currently processed element
        self.id = None
        self.title = None
        self.text = None

        # Counter to count the number of english word found
        self.filtered_words = 0
        self.all_words = 0

    def startElement(self, name, attrs):
        if name == "page":
            self.in_page = True
        if self.in_page and name == "id":
            self.in_id = True
        if self.in_page and name == "title":
            self.in_title = True
        if self.in_page and name == "text":
            self.in_text = True
            self.text = ""

    def characters(self, content):
        if self.in_title:
            self.title = content
        elif self.in_id:
            self.id = content
        elif self.in_text:
            self.text += content

    def _append_word(self):
        global output_file
        self.filtered_words += 1
        if self.frequency_list:
            self.frequency_list[self.title] = True
        output_file.write("  <entry>\n")
        output_file.write("    <id>%s</id>\n" % self.id)
        output_file.write("    <title>%s</title>\n" % self.title)
        output_file.write("    <text xml:space=\"preserve\"><![CDATA[\n")
        output_file.write("%s\n" % self.text)
        output_file.write("    ]]></text>\n")
        output_file.write("  </entry>\n")

    def endElement(self, name):
        if name == "page":
            self.in_page = False
            self.all_words += 1

            # Remove non-english words
            # Remove category title (ex: Index:Spanish)
            # Remove words beginning by an Uppercase BUG
            if "==English==" in self.text[:200] \
                    and not ":" in self.title \
                    and self.title != self.title.title():

                if not self.frequency_list or self.title in self.frequency_list:
                    self._append_word()

        if self.in_page and name == "title":
            self.in_title = False
        if self.in_page and name == "id":
            self.in_id = False
        if self.in_page and name == "text":
            self.in_text = False

if __name__ == "__main__":

    # Read the frequency to filter the words
    frequency_list = {}
    for line in codecs.open("my_english_frequency_list.csv", "r", "utf-8"):
        (rank, word) = line.strip().split(',')
        frequency_list[word] = False

    # Read the
    output_file = codecs.open("enwiktionary-frequency.xml", "w", "utf-8")
    output_file.write("<dictionary>\n")
    source = open("D:/Projects/enwiktionary-20160720-pages-articles-multistream.xml")
    xml.sax.parse(source, ABContentHandler(frequency_list))
    output_file.write("</dictionary>\n")
    output_file.close()

# Results:
# - 34 307 common words extracted from 615 209 english words among a total of 5 113 338 words.
}}}

When running the program, a new file enwiktionary-frequency.xml should appear in the current folder. Here is an excerpt of its content:


{{
<dictionary>
  <entry>
    <id>45268</id>
    <title>dictionary</title>
    <text xml:space="preserve"><![CDATA[
{{also|Dictionary}}
==English==
{{wikipedia|dab=Dictionary (disambiguation)|Dictionary}}

===Etymology===
{{PIE root|en|deyḱ}}
{{etyl|ML.|en}} {{m|la|dictionarium}}, from {{etyl|la|en}} {{m|la|dictionarius}}, from {{m|la|dictio||speaking}}, from {{m|la|dictus}}, perfect past participle of {{m|la|dīcō||speak}} + {{m|la|-arium||room, place}}.

===Pronunciation===
* {{a|RP}} {{IPA|/ˈdɪkʃ(ə)n(ə)ɹɪ/|lang=en}}
* {{a|GenAm|Canada}} {{enPR|dĭk'shə-nĕr-ē}}, {{IPA|/ˈdɪkʃənɛɹi/|lang=en}}
* {{audio|en-us-dictionary.ogg|Audio (US)|lang=en}}
* {{audio|en-uk-dictionary.ogg|Audio (UK)|lang=en}}
* {{hyphenation|dic|tion|ary|lang=en}}

===Noun===
{{en-noun|dictionaries}}

# A [[reference work]] with a list of [[word]]s from one or more languages, normally ordered [[alphabetical]]ly, explaining each word's meaning, and sometimes containing information on its etymology, pronunciation, usage, translations, and other data.
...
    ]]></text>
  </entry>
  <entry>
    <id>794618</id>
    <title>free</title>
    <text xml:space="preserve"><![CDATA[
      ...
    ]]></text>
  </entry>
  ...
</dictionary>

===Etymology===

}}

This file could quickly be parsed (10s on my local machine). The next step is to parse the value of the `text` tag to extract all relevant information.

=== Parsing the x-wiki text to generate a JSON file

The <text> tag contains a x-wiki document whose main syntax is defined [here](http://platform.xwiki.org/xwiki/bin/view/Main/XWikiSyntax). Wikipedia add a lot of semantic above this syntax to defined semantic through the use of numerous labels. I did not find a document to describe the Wiktionary special syntax, so we need to reverse engineer the format.

Here is a abbreged example of a x-wiki document (the word `keyboard`):

====
{{also|Keyboard}}
==English== // <1>
{{wikipedia|dab=keyboard|lang=en}}
[[Image:Player piano keyboard.jpg|thumb|100px|A piano keyboard]]

===Etymology===
From {{compound|key|board|lang=en}}.

===Pronunciation===
* {{a|US}} {{IPA|/ˈkibɔ˞d/|lang=en}}
* {{a|UK|Australia}} {{IPA|/ˈkiːbɔːd/|lang=en}}
* {{audio|En-us-keyboard.ogg|Audio (US)|lang=en}}

===Noun=== // <2>
{{en-noun}}

# {{lb|en|computing|etc.}} A set of keys used to operate a [[typewriter]], [[computer]] etc.
# {{lb|en|music}} A component of many [[instruments]] including the [[piano]], [[organ]], and [[harpsichord]] consisting of usually black and white keys that cause different tones to be produced when struck.
# {{lb|en|music}} A device with keys of a musical keyboard, used to control [[electronic]] sound-producing devices which may be built into or separate from the keyboard device.

====Synonyms====
* {{sense|electronic musical device}} {{l|en|electronic keyboard}} // <3>

====Related terms====
* {{l|en|key}}
* {{l|en|keypad}}

====Translations==== // <4>
{{trans-top|set of keys used to operate a typewriter, computer etc.}}
* Breton: {{t|br|klavier|m}}
* Dutch: {{t+|nl|toetsenbord|n}}, {{t+|nl|klavier|n}}
* French: {{t+|fr|clavier|m}} // <3>
{{trans-bottom}}

{{trans-top|component of many instruments}}
* Breton: {{t|br|klavier|m}}
*: Mandarin: {{t+|cmn|鍵盤|sc=Hani}}, {{t+|cmn|键盘|tr=jiànpán|sc=Hani}}
* Dutch: {{t+|nl|klavier|n}}, {{t+|nl|keyboard|n}}
* French: {{t+|fr|clavier|m}}
* German: {{t+|de|Tastatur|f}}, {{t+|de|Klaviatur|f}}, {{t+|de|Manual|n}}
{{trans-bottom}}

===Verb=== // <2>
{{en-verb}}

# {{lb|en|intransitive}} To [[type]] on a [[computer]] keyboard.
#: '' '''Keyboarding''' is the part of this job I hate the most.''

====Translations==== // <4>
{{trans-top|to type in}}
*: Mandarin: {{t+|cmn|打字|tr=dǎzì|sc=Hani}}
* French: {{t+|fr|clavier}}
* Greek: {{t|el|πληκτρογραφώ}}, {{t+|el|πληκτρολογώ}}
{{trans-bottom}}

----

==Dutch== // <1>

===Pronunciation===
* {{audio|Nl-keyboard.ogg|Audio|lang=nl}}
* {{hyphenation|key|board|lang=nl}}

===Etymology===
{{borrowing|en|keyboard|lang=nl}}.

===Noun===
{{nl-noun|n|-s|keyboardje}}

# {{lb|nl|computing|music}} {{l|en|keyboard}}

====Synonyms====
* {{sense|computing}} {{l|nl|toetsenbord}}
====

<1> A wiktionary entry contains the text of multiple dictionaries (English-English, English-Dutch). Only the English-English dictionary is relevant when learning the english language.
<2> A given word could used as a noun, a verb, etc. We need to extract the definition for each type while keeping note of the type.
<3> Label syntax such as {{t+|fr|clavier|m}} is used exhaustively inside the wiki text. Most of the text is containing inside these labels but the syntax is not easily parsable.
<4> There are many translation blocks. Often, the first one is the only translation we are interested.

On this example, the definitions are easily parsable but not words are so simple. Consider the word 'car':

Image:wiktionary-car.png[]

Here the same content as x-wiki:

====
====Noun====
{{en-noun}}

# {{lb|en|dated}} A [[wheeled]] [[vehicle]], drawn by a [[horse]] or other animal.
# A wheeled vehicle that moves independently, with at least three wheels, powered mechanically, steered by a driver and mostly for personal [[transportation]]; a [[motorcar]] or [[automobile]].
#: ''She drove her '''car''' to the mall.''                    // <1>
#* {{quote-book|year=2006|author=[[w:Edwin Black|Edwin Black]] // <2>
|title=Internal Combustion
|chapter=1|url=http://openlibrary.org/works/OL4103950W
|passage=If successful, Edison and Ford—in 1914—would move society away from the ever more expensive and then universally known killing hazards of gasoline '''cars''':&nbsp;[&hellip;]&thinsp;.}}
# {{lb|en|rail transport|chiefly|North America}} An unpowered unit in a [[railroad]] train.
#: ''The conductor coupled the '''cars''' to the locomotive.''
====

<1> Quotes could be on a line starting with `#:`, be surround with `''`
<2> While other quotes could be a line containing a label where the attribute `passage` contains the quote text.

This is only one subtlety among many others. Wiktionary syntax is full of surprise but also full of interesting content.

So, we will create another Python program to parse the previously generated XML file. The aim of to generate a structured JSON file with only the required information. For example:

===
{
  "title":"car",
  "id":"3184799",
  "ipa":"/k\u0251\u02d0/",
  "rank":683,

  "audio":"En-uk-a car.ogg",
  "audio_url":"http://upload.wikimedia.org/wikipedia/commons/3/31/En-uk-a car.ogg",

  "images":[
    {
      "description":"Diagram for the list (42 69 613). The [[car",
      "filename":"Cons-cells.svg",
      "thumb_url":"http://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Cons-cells.svg/600px-Cons-cells.svg",
      "url":"http://upload.wikimedia.org/wikipedia/commons/1/1b/Cons-cells.svg"
    }
  ],

  "types":[
    {
      "type":"Noun",
      "definitions":[
        { "text":"(dated) A wheeled vehicle, drawn by a horse or other animal." },
        {
          "text":"A wheeled vehicle that moves...",
          "quotations":[
            "She drove her <em>car</em> to the mall."
          ]
        },
        {
          "text":"(rail transport, chiefly, North America) An unpowered unit in a railroad train.",
          "quotations":[
            "The conductor coupled the <em>cars</em> to the locomotive."
          ]
        }
       ]
     }
  ],

  "synonyms":[
    "(private vehicle that moves independently) auto, motorcar",
    "(non-powered part of a train) railcar, wagon"
  ],

  "translations":[
    "char",
    "auto",
    "automobile",
    "voiture"
  ]
}
===

The code contains a lot of parsing logic and the result is not the most beautiful code that I wrote. I am not going to present the content in this post but if you are curious, the full listing is available in the project repository in [GitHub](TODO).


==== Creating the flashcards.

Unlike the previous case study on idioms, creating flashcards for vocabulary is most complicated for different reasons:

- Some word contains more than ten definitions or examples. Should we add them all?
- Not all word would benefit from a memorable image (ex: alphabetically)
- Not all word have a pronunciation sound in Wiktionary
- Which type of notes? Find the word from the image only, the sound only, a given definition, find the translation of the word, etc. There is so many possibilities.

All of these point hightlight that we can not write a program to automatically take all the decisions for us. So, we will create a basic web application to display the definitions, the examples, and a list of candidate images retrieved from Google Maps. Each of these elements will be accompagnied with a checkbox to let the user choose the most relevant definitions and examples and select the most memorable picture and not select a picture at all. If a sound is present in Wiktionary, we will systematically add it to the flashcard.

 Here is a screenshot of this application:

 Image:TODO[Check the information to include in the flashcard. According the choice, the program will create different notes]



