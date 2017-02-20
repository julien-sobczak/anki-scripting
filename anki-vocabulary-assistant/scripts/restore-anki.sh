#/bin/sh

# check we are in the right folder
ls restore-anki.sh > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "This script could only be run in the file folder"
  exit $?
fi

# Copy the reference folder
rm -Rf AnkiTest
cp -R AnkiModel AnkiTest

