# source this file

if [[ ! -e base || ! -e dev ]]; then
  echo "ERROR: source this file from its location.";
fi

export PROJECT_DOCKER="`pwd`";

# docker image = project name
export PROJECT_NAME="span";
export DOCKER_IMG_PREFIX=$PROJECT_NAME;

