#!/usr/bin/env bash

# remove the docker container -- takes one argument - the container name

if ! ./check_env.sh; then exit 1; fi

_CONT_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";

if [[ $1 != "" ]]; then
  _CONT_NAME="$1";
fi

docker rm --force $_CONT_NAME;
