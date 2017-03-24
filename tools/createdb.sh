#!/bin/bash

COMMAND="`which $0`"
COMMAND_HOME="`dirname "$COMMAND"`"

sed -e "s/--.*//g" $COMMAND_HOME/src/main/sql/gas.ddl | mysql -u gassman -p gassman
