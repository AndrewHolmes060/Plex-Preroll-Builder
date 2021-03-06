FROM python:3

COPY preroll.py /
COPY requirements.txt /
COPY Overlays /
COPY fonts /
COPY prerolls /
COPY .env /

RUN pip3 install -r requirements.txt

CMD [ "python3", "./preroll.py" ]
