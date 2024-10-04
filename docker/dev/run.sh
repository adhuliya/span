#!/usr/bin/env bash

# run the docker image -- takes one (optional) argument - the tag
# Names starting with `_` are not exported.

# INVARIANT CHECK: check if the the script is run from its location
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )";
if [[ $DIR != "`pwd`" ]]; then
  echo "NOTE: Must run this script from its directory as './...'";
  exit;  # if not then exit
fi

_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_HOST_MOUNT_DIR="$(dirname $(dirname $(pwd)))"; # i.e. the whole project
_CONT_MOUNT_POINT="/home/project";


if [[ $1 != "" ]]; then _TAG="$1"; else _TAG="1.0"; fi


chown -R $USER:docker ../..; # change the group owner


_IMG_NAME="$_NAME:$_TAG";
_CONT_NAME="$_NAME";

echo "Note: Removing any container with name '$_CONT_NAME'";
docker rm --force $_CONT_NAME;

echo "Note: Starting container with name '$_CONT_NAME'";
echo "Note: Mounting Host Dir: $_HOST_MOUNT_DIR in container at $_CONT_MOUNT_POINT";
docker run \
  --detach \
  --ulimit nofile=200000:200000 \
  -p 3333:22 \
  --name $_CONT_NAME \
  --mount type=bind,source=$_HOST_MOUNT_DIR,target=$_CONT_MOUNT_POINT \
  $_IMG_NAME;

echo -e "\nNote: Docker container started? Status: $? (Non Zero = ERROR)";


