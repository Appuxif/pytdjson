FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get clean && apt-get update -y
RUN apt-get install -y locales
RUN sed -i -e \
  's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen \
   && locale-gen

ENV LANG='ru_RU.UTF-8' LANGUAGE='ru_RU:ru' LC_LANG='ru_RU.UTF-8' LC_ALL='ru_RU.UTF-8'
ENV DEBIAN_FRONTEND='noninteractive'

RUN apt-get install -y --no-install-recommends \
    build-essential \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip
#    libffi-dev \
#    libpq-dev \
#    libjpeg-dev \
#    libcairo2 \
#    libpangocairo-1.0.0 \
#    libxslt-dev \
#    liblapack-dev \
#    libblas-dev \
#    libgdk-pixbuf2.0-0
#    libpango1.0-0 \
#    libpango1.0-dev \

# Для билда и запуска tdlib
RUN apt-get install -y --no-install-recommends \
    make \
    git \
    zlib1g-dev \
    libssl-dev \
    gperf \
    php-cli \
    cmake \
    g++
