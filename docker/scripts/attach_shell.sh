#!/usr/bin/env bash
# execute or source this file
# Accepts one optional argument: user name

if ! ./check_env.sh; then exit 1; fi

_CONT_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_HOME="/";

if [[ -n $1 ]]; then
  docker exec -u $1 -w $_HOME -it $_CONT_NAME /bin/bash;
fi

docker exec -w $_HOME -it $_CONT_NAME /bin/bash;

