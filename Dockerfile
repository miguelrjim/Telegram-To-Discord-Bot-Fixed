# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

ENV SESSION_NAME=forwardgram
ENV CONFIG_FILE=config.yml

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "forwardgram.py"]