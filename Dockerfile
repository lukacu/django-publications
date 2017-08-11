FROM ubuntu:xenial
MAINTAINER Luka Cehovin, luka.cehovin@fri.uni-lj.si

# Setup environment variable defaults
ENV PYTHONUNBUFFERED true

WORKDIR /code

# Install code dependencies
ADD ./packages.txt /code/packages.txt
RUN apt-get update && ( cat /code/packages.txt | DEBIAN_FRONTEND=noninteractive xargs apt-get --no-install-recommends -y --force-yes install ) && rm -rf /var/lib/apt/lists/

# Install Python package dependencies (do not use pip install -r here!)
ADD ./requirements.txt /code/requirements.txt
RUN { cat /code/requirements.txt | sed 's/^-e //' | xargs -n 1 pip install; } || true

# Create volume attachment point for media data
RUN mkdir -p /media

EXPOSE 80
