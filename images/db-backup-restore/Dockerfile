FROM ubuntu:18.04
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="Asia/Jerusalem"
RUN apt-get update && apt-get install -y  wget software-properties-common && \
    apt-get update && \
    apt-get install -y \
    python-pip \
    postgresql postgresql-contrib \
    curl
RUN pip install awscli
WORKDIR /app
COPY ./start.sh .
CMD ./start.sh
