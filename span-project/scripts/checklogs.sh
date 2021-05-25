#!/usr/bin/env bash

_BASE_DIR=/home/codeman/.itsoflife/mydata/local/logs
_LOGS_DIR=$_BASE_DIR/span-logs

mkdir -p $_LOGS_DIR || exit;
cd $_LOGS_DIR || exit;

egrep -n -A 4 "ERROR|WARN" ./*;



