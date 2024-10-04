Base Docker Image
=========================
Maintainer: Anshuman Dhuliya (anshumandhuliya@gmail.com)

If you are reading this README within a docker container,
this file and the folder contents are just a snapshot for
reading purpose only.

NOTE: Run the following command before running any scripts.

    source source_me.sh

This folder contains Dockerfile to build
the base image with most packaged resources.

The intent of this image is to isolate all the
third party dependencies that the project needs into
a base image. This has the following advantages,

1. Rebuilding any image derived from this image
   doesn't need to pull resources from the internet
   again and again during development.

2. This image (and possibly others) can stand as a reference as to the
   environment needed for the project.

