FROM python:3.8
RUN pip install --upgrade pip \
	&& mkdir /gecoadbot

ADD . /gecoadbot
WORKDIR /gecoadbot

RUN pip install -r requirements.txt
CMD python /gecoadbot/bot.py
