FROM python:slim
MAINTAINER Richard Abdill
# Note: The python:alpine image would be lovely
# to use here, but it isn't compatible with the
# postgres SDK, per this issue:
# https://github.com/psycopg/psycopg2/issues/699

COPY requirements.txt /
RUN pip install -r /requirements.txt

ADD . /app
WORKDIR /app
CMD ["python", "main.py"]
