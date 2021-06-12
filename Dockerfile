FROM python:3

COPY . /
RUN ls -la /

RUN pip3 install -r requirements.txt
EXPOSE 5000
CMD [ "python3", "./docker_preroll.py" ]
RUN apt-get update
RUN apt-get install ffmpeg -y
