FROM python:3.7

ADD *.py /

RUN pip install discord.py tinydb requests

CMD [ "python", "-u", "./main.py" ]