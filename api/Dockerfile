FROM python:slim
MAINTAINER Richard Abdill
# Note: The python:alpine image would be lovely
# to use here, but it isn't compatible with the
# postgres SDK, per this issue:
# https://github.com/psycopg/psycopg2/issues/699

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN apt-get update
RUN apt install -y curl

ADD . /app
WORKDIR /app

HEALTHCHECK --start-period=10s --interval=10s --timeout=10s CMD curl --fail http://localhost/ || exit 1

CMD ["python", "main.py"]
