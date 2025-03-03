#!/bin/bash
docker run -it --rm \
    -v $(pwd):/span \
    span-dev \
    "$@" 