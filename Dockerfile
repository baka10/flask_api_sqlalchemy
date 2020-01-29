FROM python:3.8.0

RUN apt-get update
RUN apt-get install -y zip unzip curl git

WORKDIR /.ENV
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt