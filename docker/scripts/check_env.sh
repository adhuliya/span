#!/usr/bin/env bash


_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";

if [[ -z $DOCKER_IMG_PREFIX || -z $DOCKER_IMG_SUFFIX ]]; then
  echo "ERROR: Illformed container/image name: '$_NAME'";
  exit 1;
fi

# successful exit
exit 0;

