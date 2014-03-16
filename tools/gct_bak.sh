#!/bin/bash

BACKUPDIR=~/backup

DBUSER=$1
DBNAME=$2
DEST=$3

if [ -z "$DBUSER" ] ; then
  echo >&2 Missing db user
  exit 1
fi
if [ -z "$DBNAME" ] ; then
  echo >&2 Missing db name
  exit 1
fi
if [ -z "$DEST" ] ; then
  echo >&2 Missing dest
  exit 1
fi

NOW=`date +%Y%m%d-%H%M%S`

DBDUMP=$BACKUPDIR/$DBNAME_db_$NOW.sql.bz2

mysqldump -u $DBUSER $DBNAME | bzip2 >$DBDUMP

MAILBODY=`mktemp`

echo Attached > $MAILBODY

mpack -s "Gassman db backup" -d $MAILBODY $DBDUMP $DEST

rm $MAILBODY
