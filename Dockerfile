FROM python:3.10.5

MAINTAINER Tiago "tiagofdev@gmail.com"

ENV PYTHONUNBUFFERED True

RUN apt-get update -y && \
	apt-get install -y python3-pip libmariadb-dev

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE $PORT

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app/main:app --host 0.0.0.0

ENTRYPOINT ["python3", "app/main.py"]

