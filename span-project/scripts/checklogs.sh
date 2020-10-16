#!/usr/bin/env bash

BASE_DIR=/home/codeman/.itsoflife/mydata/local/logs
LOGS_DIR=$BASE_DIR/span-logs

cd $LOGS_DIR;

egrep -n -A 4 "ERROR|WARN" ./*;



