FROM python:3.12-slim
LABEL telegram-bot="queue tg bot"

WORKDIR /bot/
COPY . /bot/
RUN pip install -r requirements.txt