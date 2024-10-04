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
  wget https://github.com/Kitware/CMake/releases/download/v3.30.4/cmake-3.30.4-Linux-x86_64.sh \
    -q -O /tmp/cmake-install.sh \
&& \
  chmod u+x /tmp/cmake-install.sh \
&& \
  mkdir /opt/cmake-3.30.4 \
&& \
  /tmp/cmake-install.sh --skip-license --prefix=/opt/cmake-3.30.4 \
&& \
  rm /tmp/cmake-install.sh \
&& \
  ln -s /opt/cmake-3.30.4/bin/* /usr/local/bin \
&& \
  apt-get -y autoremove \
&& \
  apt-get clean \
&& \
  python3 -m pip install --upgrade pip \
&& \
  python3 -m pip install --no-cache-dir \
    cython \
&& \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

