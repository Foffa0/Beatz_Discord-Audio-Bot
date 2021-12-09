FROM python:3.8-slim-buster

COPY . .

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN pip3 --no-cache-dir install -r requirements.txt

CMD python3 bot.py