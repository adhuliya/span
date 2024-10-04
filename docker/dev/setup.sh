#!/usr/bin/env bash

# This script installs basic packages needed for span implementation.

# Do the needful in one step.
# REF: https://buildroot.org/downloads/manual/manual.html#requirement-mandatory
  apt-get update \
&& \
  apt-get -y install --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
&& \
  apt-get -y install --no-install-recommends \
    build-essential \
    gcc \
    zlib1g zlib1g-dev \
    make \
    wget \
    ninja-build \
    ccache \
&& \
  apt-get -y install --no-install-recommends \
    openssh-server \
    sudo \
    zsh \
    tmux \
    vim \
    htop \
    less \
    git \
    make \
    zip unzip \
    imagemagick \
&& \
  apt-get -y autoremove \
&& \
  apt-get clean \
&& \
  python3 -m pip install --upgrade pip \
&& \
  python3 -m pip install --no-cache-dir \
    cython \
    pdoc3 \
&& \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

