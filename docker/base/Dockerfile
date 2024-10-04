# A base docker image with all the dependencies of the project

FROM ubuntu:22.04

# to avoid "Configuring tzdata" prompt
ARG DEBIAN_FRONTEND=noninteractive

ARG SUFFIX
ENV DOCKER_DIR "docker_$SUFFIX"

# only copy select files for reference
# don't copy the symbolic links -- these files are not needed
COPY build.sh /$DOCKER_DIR/
COPY docker_cmd.sh /$DOCKER_DIR/
COPY Dockerfile /$DOCKER_DIR/
COPY README.md /$DOCKER_DIR/
COPY run.sh /$DOCKER_DIR/
COPY setup.sh /$DOCKER_DIR/
COPY source_me.sh /$DOCKER_DIR/

RUN bash /$DOCKER_DIR/setup.sh

CMD bash /$DOCKER_DIR/docker_cmd.sh

