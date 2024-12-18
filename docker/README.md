Docker Images
=========================
Maintainer: Anshuman Dhuliya (anshumandhuliya@gmail.com)

Each folder corresponds to a docker image.

* `xxx_base` --> `base/`
* `xxx_dev` --> `dev/` (used for development related setups)

The 'xxx' is a user defined name (with C identifier characters).

## Docker setup

Setup docker in the system and allow non-root users to be able to run
the following command successfully without using `sudo`.

    $ docker image ls;


## Building dev image.

    cd ./base; source ./source_me.sh;
    ./build.sh;             # builds the base image
    cd ../dev; source ./source_me.sh;
    ./build.sh;             # builds the dev image 
    cd ..;                  # return back to this folder


## Image folder contents

Each folder contains the
following useful files that work with their
respective docker images and containers,

0. `Dockerfile` specifies the docker image content and configuration.
1. `./build.sh` is used to build a fresh docker image.
2. `./run.sh` runs the docker image (creating a container).
3. `./remove.sh` removes a running docker container.
4. `./attach_shell.sh`. attaches shell to a running docker container.
5. `./logs.sh` shows the (stdout) output logs generated by the container.


## How to run and use dev container?

Note: To use other images follow similar (almost identical) steps.

To start using the `*_dev` image first
build the image as given above and then refer below.

First start the container,

    cd ./dev;
    ./run.sh;             # if status printed is '0' container has started

The container should be running if docker is
setup properly on the system.

Now refer to this list to do specific tasks by first
cd'ing into the folder that corresponds to the image
you are using. For example, for `dev`,
do `cd ./dev` then use the following reference.

* **Attach a working shell**:
  Attach a working shell to the container using the following
  script,

        ./attach_shell.sh;

  One can attach as many shells to the container. The containers
  are built such that they don't die if all the shells quit.


* **Run a command on the container**:
  One can run arbitrary commands on the container without
  explicitly opening up an interactive shell as follows,

        ./cmd.sh <user_command>;


* **Remove the container**:
  Occasionally one might want to force stop the container.
  This can be done as follows,

        ./remove.sh;

* **Restart the container**:

        ./run.sh;  # this script restarts the container

* **Build a the container image**:
  When you are experimenting with a docker image
  creation process you will need to rebuild the image to
  start using it. Use the following command,

        ./build.sh;

  To use the new image one must restart the container using
  `./run.sh`.


* **View the list of images built in the system**:

        docker image ls;

* **Remove an image from the system**:

        docker image rm --force <IMAGE_ID>;

  The image id can be obtained with `docker image ls`.


* **View the list of containers**:

        docker container ls --all;


* **Remove a container**:

        docker container rm <CONTAINER ID>;

  Sometimes its necessary to remove containers as they may consume
  a huge amount of space when running for a long time (10s of GBs).

