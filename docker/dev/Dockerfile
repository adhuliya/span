# A dev docker image with settings for development

# this arg is required before FROM
ARG PREFIX
ARG BASE_TAG

FROM ${PREFIX}_base:${BASE_TAG}

# to avoid "Configuring tzdata" prompt
ARG DEBIAN_FRONTEND=noninteractive

ARG uid
ARG user
ARG gid
ARG group
ARG SUFFIX
ARG PREFIX # a required repeat because of FROM above.

ENV DOCKER_DIR docker_dev
ENV PROJECT $PREFIX
ENV PROJECT_HOME /home/project

# only copy select files for reference
# don't copy the symbolic links -- these files are not needed
COPY build.sh /$DOCKER_DIR/
COPY docker_cmd.sh /$DOCKER_DIR/
COPY Dockerfile /$DOCKER_DIR/
COPY README.md /$DOCKER_DIR/
COPY run.sh /$DOCKER_DIR/
COPY setup.sh /$DOCKER_DIR/
COPY source_me.sh /$DOCKER_DIR/

RUN bash $DOCKER_DIR/setup.sh

# Create the same user as the host system user.
RUN echo -e "[Detail] User gid: ${gid} ${group}" && sync
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${gid} -m -d $PROJECT_HOME -s /bin/bash ${user}

RUN echo -e "[Detail] USER and GROUP information: "
RUN echo "  Group Info: " && grep ${group} /etc/group
RUN echo "  User Info : " && grep ${user} /etc/passwd

# for ssh access
RUN usermod -aG sudo ${user} \
  && \
  $(echo "${user}:${user}" | chpasswd) \
  && \
  service ssh start
EXPOSE 22

# Add global fixed environment variables
RUN echo "PROJECT_HOME=$PROJECT_HOME" >> /etc/environemnt

RUN bash /$DOCKER_DIR/setup.sh

# Run a script to keep the container alive.
CMD bash /$DOCKER_DIR/docker_cmd.sh

