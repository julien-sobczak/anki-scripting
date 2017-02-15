Bulk Loading
============

Use
---


### Preparation

First, make a copy of your Anki home directory (a backup does not save media files).

```
$ cp -R ~/Documents/Anki ~/Documents/AnkiBackup
```

Then, create a new Anki home folder (an empty one or a copy your existing). To preserve our data, we will load the flashcards in a new profile and export/import the result when we are sure that everything is right.

```
(copy)
$ cp -R ~/Documents/Anki ~/Documents/AnkiWIP

(existing)
$ # Nothing to do, just start Anki by passing a new folder
```

You could now start Anki by passing the correct folder:

```
$ anki -b ~/Documents/AnkiWIP
```

You need to create the note type as describe in the blog post (Tools > Manage Note Types...).

Once done, exit Anki.

Again, make a copy of this anki profile to be able to restore it easily if we corrup the Anki database:

```
$ cp -R ~/Documents/AnkiWIP ~/Documents/AnkiWIPBackup
```

You could create a small script `restore-anki.sh` to automate the restore of the initial version (useful in development):

```
#/bin/bash

rm -Rf ~/Documents/AnkiWIP
cp -R ~/Documents/AnkiWIP ~/Documents/AnkiWIPBackup
```

We are now ready to launch the generation. Let's go!
 

### Loading

Before running the program, check virtualenv is running:

```
$ cd <anki-scripting>
$ source venv/bin/activate
```

We consider the word definitions are present under the folder `<anki-scripting>/anki-vocabulary-assistant/save`

```
$ python load_word.py --from 1 --to 100 --deck "EnglishVocabulary" -f $WORKSPACE/anki-scripting/anki-vocabulary-assistant/save ~/Documents/AnkiWIP/User\ 1
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
$ anki -b ~/Documents/AnkiWIP
```

You should see appear the flashcards. Launch the study mode to see them. If the result looks good, export the deck using the menu `File > Export...`, and exit Anki. Then, launch Anki using the default path (containing the profile you use daily) and use the menu 'File > Import'. Finished!
