FROM debian:stable-slim

COPY . /opt/source-code
WORKDIR /opt/source-code

RUN apt-get update -y
RUN apt-get -y install python3-pip
RUN apt-get -y install --upgrade pip
RUN pip3 --no-cache-dir install -r requirements.txt

RUN apt-get install ffmpeg -y

CMD python3 bot.py