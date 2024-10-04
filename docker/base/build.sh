#!/usr/bin/env bash

# build the docker image 

# Takes one optional argument - the tag e.g. '1.0' (default)

if ! ./check_env.sh; then exit 1; fi

# INVARIANT CHECK: check if the script is run from its location
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)";
if [[ $DIR != "`pwd`" ]]; then
    echo "${_IMG_NAME}: Run the script from its directory as './x.sh'";
    exit;
fi

_IMG_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_suffix=${DOCKER_IMG_SUFFIX};

if [[ $1 != "" ]]; then _TAG="$1"; else _TAG="1.0"; fi

docker build \
    --build-arg SUFFIX=$_suffix \
    --tag $_IMG_NAME:${_TAG} \
    . \
    ;
