#!/usr/bin/env bash

# this script keeps the docker container alive.

service ssh start;

while true; do
  echo "Dev: `date`";
  sleep 60;
done
