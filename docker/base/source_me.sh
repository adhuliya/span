# source this file before running any of the scripts.

# set image suffix

pushd .. > /dev/null;
source source_me.sh;
popd > /dev/null;
export DOCKER_IMG_SUFFIX="base";

