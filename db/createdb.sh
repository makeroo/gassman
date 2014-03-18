#!/bin/bash

sed -e "s/--.*//g" ../gas.ddl | mysql -u gassman -p gassman
