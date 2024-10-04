#!/usr/bin/env bash

# view docker logs (its stdout)

if ! ./check_env.sh; then exit 1; fi

_CONT_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";

docker logs $_CONT_NAME;

