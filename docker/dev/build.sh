#!/usr/bin/env bash

# build the docker image -- takes one optional argument - the tag

if ! ./check_env.sh; then exit 1; fi

# INVARIANT CHECK: check if the script is run from its location
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)";
if [[ $DIR != "`pwd`" ]]; then
    echo "${_IMG_NAME}: Run the script from its directory as './x.sh'";
    exit;
fi

_IMG_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_prefix="${DOCKER_IMG_PREFIX}";
_suffix=${DOCKER_IMG_SUFFIX};

if [[ $1 != "" ]]; then _TAG="$1"; else _TAG="1.0"; fi

# get the gid of the docker group on the host system
_DOCKER_GROUP=docker;
_DOCKER_GID=$(getent group $_DOCKER_GROUP | awk -F: '{printf "%d", $3}');

echo "[Detail] Group is $_DOCKER_GROUP ($_DOCKER_GID)";
echo "[Detail] User is $(id -nu) ($(id -u))";

# The user must add itself to the docker group.
# sudo usermod -aG docker $USER;
chown -R $USER:$_DOCKER_GROUP ../..; # change the group owner
chmod g+s ../..; # preserve the group change in the directory

docker build \
  --build-arg uid="$(id -u)" \
  --build-arg user="$(id -nu)" \
  --build-arg gid="$_DOCKER_GID" \
  --build-arg group="$_DOCKER_GROUP" \
  --build-arg PREFIX=$_prefix \
  --build-arg SUFFIX=$_suffix \
  --build-arg BASE_TAG=$_TAG \
  --progress plain \
  --tag $_IMG_NAME:${_TAG} \
  . \
  |& tee docker_build.out \
  ;

