# source this file
# run an arbitrary command on the docker container

if ! ./check_env.sh; then exit 1; fi

_CONT_NAME="${DOCKER_IMG_PREFIX}_${DOCKER_IMG_SUFFIX}";
_HOME="/";

docker exec -w $_HOME -it $_CONT_NAME "$@";
