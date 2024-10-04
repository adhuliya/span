#!/usr/bin/env bash

# run the docker image -- takes one (optional) argument - the tag
# Names starting with `_` are not exported.

if ! ./check_env.sh; then exit 1; fi

# INVARIANT CHECK: check if the script is run from its location
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)";
if [[ $DIR != "`pwd`" ]]; then
  echo "${_IMG_NAME}: Run the script from its directory as './xxx.sh'";
  exit;
fi

_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_HOST_MOUNT_DIR="$(dirname $(dirname `pwd`))";
_CONT_MOUNT_POINT="/home/${DOCKER_IMG_SUFFIX}";

if [[ -n $1 ]]; then _TAG="$1"; else _TAG="1.0"; fi

if id | grep docker; then 
  chown -R $USER:docker ../..; # change group owner of the project directory
else
  echo "ERROR: $USER doesnot belong to the docker group (exiting).";
  exit;
fi

_IMG_NAME="$_NAME:$_TAG";
_CONT_NAME="$_NAME";

echo "Note: Removing any container with name '$_CONT_NAME'";
docker rm --force $_CONT_NAME;

echo "Note: Starting container with name '$_CONT_NAME'";
echo "Note: Mounting Host Dir: $_HOST_MOUNT_DIR in container at $_CONT_MOUNT_POINT";
# if using --network="itsoflife" create the network first (only once):
#   docker network create itsoflife;
docker run \
  --detach \
  --ulimit nofile=200000:200000 \
  --mount type=bind,source=$_HOST_MOUNT_DIR,target=$_CONT_MOUNT_POINT \
  --name $_CONT_NAME \
  $_IMG_NAME;

# # To use USB device inside docker, add the line given below to the docker run command
#   -v /dev/:/dev --device-cgroup-rule='c 188:* rmw' \

echo "Note: Docker container started? Status: $? (Non Zero = ERROR)";


