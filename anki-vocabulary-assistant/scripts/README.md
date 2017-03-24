Bulk Loading
============

Use
---


### Preparation

First, make a copy of your Anki home directory (a backup does not save media files).

```
$ cp -R AnkiModel AnkiTest
```

Inside the current folder, run the script `restore-anki.sh` to generate a folder `AnkiTest` in the same directory. 

### Loading

Before running the program, check virtualenv is running:

```
$ cd <anki-scripting>
$ source venv/bin/activate
```

We consider the word definitions are present under the folder `<anki-scripting>/anki-vocabulary-assistant/save`

```
$ python load_word.py --from 1 --to 100 --deck "EnglishVocabulary" -f $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save ./AnkiTest/User\ 1
...
Opening file $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save/57-by.json
Copying media file $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save/57-by.ogg to ~/Documents/AnkiWIP/User 1/collection.media/57-by.ogg
Opening file $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save/26-we.json
Copying media file $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save/26-we.ogg to ~/Documents/AnkiWIP/User 1/collection.media/26-we.ogg
...
```

This example generates the flashcards for the first 100 words. 


### Verification

We just have to run Anki again:

```
$ anki -b ./AnkiTest
```

Note: Anki should be run in Python 2 (current virtualenv uses Python 3)

You should see appear the flashcards. Launch the study mode to see them. If the result looks good, export the deck using the menu `File > Export...`, and exit Anki. Then, launch Anki using the default path (containing the profile you use daily) and use the menu 'File > Import'. Finished!

Note: If you need to repeat the procedure, just rerun the script `restore-anki.sh` to start from a fresh installation again.
