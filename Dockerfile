##############################################################################
# cnmem build stage
#

FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04 AS cnmem-build
# Install system dependencies
RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       # sort: alphabetically
       git \
       cmake \
    && rm -rf /var/lib/apt/lists/*
# Install CNMeM, a memory manager for CUDA
RUN git clone https://github.com/NVIDIA/cnmem.git /tmp/cnmem \
 && cd /tmp/cnmem/ \
 && git checkout v1.0.0 \
 && mkdir -p /tmp/cnmem/build \
 && cd /tmp/cnmem/build \
 && cmake .. \
 && make -j4 \
 && make install \
 && cd .. \
 && rm -rf /tmp/cnmem



##############################################################################
# runtime build stage
#

FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04 AS runtime

MAINTAINER Wild Me <dev@wildme.org>

# Fix for ubuntu 18.04 container https://stackoverflow.com/a/58173981/176882
ENV LANG C.UTF-8

USER root

# ###
# System setup
# ###

# Create runtime user "wbia" (aka WildBook IA)
RUN set -x \
    && addgroup --system wbia \
    && adduser --system --group wbia

# Install system dependencies
RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       # ** Please sort alphabetically **
       ca-certificates \
       #: required for downloading 'wait-for'
       curl \
       #: used during package acquisition
       git \
       #: tool to setuid+setgid+setgroups+exec at execution time
       gosu \
       #: opencv2 dep
       libglib2.0-0 \
       #: opencv2 dependency
       libsm6 \
       #: opencv2 dependency
       libxrender1 \
       #: opencv2 dependency
       libxext6 \
       #: opencv2 dependency
       libgl1 \
       #: required to stop prompting by pgloader
       libssl1.0.0 \
       #: required by wait-for
       netcat \
       #: sqlite->postgres dependency
       pgloader \
       #: dev debug dependency
       #: python3-dev required to build 'annoy'
       python3.7 \
       python3.7-dev \
       python3.7-gdbm \
       python3-pip \
       python3-setuptools \
       python3-venv \
       unzip \
    && rm -rf /var/lib/apt/lists/*

# Install CNMeM, a memory manager for CUDA
COPY --from=cnmem-build /usr/local/lib/libcnmem.so* /usr/local/lib/

# Set CUDA-specific environment paths
ENV PATH "/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH "/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
ENV CUDA_HOME "/usr/local/cuda"

# Create the working directory
RUN set -x \
    && mkdir -p /data \
    && chown wbia:wbia /data \
    && chmod 755 /data

# Install wait-for
RUN set -x \
    && curl -s https://raw.githubusercontent.com/eficode/wait-for/v2.0.0/wait-for > /usr/local/bin/wait-for \
    && chmod a+x /usr/local/bin/wait-for \
    # test it works
    && wait-for google.com:80 -- echo "success"

# ###
# Application setup
# ###

COPY . /tmp/code

RUN set -x \
    && cd /tmp/code \
    && python3.7 -m pip install --upgrade pip \
    && python3.7 -m pip install --verbose --no-deps . \
    # Install pytorch early because it's a large package
    && python3.7 -m pip install torch \
    && python3.7 -m pip install -r /tmp/code/requirements/runtime.txt \
    && python3.7 -m pip install -r /tmp/code/requirements/postgres.txt \
    # TODO (4-Jun-12020) plugins will come in time...
    # && python3 -m pip install -r /tmp/code/requirements.txt -r /tmp/code/requirements/plugins.txt
    && rm -rf /tmp/code

# Visual install verification of the OpenCV2 Python buildings
RUN python3.7 -c "import cv2; print(cv2.getBuildInformation())"

# Ports for the frontend web server
EXPOSE 5000

# Move to the workdir
WORKDIR /data

# Set the "workdir"
RUN python3.7 -m wbia --set-workdir /data --preload-exit

COPY .dockerfiles/docker-entrypoint.sh /docker-entrypoint.sh

ENV WBIA_DB_DIR="/data/db"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python3.7", "-m", "wbia.dev", "--dbdir", "$WBIA_DB_DIR", "--logdir", "/data/logs/", "--web", "--port", "5000", "--web-deterministic-ports", "--containerized", "--cpudark", "--production"]
